from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.undo_store import clear_undo_history, load_undo_history, save_undo_history


def test_save_and_load_undo_history(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    target = tmp_path / "note.md"
    target.write_text("x", encoding="utf-8")
    save_undo_history(target, ["a", "b", "c"])
    assert load_undo_history(target) == ["a", "b", "c"]


def test_save_undo_history_honors_limit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    target = tmp_path / "note.md"
    target.write_text("x", encoding="utf-8")
    save_undo_history(target, ["1", "2", "3", "4"], limit=2)
    assert load_undo_history(target) == ["3", "4"]


def test_clear_undo_history(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    target = tmp_path / "note.md"
    target.write_text("x", encoding="utf-8")
    save_undo_history(target, ["one"])
    clear_undo_history(target)
    assert load_undo_history(target) == []
