from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    license_name: str
