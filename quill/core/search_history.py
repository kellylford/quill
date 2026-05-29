from __future__ import annotations

from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic


def search_history_path() -> Path:
    return app_data_dir() / "search-history.json"


def load_search_history() -> list[str]:
    raw = read_json(search_history_path(), default=[])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str)]


def add_search_term(term: str, limit: int = 100) -> list[str]:
    clean = term.strip()
    if not clean:
        return load_search_history()
    existing = [item for item in load_search_history() if item != clean]
    updated = [clean, *existing][:limit]
    write_json_atomic(search_history_path(), updated)
    return updated
