"""Watch profiles and the multi-profile watch manager (WATCH-1, WATCH-5).

A :class:`WatchProfile` is a named, independently enabled rule: a folder, a set
of filters, exactly one action (bound by id into the WATCH-2 registry), and
post-action handling. The :class:`WatchManager` runs one poller per enabled
profile concurrently with isolated failure (one bad profile or file never stalls
the others) and feeds every detection into the shared durable queue (WATCH-3),
which de-duplicates so a file is claimed exactly once across overlapping
profiles.

This module is UI-framework-agnostic: no ``wx`` imports.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from .watch_queue import WatchQueue

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

_DEFAULT_POLL_SECONDS = 5
_MIN_POLL_SECONDS = 2
_MAX_POLL_SECONDS = 300
_MIN_FILE_AGE_SECONDS = 2.0

#: Post-action handling for a source file once its action succeeds.
POST_LEAVE = "leave"
POST_MOVE = "move"
POST_DELETE = "delete"
_POST_ACTIONS = frozenset({POST_LEAVE, POST_MOVE, POST_DELETE})

_DEFAULT_SUFFIXES = (
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".json",
    ".csv",
    ".tsv",
    ".docx",
    ".pptx",
    ".epub",
    ".pdf",
    ".odt",
    ".rtf",
)


def _clean_suffix(suffix: str) -> str:
    suffix = suffix.strip().lower()
    if not suffix:
        return ""
    if not suffix.startswith("."):
        suffix = "." + suffix
    return suffix


@dataclass(frozen=True, slots=True)
class WatchProfile:
    """One named watch rule binding a folder to a single action."""

    profile_id: str = ""
    name: str = "Untitled profile"
    enabled: bool = False
    folder_path: str = ""
    include_subfolders: bool = False
    process_existing: bool = False
    suffixes: tuple[str, ...] = _DEFAULT_SUFFIXES
    min_size_bytes: int = 1
    min_age_seconds: float = _MIN_FILE_AGE_SECONDS
    poll_interval_seconds: int = _DEFAULT_POLL_SECONDS
    action_id: str = "open"
    action_options: dict[str, object] = field(default_factory=dict)
    post_action: str = POST_LEAVE
    post_action_destination: str = ""

    def normalized(self) -> WatchProfile:
        interval = int(self.poll_interval_seconds or _DEFAULT_POLL_SECONDS)
        interval = max(_MIN_POLL_SECONDS, min(_MAX_POLL_SECONDS, interval))
        suffixes = tuple(dict.fromkeys(s for s in (_clean_suffix(x) for x in self.suffixes) if s))
        post = self.post_action if self.post_action in _POST_ACTIONS else POST_LEAVE
        return WatchProfile(
            profile_id=self.profile_id or uuid.uuid4().hex,
            name=str(self.name).strip() or "Untitled profile",
            enabled=bool(self.enabled),
            folder_path=str(self.folder_path).strip(),
            include_subfolders=bool(self.include_subfolders),
            process_existing=bool(self.process_existing),
            suffixes=suffixes or _DEFAULT_SUFFIXES,
            min_size_bytes=max(0, int(self.min_size_bytes)),
            min_age_seconds=max(0.0, float(self.min_age_seconds)),
            poll_interval_seconds=interval,
            action_id=str(self.action_id).strip() or "open",
            action_options=dict(self.action_options),
            post_action=post,
            post_action_destination=str(self.post_action_destination).strip(),
        )

    def validate(self) -> list[str]:
        """Return human-readable configuration problems (empty when valid)."""
        problems: list[str] = []
        normalized = self.normalized()
        if not normalized.folder_path:
            problems.append("Choose a folder to watch.")
        elif not Path(normalized.folder_path).expanduser().is_dir():
            problems.append(f"Watch folder does not exist: {normalized.folder_path}")
        if normalized.post_action == POST_MOVE:
            destination = normalized.post_action_destination
            if not destination:
                problems.append("Choose a destination folder for processed files.")
            elif not Path(destination).expanduser().is_dir():
                problems.append(f"Destination folder does not exist: {destination}")
        return problems

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "enabled": self.enabled,
            "folder_path": self.folder_path,
            "include_subfolders": self.include_subfolders,
            "process_existing": self.process_existing,
            "suffixes": list(self.suffixes),
            "min_size_bytes": self.min_size_bytes,
            "min_age_seconds": self.min_age_seconds,
            "poll_interval_seconds": self.poll_interval_seconds,
            "action_id": self.action_id,
            "action_options": dict(self.action_options),
            "post_action": self.post_action,
            "post_action_destination": self.post_action_destination,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> WatchProfile:
        suffixes_raw = raw.get("suffixes")
        if isinstance(suffixes_raw, (list, tuple)):
            suffixes = tuple(str(s) for s in suffixes_raw)
        else:
            suffixes = _DEFAULT_SUFFIXES
        options_raw = raw.get("action_options")
        options = dict(options_raw) if isinstance(options_raw, dict) else {}
        return cls(
            profile_id=str(raw.get("profile_id", "")),
            name=str(raw.get("name", "Untitled profile")),
            enabled=bool(raw.get("enabled", False)),
            folder_path=str(raw.get("folder_path", "")),
            include_subfolders=bool(raw.get("include_subfolders", False)),
            process_existing=bool(raw.get("process_existing", False)),
            suffixes=suffixes,
            min_size_bytes=_as_int(raw.get("min_size_bytes"), 1),
            min_age_seconds=_as_float(raw.get("min_age_seconds"), _MIN_FILE_AGE_SECONDS),
            poll_interval_seconds=_as_int(raw.get("poll_interval_seconds"), _DEFAULT_POLL_SECONDS),
            action_id=str(raw.get("action_id", "open")),
            action_options=options,
            post_action=str(raw.get("post_action", POST_LEAVE)),
            post_action_destination=str(raw.get("post_action_destination", "")),
        ).normalized()


def _as_int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _as_float(value: object, default: float) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def iter_matching_files(profile: WatchProfile, *, now: float | None = None) -> Iterable[Path]:
    """Yield files in ``profile``'s folder that pass its filters.

    Applies the suffix set, minimum size, and minimum settle age so partially
    written files are skipped until they stop changing. Returns nothing when the
    folder is missing rather than raising, so a transiently unavailable network
    share never crashes the poller.
    """
    folder = Path(profile.folder_path).expanduser()
    if not folder.is_dir():
        return
    moment = time.time() if now is None else now
    suffixes = set(profile.suffixes)
    pattern = "**/*" if profile.include_subfolders else "*"
    candidates: list[Path] = []
    for candidate in folder.glob(pattern):
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in suffixes:
            continue
        try:
            stat = candidate.stat()
        except OSError:
            continue
        if stat.st_size < profile.min_size_bytes:
            continue
        if (moment - stat.st_mtime) < profile.min_age_seconds:
            continue
        candidates.append(candidate)
    candidates.sort(key=lambda path: path.name.lower())
    yield from candidates


class WatchManager:
    """Runs one poller thread per enabled profile, feeding the shared queue.

    Each poller catches and logs its own exceptions so a single failing profile
    can never stall the others (isolated failure, WATCH-1). All detections flow
    into the one :class:`WatchQueue`, whose path-based de-duplication enforces
    exactly-once claiming across overlapping profiles.
    """

    def __init__(self, queue: WatchQueue) -> None:
        self._queue = queue
        self._lock = threading.Lock()
        self._threads: dict[str, threading.Thread] = {}
        self._stop_events: dict[str, threading.Event] = {}
        self._running = False

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def active_profile_ids(self) -> set[str]:
        with self._lock:
            return set(self._threads)

    def start(self, profiles: Iterable[WatchProfile]) -> list[str]:
        """Start pollers for every enabled, valid profile; returns started ids."""
        self.stop()
        started: list[str] = []
        with self._lock:
            self._running = True
            for raw_profile in profiles:
                profile = raw_profile.normalized()
                if not profile.enabled:
                    continue
                if profile.validate():
                    logger.warning(
                        "Skipping invalid watch profile %s (%s)",
                        profile.name,
                        profile.profile_id,
                    )
                    continue
                stop_event = threading.Event()
                thread = threading.Thread(
                    target=self._poll_loop,
                    args=(profile, stop_event),
                    name=f"quill-watch-{profile.profile_id[:8]}",
                    daemon=True,
                )
                self._stop_events[profile.profile_id] = stop_event
                self._threads[profile.profile_id] = thread
                started.append(profile.profile_id)
            for profile_id in started:
                self._threads[profile_id].start()
        return started

    def stop(self) -> None:
        with self._lock:
            stop_events = list(self._stop_events.values())
            threads = list(self._threads.items())
            self._stop_events.clear()
            self._threads.clear()
            self._running = False
        for event in stop_events:
            event.set()
        for _profile_id, thread in threads:
            thread.join(timeout=5.0)

    def _poll_loop(self, profile: WatchProfile, stop_event: threading.Event) -> None:
        if not profile.process_existing:
            # Reserve the de-dup slot for files present at startup so they are
            # ignored until they change, without enqueuing or actioning them.
            try:
                for path in iter_matching_files(profile):
                    self._queue.prime(path)
            except Exception:  # never let prescan crash the poller
                logger.exception("Watch prescan failed for profile %s", profile.profile_id)
        while not stop_event.is_set():
            try:
                for path in iter_matching_files(profile):
                    self._queue.enqueue(path, profile.profile_id, profile.action_id)
            except Exception:  # isolated failure: log and keep polling
                logger.exception("Watch scan failed for profile %s", profile.profile_id)
            stop_event.wait(float(profile.poll_interval_seconds))


__all__ = [
    "POST_DELETE",
    "POST_LEAVE",
    "POST_MOVE",
    "SCHEMA_VERSION",
    "WatchManager",
    "WatchProfile",
    "iter_matching_files",
]
