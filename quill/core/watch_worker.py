"""Watch worker: drains the queue by running actions (WATCH-3, WATCH-7).

The worker claims items from the durable queue one at a time, looks up the
profile that produced each item, runs its bound action through the action
registry, applies post-action handling (leave, move, or delete the source on
success), and records the outcome back on the queue. It runs on a single daemon
thread so actions never overlap, keeping side effects predictable; the queue's
own pause/resume and retry/backoff govern pacing.

This module is UI-framework-agnostic: no ``wx`` imports.
"""

from __future__ import annotations

import logging
import shutil
import threading
from collections.abc import Callable, Mapping
from pathlib import Path

from .watch_actions import OUTCOME_SKIPPED, WatchActionRegistry, WatchItem
from .watch_profiles import POST_DELETE, POST_LEAVE, POST_MOVE, WatchProfile
from .watch_queue import QueueItem, WatchQueue

logger = logging.getLogger(__name__)

_IDLE_WAIT_SECONDS = 0.5

#: Resolve a profile id to its current profile (or ``None`` if it was deleted).
ProfileLookup = Callable[[str], "WatchProfile | None"]


class WatchWorker:
    """Single-threaded drainer that executes queued watch items."""

    def __init__(
        self,
        *,
        queue: WatchQueue,
        registry: WatchActionRegistry,
        profile_lookup: ProfileLookup,
        idle_wait_seconds: float = _IDLE_WAIT_SECONDS,
    ) -> None:
        self._queue = queue
        self._registry = registry
        self._profile_lookup = profile_lookup
        self._idle_wait = max(0.05, float(idle_wait_seconds))
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._wake = threading.Event()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> bool:
        if self._running:
            return False
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, name="quill-watch-worker", daemon=True
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        if not self._running:
            return
        self._stop_event.set()
        self._wake.set()
        self._running = False
        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=5.0)

    def wake(self) -> None:
        """Nudge the worker to check the queue immediately (e.g. after enqueue)."""
        self._wake.set()

    def drain_once(self) -> bool:
        """Process a single ready item synchronously; returns ``True`` if one ran.

        Exposed for deterministic testing and for callers that prefer to pump the
        queue on their own schedule rather than run the background thread.
        """
        item = self._queue.claim_next()
        if item is None:
            return False
        self._process(item)
        return True

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            processed = False
            try:
                processed = self.drain_once()
            except Exception:  # a crash here must never kill the worker thread
                logger.exception("Watch worker iteration failed")
            if not processed:
                self._wake.wait(self._idle_wait)
                self._wake.clear()

    def _process(self, item: QueueItem) -> None:
        profile = self._profile_lookup(item.profile_id)
        if profile is None:
            self._queue.mark_skipped(
                item.item_id, "The watch profile for this item no longer exists."
            )
            return
        options: Mapping[str, object] = profile.action_options
        outcome = self._registry.run(
            item.action_id,
            WatchItem(source_path=Path(item.source_path), profile_id=item.profile_id),
            options,
        )
        if outcome.status == OUTCOME_SKIPPED:
            self._queue.mark_skipped(item.item_id, outcome.message)
            return
        if not outcome.ok:
            self._queue.mark_failed(item.item_id, outcome.message or "Action failed.")
            return
        result_path = self._apply_post_action(profile, Path(item.source_path), outcome.result_path)
        self._queue.mark_done(
            item.item_id, outcome.message, str(result_path) if result_path else ""
        )

    def _apply_post_action(
        self, profile: WatchProfile, source: Path, action_result: Path | None
    ) -> Path | None:
        """Run the profile's post-action on the source file after a success.

        Returns the path the file ended up at (the action's own result path when
        it already moved the file, the new location after a move, or the source
        when left in place). Post-action errors are logged but do not flip a
        succeeded item to failed, since the action itself completed.
        """
        if profile.post_action == POST_LEAVE:
            return action_result or (source if source.exists() else None)
        if not source.exists():
            # The action already consumed the source (e.g. a move action).
            return action_result
        if profile.post_action == POST_DELETE:
            try:
                source.unlink()
            except OSError:
                logger.exception("Watch post-action delete failed for %s", source)
            return action_result
        if profile.post_action == POST_MOVE:
            destination = Path(profile.post_action_destination).expanduser()
            if not destination.is_dir():
                logger.warning("Watch post-action move destination missing: %s", destination)
                return action_result or source
            target = destination / source.name
            try:
                moved = shutil.move(str(source), str(target))
            except OSError:
                logger.exception("Watch post-action move failed for %s", source)
                return action_result or source
            return Path(moved)
        return action_result or source


__all__ = ["ProfileLookup", "WatchWorker"]
