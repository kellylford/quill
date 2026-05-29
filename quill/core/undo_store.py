from __future__ import annotations

from hashlib import sha1
from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic


def load_undo_history(path: Path) -> list[str]:
    raw = read_json(_undo_path(path), default=[])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str)]


def save_undo_history(path: Path, history: list[str], limit: int = 100) -> list[str]:
    bounded = history[-max(limit, 1) :]
    write_json_atomic(_undo_path(path), bounded)
    return bounded


def clear_undo_history(path: Path) -> None:
    target = _undo_path(path)
    if target.exists():
        target.unlink()


def _undo_path(path: Path) -> Path:
    digest = sha1(str(path.resolve()).encode("utf-8")).hexdigest()
    return app_data_dir() / "undo" / f"{digest}.json"
