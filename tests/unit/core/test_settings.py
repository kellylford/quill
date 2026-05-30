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
            wrap_find=False,
            indent_with_tabs=True,
            indent_size=2,
            auto_check_updates=True,
            recent_files_limit=7,
            tray_enabled=True,
            persistent_undo=True,
            spellcheck_as_you_type=True,
            title_bar_path_mode="full_path",
            dirty_title_style="asterisk_text",
            announcement_backend="prism",
            announcement_trace_enabled=True,
            status_bar_order=["line_column", "mode", "message", "file_path", "selection"],
            status_bar_hidden=["selection"],
        )
    )
    loaded = load_settings()
    assert loaded.theme == "dark"
    assert loaded.keyboard_pack == "VS Code"
    assert loaded.soft_wrap is False
    assert loaded.wrap_find is False
    assert loaded.indent_with_tabs is True
    assert loaded.indent_size == 2
    assert loaded.auto_check_updates is True
    assert loaded.recent_files_limit == 7
    assert loaded.tray_enabled is True
    assert loaded.persistent_undo is True
    assert loaded.spellcheck_as_you_type is True
    assert loaded.snippet_trigger_expansion is True
    assert loaded.title_bar_path_mode == "full_path"
    assert loaded.dirty_title_style == "asterisk_text"
    assert loaded.announcement_backend == "prism"
    assert loaded.announcement_trace_enabled is True
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


def test_settings_clamps_indent_size(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(
        '{"indent_size":0,"indent_with_tabs":1}',
        encoding="utf-8",
    )
    loaded = load_settings()
    assert loaded.indent_size == 1
    assert loaded.indent_with_tabs is True


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


def test_settings_normalize_announcement_backend(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(
        '{"announcement_backend":"not-real","announcement_trace_enabled":1}',
        encoding="utf-8",
    )

    loaded = load_settings()

    assert loaded.announcement_backend == "auto"
    assert loaded.announcement_trace_enabled is True


def test_settings_defaults_snippet_trigger_expansion_to_true(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text("{}", encoding="utf-8")
    loaded = load_settings()
    assert loaded.snippet_trigger_expansion is True
