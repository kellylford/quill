"""Tests for the watch worker that drains the queue (WATCH-3, WATCH-7)."""

from __future__ import annotations

from pathlib import Path

from quill.core.watch_actions import (
    MoveAction,
    OpenAction,
    UnavailableAction,
    WatchActionRegistry,
)
from quill.core.watch_profiles import POST_DELETE, POST_LEAVE, POST_MOVE, WatchProfile
from quill.core.watch_queue import STATE_DONE, STATE_FAILED, STATE_SKIPPED, WatchQueue
from quill.core.watch_worker import WatchWorker


def _registry(on_open=None) -> WatchActionRegistry:
    registry = WatchActionRegistry()
    registry.register(OpenAction(on_open=on_open or (lambda _p: None)))
    registry.register(MoveAction())
    return registry


def _worker(queue: WatchQueue, registry: WatchActionRegistry, profiles: dict[str, WatchProfile]):
    return WatchWorker(
        queue=queue,
        registry=registry,
        profile_lookup=profiles.get,
    )


def test_drain_open_action_marks_done(tmp_path: Path) -> None:
    opened: list[Path] = []
    queue = WatchQueue()
    registry = _registry(on_open=opened.append)
    profile = WatchProfile(profile_id="p1", action_id="open", post_action=POST_LEAVE).normalized()
    worker = _worker(queue, registry, {"p1": profile})

    source = tmp_path / "doc.txt"
    source.write_text("hi", encoding="utf-8")
    item = queue.enqueue(source, "p1", "open")
    assert item is not None

    assert worker.drain_once() is True
    assert queue.get(item.item_id).state == STATE_DONE
    assert opened == [source]
    assert source.exists()  # leave in place


def test_drain_missing_profile_is_skipped(tmp_path: Path) -> None:
    queue = WatchQueue()
    registry = _registry()
    worker = _worker(queue, registry, {})  # no profiles
    item = queue.enqueue(tmp_path / "a.txt", "ghost", "open")
    assert item is not None
    assert worker.drain_once() is True
    assert queue.get(item.item_id).state == STATE_SKIPPED


def test_drain_unavailable_action_is_skipped(tmp_path: Path) -> None:
    queue = WatchQueue()
    registry = WatchActionRegistry(feature_enabled=lambda _f: False)
    registry.register(
        UnavailableAction(
            action_id="glow", label="GLOW", required_feature_id="future.glow", reason="nope"
        )
    )
    profile = WatchProfile(profile_id="p1", action_id="glow").normalized()
    worker = _worker(queue, registry, {"p1": profile})
    item = queue.enqueue(tmp_path / "a.txt", "p1", "glow")
    assert item is not None
    assert worker.drain_once() is True
    assert queue.get(item.item_id).state == STATE_SKIPPED


def test_drain_failed_action_marks_failed_after_retries(tmp_path: Path) -> None:
    queue = WatchQueue(max_attempts=1)
    registry = WatchActionRegistry()
    # MoveAction with no destination fails validation -> failed outcome.
    registry.register(MoveAction())
    profile = WatchProfile(
        profile_id="p1", action_id="move", action_options={"destination": ""}
    ).normalized()
    worker = _worker(queue, registry, {"p1": profile})
    item = queue.enqueue(tmp_path / "a.txt", "p1", "move")
    assert item is not None
    worker.drain_once()
    assert queue.get(item.item_id).state == STATE_FAILED


def test_post_action_delete_removes_source(tmp_path: Path) -> None:
    queue = WatchQueue()
    registry = _registry()
    profile = WatchProfile(profile_id="p1", action_id="open", post_action=POST_DELETE).normalized()
    worker = _worker(queue, registry, {"p1": profile})
    source = tmp_path / "doc.txt"
    source.write_text("hi", encoding="utf-8")
    item = queue.enqueue(source, "p1", "open")
    assert item is not None
    worker.drain_once()
    assert queue.get(item.item_id).state == STATE_DONE
    assert not source.exists()


def test_post_action_move_relocates_source(tmp_path: Path) -> None:
    dest = tmp_path / "processed"
    dest.mkdir()
    queue = WatchQueue()
    registry = _registry()
    profile = WatchProfile(
        profile_id="p1",
        action_id="open",
        post_action=POST_MOVE,
        post_action_destination=str(dest),
    ).normalized()
    worker = _worker(queue, registry, {"p1": profile})
    source = tmp_path / "doc.txt"
    source.write_text("hi", encoding="utf-8")
    item = queue.enqueue(source, "p1", "open")
    assert item is not None
    worker.drain_once()
    done = queue.get(item.item_id)
    assert done.state == STATE_DONE
    assert not source.exists()
    assert (dest / "doc.txt").exists()
    assert done.result_path == str(dest / "doc.txt")


def test_drain_once_returns_false_when_empty() -> None:
    queue = WatchQueue()
    worker = _worker(queue, _registry(), {})
    assert worker.drain_once() is False


def test_move_action_then_leave_post_action(tmp_path: Path) -> None:
    # The action itself moves the file; post-action LEAVE must not error.
    out = tmp_path / "out"
    out.mkdir()
    queue = WatchQueue()
    registry = _registry()
    profile = WatchProfile(
        profile_id="p1",
        action_id="move",
        action_options={"destination": str(out)},
        post_action=POST_LEAVE,
    ).normalized()
    worker = _worker(queue, registry, {"p1": profile})
    source = tmp_path / "doc.txt"
    source.write_text("hi", encoding="utf-8")
    item = queue.enqueue(source, "p1", "move")
    assert item is not None
    worker.drain_once()
    assert queue.get(item.item_id).state == STATE_DONE
    assert (out / "doc.txt").exists()


def test_start_stop_lifecycle() -> None:
    queue = WatchQueue()
    worker = _worker(queue, _registry(), {})
    assert worker.start() is True
    assert worker.is_running is True
    assert worker.start() is False  # already running
    worker.stop()
    assert worker.is_running is False
