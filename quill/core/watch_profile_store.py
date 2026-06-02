"""Persistent store for watch profiles (WATCH-5).

Holds the ordered list of :class:`WatchProfile`s and supports create, edit,
duplicate, enable/disable, reorder, and delete, persisting atomically and
schema-validated so the set survives restarts. This is the model the accessible
profile manager dialog drives; it is UI-framework-agnostic (no ``wx`` imports).
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

from .storage import read_json, write_json_atomic
from .watch_profiles import WatchProfile

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


class WatchProfileStore:
    """Thread-safe, durable collection of watch profiles."""

    def __init__(self, *, storage_path: Path | None = None) -> None:
        self._storage_path = storage_path
        self._lock = threading.RLock()
        self._profiles: list[WatchProfile] = []
        if storage_path is not None:
            self._load()

    def profiles(self) -> list[WatchProfile]:
        with self._lock:
            return list(self._profiles)

    def enabled_profiles(self) -> list[WatchProfile]:
        with self._lock:
            return [p for p in self._profiles if p.enabled]

    def get(self, profile_id: str) -> WatchProfile | None:
        with self._lock:
            for profile in self._profiles:
                if profile.profile_id == profile_id:
                    return profile
        return None

    def lookup(self, profile_id: str) -> WatchProfile | None:
        """Alias suitable for passing directly as the worker's profile lookup."""
        return self.get(profile_id)

    def add(self, profile: WatchProfile) -> WatchProfile:
        """Add ``profile`` (assigning an id if missing) and persist."""
        normalized = profile.normalized()
        with self._lock:
            if not normalized.profile_id or self._has_id(normalized.profile_id):
                normalized = replace(normalized, profile_id=uuid.uuid4().hex)
            self._profiles.append(normalized)
            self._save_locked()
        return normalized

    def update(self, profile: WatchProfile) -> bool:
        """Replace the profile with the same id; returns ``False`` if not found."""
        normalized = profile.normalized()
        with self._lock:
            for index, existing in enumerate(self._profiles):
                if existing.profile_id == normalized.profile_id:
                    self._profiles[index] = normalized
                    self._save_locked()
                    return True
        return False

    def duplicate(self, profile_id: str) -> WatchProfile | None:
        """Create a disabled copy of a profile under a new id and name."""
        with self._lock:
            source = self.get(profile_id)
            if source is None:
                return None
            copy = replace(
                source,
                profile_id=uuid.uuid4().hex,
                name=f"{source.name} (copy)",
                enabled=False,
            )
            self._profiles.append(copy)
            self._save_locked()
            return copy

    def set_enabled(self, profile_id: str, enabled: bool) -> bool:
        with self._lock:
            for index, existing in enumerate(self._profiles):
                if existing.profile_id == profile_id:
                    self._profiles[index] = replace(existing, enabled=bool(enabled))
                    self._save_locked()
                    return True
        return False

    def delete(self, profile_id: str) -> bool:
        with self._lock:
            before = len(self._profiles)
            self._profiles = [p for p in self._profiles if p.profile_id != profile_id]
            if len(self._profiles) == before:
                return False
            self._save_locked()
            return True

    def move(self, profile_id: str, offset: int) -> bool:
        """Shift a profile up or down in the ordered list; returns success."""
        with self._lock:
            index = self._index_of(profile_id)
            if index is None:
                return False
            target = index + offset
            if target < 0 or target >= len(self._profiles):
                return False
            profile = self._profiles.pop(index)
            self._profiles.insert(target, profile)
            self._save_locked()
            return True

    def replace_all(self, profiles: Iterable[WatchProfile]) -> None:
        with self._lock:
            self._profiles = [p.normalized() for p in profiles]
            self._save_locked()

    # -- internals -------------------------------------------------------

    def _has_id(self, profile_id: str) -> bool:
        return any(p.profile_id == profile_id for p in self._profiles)

    def _index_of(self, profile_id: str) -> int | None:
        for index, profile in enumerate(self._profiles):
            if profile.profile_id == profile_id:
                return index
        return None

    def _save_locked(self) -> None:
        if self._storage_path is None:
            return
        payload = {
            "schema_version": SCHEMA_VERSION,
            "profiles": [p.to_dict() for p in self._profiles],
        }
        try:
            write_json_atomic(self._storage_path, payload)
        except OSError:
            logger.exception("Failed to persist watch profiles to %s", self._storage_path)

    def _load(self) -> None:
        assert self._storage_path is not None
        try:
            raw = read_json(self._storage_path, default=None)
        except (OSError, ValueError):
            logger.exception("Failed to read watch profiles from %s", self._storage_path)
            return
        if not isinstance(raw, dict):
            return
        raw_profiles = raw.get("profiles")
        if not isinstance(raw_profiles, list):
            return
        loaded: list[WatchProfile] = []
        seen_ids: set[str] = set()
        for entry in raw_profiles:
            if not isinstance(entry, dict):
                continue
            profile = WatchProfile.from_dict(entry)
            if profile.profile_id in seen_ids:
                profile = replace(profile, profile_id=uuid.uuid4().hex)
            seen_ids.add(profile.profile_id)
            loaded.append(profile)
        self._profiles = loaded


__all__ = ["SCHEMA_VERSION", "WatchProfileStore"]
