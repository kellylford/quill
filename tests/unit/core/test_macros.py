from __future__ import annotations

from pathlib import Path

import pytest

import quill.core.macros as macros_module
from quill.core.macros import MacroManager


def test_macro_manager_records_and_plays(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(macros_module, "macros_path", lambda: tmp_path / "macros.json")
    manager = MacroManager.load()

    manager.start_recording("demo")
    manager.record("edit.find")
    manager.record("edit.find_next")
    saved = manager.stop_recording()

    assert saved is not None
    assert saved.name == "demo"
    assert saved.steps == ["edit.find", "edit.find_next"]

    played: list[str] = []
    manager.play_last_macro(played.append)
    assert played == ["edit.find", "edit.find_next"]


def test_macro_manager_ignores_recording_during_playback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(macros_module, "macros_path", lambda: tmp_path / "macros.json")
    manager = MacroManager.load()
    manager.start_recording("demo")
    manager.record("edit.find")
    manager.stop_recording()

    def runner(command_id: str) -> None:
        manager.record(command_id)

    manager.play_last_macro(runner)
    assert manager.macros["demo"].steps == ["edit.find"]


def test_macro_manager_rename_delete_and_reload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(macros_module, "macros_path", lambda: tmp_path / "macros.json")
    manager = MacroManager.load()
    manager.start_recording("demo")
    manager.record("edit.find")
    manager.stop_recording()
    manager.rename_macro("demo", "renamed")
    assert "renamed" in manager.macros
    manager.delete_macro("renamed")
    assert manager.macros == {}

    reloaded = MacroManager.load()
    assert reloaded.macros == {}
