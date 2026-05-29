from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.notifications import (
    add_notification,
    clear_notifications,
    load_notifications,
    save_notifications,
)


def test_add_notification_persists_entry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    entries = add_notification("Update available", "update")
    assert len(entries) == 1
    assert entries[0].message == "Update available"
    assert entries[0].category == "update"


def test_notifications_round_trip_and_clear(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    add_notification("One")
    add_notification("Two")
    loaded = load_notifications()
    assert [entry.message for entry in loaded] == ["One", "Two"]
    save_notifications(loaded, limit=1)
    trimmed = load_notifications()
    assert [entry.message for entry in trimmed] == ["Two"]
    clear_notifications()
    assert load_notifications() == []
