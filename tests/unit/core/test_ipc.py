from __future__ import annotations

from pathlib import Path

import pytest

import quill.core.ipc as ipc
from quill.core.ipc import (
    drain_open_requests,
    enqueue_open_request,
    release_primary_instance,
    try_claim_primary_instance,
)


def test_try_claim_and_release_primary_instance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    assert try_claim_primary_instance() is True
    assert try_claim_primary_instance() is False
    release_primary_instance()
    assert try_claim_primary_instance() is True


def test_try_claim_replaces_stale_lock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    lock_path = tmp_path / "ipc" / "instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("999999", encoding="utf-8")
    monkeypatch.setattr(ipc, "_pid_is_running", lambda _pid: False)
    assert try_claim_primary_instance() is True


def test_enqueue_and_drain_open_requests(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    first = tmp_path / "one.md"
    second = tmp_path / "two.md"
    enqueue_open_request(first)
    enqueue_open_request(second)
    drained = drain_open_requests()
    assert drained == [first, second]
    assert drain_open_requests() == []
