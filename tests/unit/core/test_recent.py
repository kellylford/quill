from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.recent import add_recent_file, clear_recent_files, load_recent_files


def test_add_recent_file_prepends_and_dedupes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    one = tmp_path / "one.txt"
    two = tmp_path / "two.txt"
    one.write_text("1", encoding="utf-8")
    two.write_text("2", encoding="utf-8")

    add_recent_file(one, limit=10)
    add_recent_file(two, limit=10)
    items = add_recent_file(one, limit=10)

    assert items[0] == one.resolve()
    assert items[1] == two.resolve()
    assert len(items) == 2


def test_add_recent_file_honors_limit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    paths = []
    for index in range(5):
        current = tmp_path / f"{index}.txt"
        current.write_text("x", encoding="utf-8")
        add_recent_file(current, limit=3)
        paths.append(current.resolve())

    recent = load_recent_files()
    assert recent == list(reversed(paths[-3:]))


def test_clear_recent_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    one = tmp_path / "one.txt"
    one.write_text("1", encoding="utf-8")
    add_recent_file(one, limit=10)
    clear_recent_files()
    assert load_recent_files() == []
