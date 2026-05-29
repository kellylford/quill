from __future__ import annotations

from pathlib import Path

from quill.core.storage import read_json, write_json_atomic


def test_write_and_read_json(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    payload = {"a": 1, "b": ["x", "y"]}
    write_json_atomic(target, payload)
    loaded = read_json(target, default={})
    assert loaded == payload


def test_read_json_returns_default_for_missing_file(tmp_path: Path) -> None:
    target = tmp_path / "missing.json"
    loaded = read_json(target, default={"ok": True})
    assert loaded == {"ok": True}
