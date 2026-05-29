from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.trust import is_trusted_location, load_trusted_locations, save_trusted_locations


def test_is_trusted_location_matches_parent_path() -> None:
    root = Path(r"C:\trusted").resolve()
    target = root / "docs" / "file.txt"
    assert is_trusted_location(target, {root}) is True


def test_trusted_locations_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    trusted = {Path(r"C:\one").resolve(), Path(r"C:\two").resolve()}
    save_trusted_locations(trusted)
    loaded = load_trusted_locations()
    assert loaded == trusted
