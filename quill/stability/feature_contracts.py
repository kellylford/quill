"""Feature contract and validation.

Implements: ROADMAP FLAG-1 / FLAG-2 (the per-feature stability and
maturity contract that the feature manager, palette, menu gating, and
status bar all honour). Every user-facing feature that touches the
UI, network, or a long-running worker registers a
:class:`FeatureContract` so Safe Mode, the feature profiles, and the
Why-Don't-I-See-a-Feature dialog all have a single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeatureContract:
    feature_id: str
    display_name: str
    stability_level: str
    default_enabled: bool
    disabled_in_safe_mode: bool
    runs_on_wx_main_thread: bool
    supports_cancellation: bool
    reports_progress: bool
    diagnostic_category: str
    requires_timeout: bool | None = None


def validate_feature_contract(contract: FeatureContract) -> None:
    risky = contract.stability_level.lower() in {"beta", "experimental", "risky", "advanced"}
    if risky and contract.runs_on_wx_main_thread:
        raise ValueError(
            f"Feature {contract.feature_id!r} is marked risky but runs on the wx main thread."
        )
    if contract.requires_timeout and not contract.supports_cancellation:
        raise ValueError(
            f"Feature {contract.feature_id!r} requires a timeout but does not support cancellation."
        )
