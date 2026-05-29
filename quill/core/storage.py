from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as file_handle:
        json.dump(data, file_handle, indent=2, sort_keys=True, ensure_ascii=False)
        file_handle.write("\n")
    temp_path.replace(path)
