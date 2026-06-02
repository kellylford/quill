"""Tests for the persistent watch profile store (WATCH-5)."""

from __future__ import annotations

from pathlib import Path

from quill.core.watch_profile_store import WatchProfileStore
from quill.core.watch_profiles import WatchProfile


def _profile(name: str = "Inbox", folder: str = "", enabled: bool = True) -> WatchProfile:
    return WatchProfile(name=name, folder_path=folder, enabled=enabled)


def test_add_assigns_id_and_persists(tmp_path: Path) -> None:
    store = WatchProfileStore()
    added = store.add(_profile())
    assert added.profile_id
    assert store.get(added.profile_id) is not None
    assert len(store.profiles()) == 1


def test_add_reassigns_duplicate_id() -> None:
    store = WatchProfileStore()
    first = store.add(WatchProfile(profile_id="dup", name="A"))
    second = store.add(WatchProfile(profile_id="dup", name="B"))
    assert first.profile_id != second.profile_id


def test_update_replaces_existing() -> None:
    store = WatchProfileStore()
    added = store.add(_profile(name="Old"))
    from dataclasses import replace

    changed = replace(added, name="New")
    assert store.update(changed) is True
    assert store.get(added.profile_id).name == "New"


def test_update_missing_returns_false() -> None:
    store = WatchProfileStore()
    assert store.update(WatchProfile(profile_id="ghost")) is False


def test_duplicate_creates_disabled_copy() -> None:
    store = WatchProfileStore()
    added = store.add(_profile(name="Inbox", enabled=True))
    copy = store.duplicate(added.profile_id)
    assert copy is not None
    assert copy.profile_id != added.profile_id
    assert copy.enabled is False
    assert copy.name == "Inbox (copy)"


def test_set_enabled_toggles() -> None:
    store = WatchProfileStore()
    added = store.add(_profile(enabled=True))
    assert store.set_enabled(added.profile_id, False) is True
    assert store.get(added.profile_id).enabled is False
    assert store.enabled_profiles() == []


def test_delete_removes() -> None:
    store = WatchProfileStore()
    added = store.add(_profile())
    assert store.delete(added.profile_id) is True
    assert store.get(added.profile_id) is None
    assert store.delete("ghost") is False


def test_move_reorders() -> None:
    store = WatchProfileStore()
    store.add(_profile(name="A"))
    b = store.add(_profile(name="B"))
    assert [p.name for p in store.profiles()] == ["A", "B"]
    assert store.move(b.profile_id, -1) is True
    assert [p.name for p in store.profiles()] == ["B", "A"]
    # Out of range is rejected.
    assert store.move(b.profile_id, -1) is False


def test_lookup_alias_matches_get() -> None:
    store = WatchProfileStore()
    added = store.add(_profile())
    assert store.lookup(added.profile_id) is store.get(added.profile_id)


def test_persistence_round_trip(tmp_path: Path) -> None:
    store_path = tmp_path / "profiles.json"
    store = WatchProfileStore(storage_path=store_path)
    store.add(_profile(name="Inbox", folder=str(tmp_path)))
    store.add(_profile(name="Archive", folder=str(tmp_path), enabled=False))

    reloaded = WatchProfileStore(storage_path=store_path)
    names = [p.name for p in reloaded.profiles()]
    assert names == ["Inbox", "Archive"]
    assert len(reloaded.enabled_profiles()) == 1


def test_load_reassigns_duplicate_ids_on_disk(tmp_path: Path) -> None:
    store_path = tmp_path / "profiles.json"
    payload = {
        "schema_version": 1,
        "profiles": [
            {"profile_id": "same", "name": "A"},
            {"profile_id": "same", "name": "B"},
        ],
    }
    import json

    store_path.write_text(json.dumps(payload), encoding="utf-8")
    store = WatchProfileStore(storage_path=store_path)
    ids = {p.profile_id for p in store.profiles()}
    assert len(ids) == 2


def test_replace_all(tmp_path: Path) -> None:
    store = WatchProfileStore()
    store.add(_profile(name="Old"))
    store.replace_all([_profile(name="Fresh")])
    assert [p.name for p in store.profiles()] == ["Fresh"]
