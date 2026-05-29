from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.settings import STATUS_BAR_ITEMS, Settings, load_settings, save_settings


def test_settings_round_trip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    save_settings(
        Settings(
            theme="dark",
            keyboard_pack="VS Code",
            soft_wrap=False,
            recent_files_limit=7,
            tray_enabled=True,
            persistent_undo=True,
            spellcheck_as_you_type=True,
            status_bar_order=["line_column", "mode", "message", "file_path", "selection"],
            status_bar_hidden=["selection"],
        )
    )
    loaded = load_settings()
    assert loaded.theme == "dark"
    assert loaded.keyboard_pack == "VS Code"
    assert loaded.soft_wrap is False
    assert loaded.recent_files_limit == 7
    assert loaded.tray_enabled is True
    assert loaded.persistent_undo is True
    assert loaded.spellcheck_as_you_type is True
    expected_order = list(
        dict.fromkeys(
            [
                "line_column",
                "mode",
                "message",
                "file_path",
                "selection",
                *STATUS_BAR_ITEMS,
            ]
        )
    )
    assert loaded.status_bar_order == expected_order
    assert loaded.status_bar_hidden == ["selection"]


def test_settings_clamps_recent_file_limit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    save_settings(Settings(recent_files_limit=1000))
    loaded = load_settings()
    assert loaded.recent_files_limit == 50


def test_settings_normalize_status_bar_layout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(
        (
            '{"status_bar_order":["line_column","line_column","unknown"],'
            '"status_bar_hidden":["line_column","missing"]}'
        ),
        encoding="utf-8",
    )
    loaded = load_settings()
    expected_order = list(dict.fromkeys(["line_column", *STATUS_BAR_ITEMS]))
    assert loaded.status_bar_order == expected_order
    assert loaded.status_bar_hidden == ["line_column"]
