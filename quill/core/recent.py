from __future__ import annotations

from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic


def recent_path() -> Path:
    return app_data_dir() / "recent.json"


def load_recent_files() -> list[Path]:
    raw = read_json(recent_path(), default=[])
    if not isinstance(raw, list):
        return []
    results: list[Path] = []
    for item in raw:
        if isinstance(item, str):
            results.append(Path(item))
    return results


def add_recent_file(path: Path, limit: int) -> list[Path]:
    normalized = path.resolve()
    existing = [entry.resolve() for entry in load_recent_files()]
    deduped = [entry for entry in existing if entry != normalized]
    updated = [normalized, *deduped][:limit]
    write_json_atomic(recent_path(), [str(entry) for entry in updated])
    return updated


def clear_recent_files() -> None:
    write_json_atomic(recent_path(), [])
