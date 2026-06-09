"""Versioned, nested serialization and migration for :class:`Settings` (SET-5).

The on-disk settings file historically stored a single flat JSON object. This
module adds a *nested, versioned* document shape that groups the flat
:class:`~quill.core.settings.Settings` fields by their registry group, while
keeping a clean migration path from the legacy flat file.

Design goals (SET-5):

* **Nested and versioned** - the document is ``{"schema_version", "groups"}``
  with one sub-object per settings group, so the file is readable and future
  schema changes can be detected and migrated.
* **Lossless round-trip** - every :class:`Settings` field is serialized,
  including fields that have no registry spec (they land in the ``_ungrouped``
  bucket), so ``from_versioned(to_versioned(s)) == s``.
* **Corrupt-file recovery that preserves other settings** - a bad value in one
  group falls back to that field's default without discarding the rest, because
  the flattened payload is validated field-by-field through
  :meth:`Settings.from_dict`.
* **Migration** - a legacy flat document (no ``groups`` key) is accepted and
  upgraded transparently.

No ``wx`` imports: this is pure model code. It is imported lazily by
:mod:`quill.core.settings` to avoid an import cycle with the registry.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from quill.core.settings import Settings
from quill.core.settings_registry import find_spec

#: Bump when the nested document shape changes incompatibly.
SETTINGS_SCHEMA_VERSION = 1

#: Bucket for fields that have no registry spec (still serialized, never lost).
UNGROUPED_KEY = "_ungrouped"


def _group_for_key(key: str) -> str:
    spec = find_spec(key)
    if spec is not None and spec.group:
        return spec.group
    return UNGROUPED_KEY


def to_versioned(settings: Settings) -> dict[str, Any]:
    """Return the nested, versioned document for ``settings``.

    Shape::

        {"schema_version": 1, "groups": {"general": {...}, "_ungrouped": {...}}}

    Every field is placed under its registry group; fields without a spec go to
    the ``_ungrouped`` bucket so the export stays lossless.
    """
    groups: dict[str, dict[str, Any]] = {}
    for key, value in asdict(settings).items():
        group_id = _group_for_key(key)
        groups.setdefault(group_id, {})[key] = value
    return {"schema_version": SETTINGS_SCHEMA_VERSION, "groups": groups}


def _flatten_groups(groups: object) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if not isinstance(groups, dict):
        return flat
    for bucket in groups.values():
        if isinstance(bucket, dict):
            for key, value in bucket.items():
                flat[str(key)] = value
    return flat


def migrate(raw: object) -> dict[str, Any]:
    """Return a flat settings mapping from any supported on-disk shape.

    Accepts the nested ``{"schema_version", "groups"}`` document, a legacy flat
    mapping, or junk (returns an empty mapping). The result is suitable for
    :meth:`Settings.from_dict`, which validates and defaults field-by-field.
    """
    if not isinstance(raw, dict):
        return {}
    if "groups" in raw:
        return _flatten_groups(raw.get("groups"))
    # Legacy flat document: every key is already a candidate field.
    return {str(key): value for key, value in raw.items() if key != "schema_version"}


def _accepts(key: str, value: Any) -> bool:
    try:
        Settings.from_dict({key: value})
    except (TypeError, ValueError):
        return False
    return True


def _safe_from_dict(flat: dict[str, Any]) -> Settings:
    try:
        return Settings.from_dict(flat)
    except (TypeError, ValueError):
        # A corrupt value raised on the whole load; keep every field that
        # validates on its own and drop only the offending ones.
        good: dict[str, Any] = {}
        for key, value in flat.items():
            try:
                Settings.from_dict({key: value})
                good[key] = value
            except (TypeError, ValueError):
                continue
        return Settings.from_dict(good)


def from_versioned(raw: object) -> Settings:
    """Build a validated :class:`Settings` from any supported document shape.

    A corrupt individual value is dropped (falling back to that field's
    default) without discarding the surrounding settings; an unreadable
    document yields an all-defaults :class:`Settings`.
    """
    return _safe_from_dict(migrate(raw))
