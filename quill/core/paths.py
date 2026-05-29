from __future__ import annotations

import os
from pathlib import Path

from quill.core.storage_mode import load_storage_mode, portable_root_dir


def app_data_dir() -> Path:
    override = os.environ.get("QUILL_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    portable_root = portable_root_dir()
    if portable_root is not None:
        mode = load_storage_mode()
        if mode == "portable":
            return portable_root
        if mode == "appdata":
            appdata = os.environ.get("APPDATA")
            if appdata:
                return Path(appdata) / "Quill"
            return Path.home() / ".quill"

    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Quill"

    return Path.home() / ".quill"


def ensure_app_directories() -> None:
    root = app_data_dir()
    for relative in ("", "logs", "diagnostics", "backups", "autosave", "sessions"):
        (root / relative).mkdir(parents=True, exist_ok=True)
