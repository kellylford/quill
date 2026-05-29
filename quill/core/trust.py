from __future__ import annotations

from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic


def trusted_locations_path() -> Path:
    return app_data_dir() / "trusted_locations.json"


def load_trusted_locations() -> set[Path]:
    raw = read_json(trusted_locations_path(), default=[])
    if not isinstance(raw, list):
        return set()
    trusted: set[Path] = set()
    for value in raw:
        if isinstance(value, str):
            trusted.add(Path(value).resolve())
    return trusted


def save_trusted_locations(locations: set[Path]) -> None:
    serialized = sorted(str(path.resolve()) for path in locations)
    write_json_atomic(trusted_locations_path(), serialized)


def is_trusted_location(path: Path, locations: set[Path]) -> bool:
    resolved = path.resolve()
    parents = [resolved]
    parents.extend(resolved.parents)
    return any(parent in locations for parent in parents)
