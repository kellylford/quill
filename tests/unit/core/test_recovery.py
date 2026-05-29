from __future__ import annotations

import time
from pathlib import Path
from uuid import uuid4

import pytest

from quill.core.recovery import (
    begin_session,
    latest_session_snapshot,
    mark_clean_exit,
    read_recovery_snapshot,
)


def test_begin_session_offers_previous_unclean_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    previous = str(uuid4())
    current = str(uuid4())
    session_root = tmp_path / "autosave" / previous
    session_root.mkdir(parents=True)
    snap = session_root / "doc.snap"
    snap.write_text("recovered text", encoding="utf-8")
    begin_session(previous)
    offers = begin_session(current)
    assert len(offers) == 1
    assert offers[0].session_id == previous
    assert offers[0].snapshot == snap


def test_mark_clean_exit_prevents_future_offer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    session = str(uuid4())
    begin_session(session)
    mark_clean_exit(session)
    offers = begin_session(str(uuid4()))
    assert offers == []


def test_latest_session_snapshot_and_reader(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    session = str(uuid4())
    root = tmp_path / "autosave" / session
    root.mkdir(parents=True)
    older = root / "old.snap"
    newer = root / "new.snap"
    older.write_text("old", encoding="utf-8")
    time.sleep(0.01)
    newer.write_text("new", encoding="utf-8")
    latest = latest_session_snapshot(session)
    assert latest == newer
    assert read_recovery_snapshot(newer) == "new"
