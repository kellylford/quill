from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic

STATUS_BAR_ITEMS: tuple[str, ...] = (
    "message",
    "line_column",
    "word_count",
    "mode",
    "selection",
    "encoding",
    "line_endings",
    "spell_check",
    "background_tasks",
    "notifications",
    "read_aloud",
    "autosave",
    "search_term",
    "file_path",
)


def _normalize_status_bar_order(raw: object) -> list[str]:
    if not isinstance(raw, list):
        values: list[str] = []
    else:
        values = [value for value in raw if isinstance(value, str)]
    allowed = set(STATUS_BAR_ITEMS)
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in allowed or value in seen:
            continue
        unique.append(value)
        seen.add(value)
    for item in STATUS_BAR_ITEMS:
        if item not in seen:
            unique.append(item)
    return unique


def _normalize_status_bar_hidden(raw: object, order: list[str]) -> list[str]:
    if not isinstance(raw, list):
        return [
            "selection",
            "encoding",
            "line_endings",
            "spell_check",
            "background_tasks",
            "notifications",
            "read_aloud",
            "autosave",
            "search_term",
        ]
    order_set = set(order)
    hidden: list[str] = []
    seen: set[str] = set()
    for value in raw:
        if not isinstance(value, str):
            continue
        if value not in order_set or value in seen:
            continue
        hidden.append(value)
        seen.add(value)
    return hidden


@dataclass(slots=True)
class Settings:
    theme: str = "system"
    keyboard_pack: str = "Quill Default"
    soft_wrap: bool = True
    wrap_find: bool = True
    recent_files_limit: int = 10
    tray_enabled: bool = False
    persistent_undo: bool = False
    spellcheck_as_you_type: bool = False
    show_line_numbers: bool = True
    start_with_no_document_open: bool = False
    read_aloud_voice: str = ""
    status_bar_order: list[str] = field(default_factory=lambda: list(STATUS_BAR_ITEMS))
    status_bar_hidden: list[str] = field(
        default_factory=lambda: [
            "selection",
            "encoding",
            "line_endings",
            "spell_check",
            "background_tasks",
            "notifications",
            "read_aloud",
            "autosave",
            "search_term",
        ]
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        theme = str(data.get("theme", "system"))
        keyboard_pack = str(data.get("keyboard_pack", "Quill Default"))
        soft_wrap = bool(data.get("soft_wrap", True))
        wrap_find = bool(data.get("wrap_find", True))
        recent_files_limit = int(data.get("recent_files_limit", 10))
        tray_enabled = bool(data.get("tray_enabled", False))
        persistent_undo = bool(data.get("persistent_undo", False))
        spellcheck_as_you_type = bool(data.get("spellcheck_as_you_type", False))
        show_line_numbers = bool(data.get("show_line_numbers", True))
        start_with_no_document_open = bool(data.get("start_with_no_document_open", False))
        read_aloud_voice = str(data.get("read_aloud_voice", ""))
        status_bar_order = _normalize_status_bar_order(data.get("status_bar_order"))
        status_bar_hidden = _normalize_status_bar_hidden(
            data.get("status_bar_hidden"), status_bar_order
        )
        if recent_files_limit < 1:
            recent_files_limit = 1
        if recent_files_limit > 50:
            recent_files_limit = 50
        return cls(
            theme=theme,
            keyboard_pack=keyboard_pack,
            soft_wrap=soft_wrap,
            wrap_find=wrap_find,
            recent_files_limit=recent_files_limit,
            tray_enabled=tray_enabled,
            persistent_undo=persistent_undo,
            spellcheck_as_you_type=spellcheck_as_you_type,
            show_line_numbers=show_line_numbers,
            start_with_no_document_open=start_with_no_document_open,
            read_aloud_voice=read_aloud_voice,
            status_bar_order=status_bar_order,
            status_bar_hidden=status_bar_hidden,
        )


def settings_path() -> Path:
    return app_data_dir() / "settings.json"


def load_settings() -> Settings:
    raw = read_json(settings_path(), default={})
    if not isinstance(raw, dict):
        return Settings()
    return Settings.from_dict(raw)


def save_settings(settings: Settings) -> None:
    write_json_atomic(settings_path(), asdict(settings))
