from __future__ import annotations

import os
from pathlib import Path

from quill.core.storage import read_json, write_json_atomic

_VALID_MODES = {"appdata", "portable"}


def portable_root_dir() -> Path | None:
    override = os.environ.get("QUILL_PORTABLE_ROOT")
    if not override:
        return None
    return Path(override).expanduser().resolve()


def storage_mode_path() -> Path | None:
    root = portable_root_dir()
    if root is None:
        return None
    return root / "storage-mode.json"


def load_storage_mode() -> str | None:
    path = storage_mode_path()
    if path is None:
        return None
    raw = read_json(path, default={})
    if not isinstance(raw, dict):
        return None
    mode = raw.get("mode")
    if isinstance(mode, str) and mode in _VALID_MODES:
        return mode
    return None


def save_storage_mode(mode: str) -> None:
    if mode not in _VALID_MODES:
        raise ValueError(f"Unknown storage mode: {mode}")
    path = storage_mode_path()
    if path is None:
        raise RuntimeError("Portable root is not configured")
    write_json_atomic(path, {"mode": mode})
