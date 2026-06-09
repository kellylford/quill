"""Safe Mode configuration and detection.

Implements: ROADMAP SAFE-1 (the env-var contract for Safe Mode) and
H-SAFE-1 from the pre-release review. When ``QUILL_SAFE_MODE=1`` is
set in the environment, or ``--safe-mode`` is passed on the command
line, ``should_enable_safe_mode`` returns True and ``build_safe_mode_config``
produces a :class:`SafeModeConfig` that disables plugins, AI, network
services, and other non-essential surfaces for the lifetime of the
process.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SafeModeConfig:
    enabled: bool
    disable_plugins: bool = True
    disable_experimental_features: bool = True
    disable_ai_integrations: bool = True
    disable_startup_restore: bool = True
    disable_background_indexing: bool = True
    disable_file_watchers: bool = True
    disable_custom_themes: bool = True
    disable_custom_snippets: bool = True
    disable_network_services: bool = True


def build_safe_mode_config(enabled: bool) -> SafeModeConfig:
    return SafeModeConfig(enabled=enabled)


def should_enable_safe_mode(arguments: Sequence[str], environment: Mapping[str, str]) -> bool:
    if "--safe-mode" in arguments:
        return True
    return environment.get("QUILL_SAFE_MODE") == "1"
