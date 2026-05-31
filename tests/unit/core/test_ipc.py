from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import quill.core.ipc as ipc
from quill.core.ipc import (
    drain_open_requests,
    enqueue_open_request,
    release_primary_instance,
    try_claim_primary_instance,
)


@pytest.fixture(autouse=True)
def _release_lock_after_each_test() -> object:
    # Each test gets its own QUILL_DATA_DIR, but the held lock handle is module
    # state — always release it so a held fd can't leak into the next test.
    yield
    release_primary_instance()
    ipc._lock_handle = None


def test_claim_is_idempotent_then_releases(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    assert try_claim_primary_instance() is True
    # Same process claiming again is a no-op success, not a second instance.
    assert try_claim_primary_instance() is True
    release_primary_instance()
    assert try_claim_primary_instance() is True


def test_leftover_lock_file_with_no_holder_does_not_block(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A lock file left behind by a previous run (no live process holding the OS
    # lock) must never block a new instance — this is the bug the OS lock fixes.
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    lock_path = tmp_path / "ipc" / "instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text('{"pid": 999999}', encoding="utf-8")
    assert try_claim_primary_instance() is True


def test_a_dead_holder_never_blocks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # A child claims the lock then exits HARD (os._exit) without releasing —
    # simulating a crash/force-kill. The OS frees the lock on process death, so
    # we can claim with no PID bookkeeping or "self-heal" logic.
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    code = (
        "import os;"
        "from quill.core.ipc import try_claim_primary_instance;"
        "assert try_claim_primary_instance();"
        "os._exit(0)"
    )
    result = subprocess.run([sys.executable, "-c", code])
    assert result.returncode == 0
    assert try_claim_primary_instance() is True


def test_a_live_instance_blocks_a_second(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # While this process holds the lock, a genuinely separate process must not
    # be able to claim it.
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    assert try_claim_primary_instance() is True
    code = (
        "import sys;"
        "from quill.core.ipc import try_claim_primary_instance;"
        "sys.exit(0 if try_claim_primary_instance() else 3)"
    )
    result = subprocess.run([sys.executable, "-c", code])
    assert result.returncode == 3  # the second process could NOT claim


def test_enqueue_and_drain_open_requests(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    first = tmp_path / "one.md"
    second = tmp_path / "two.md"
    enqueue_open_request(first)
    enqueue_open_request(second)
    drained = drain_open_requests()
    assert [request.path for request in drained] == [first, second]
    assert drain_open_requests() == []


def test_enqueue_show_request(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    enqueue_open_request(None)
    assert drain_open_requests() == [None]
