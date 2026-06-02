"""Pluggable watch-action registry (WATCH-2).

A watch *action* is the single operation a watch profile performs on each file
it claims. Actions implement a small, stable contract so new ones register
without touching the watch engine, and each action declares the feature id it
requires so the registry can gate it through the feature manager (FLAG-1).

This module is UI-framework-agnostic: no ``wx`` imports. The registry is the
seam that GLOW (WATCH-8) and BITS Whisperer (WATCH-9) plug into, and the same
seam the built-in actions (WATCH-7) use.
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

#: Outcome status values for a single action run.
OUTCOME_DONE = "done"
OUTCOME_FAILED = "failed"
OUTCOME_SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class WatchItem:
    """One file claimed by a profile, handed to an action's ``run``."""

    source_path: Path
    profile_id: str = ""


@dataclass(frozen=True, slots=True)
class WatchActionOutcome:
    """The result of running an action on a single item."""

    status: str  # OUTCOME_DONE | OUTCOME_FAILED | OUTCOME_SKIPPED
    message: str = ""
    result_path: Path | None = None

    @property
    def ok(self) -> bool:
        return self.status == OUTCOME_DONE

    @classmethod
    def done(cls, message: str = "", result_path: Path | None = None) -> WatchActionOutcome:
        return cls(OUTCOME_DONE, message, result_path)

    @classmethod
    def failed(cls, message: str) -> WatchActionOutcome:
        return cls(OUTCOME_FAILED, message)

    @classmethod
    def skipped(cls, message: str) -> WatchActionOutcome:
        return cls(OUTCOME_SKIPPED, message)


@runtime_checkable
class WatchAction(Protocol):
    """The contract every watch action implements.

    Attributes
    ----------
    action_id:
        Stable identifier used to bind a profile to this action and to persist
        the choice. Never changes across releases.
    label:
        Short human-readable name for menus and the monitor.
    required_feature_id:
        Feature id this action needs; an empty string means always available.
    """

    action_id: str
    label: str
    required_feature_id: str

    def describe(self) -> str:
        """Return a plain-language sentence describing what the action does."""

    def validate(self, options: Mapping[str, object]) -> list[str]:
        """Return a list of human-readable problems with ``options`` (empty if valid)."""

    def run(self, item: WatchItem, options: Mapping[str, object]) -> WatchActionOutcome:
        """Perform the action for ``item`` and return its outcome."""


@dataclass(slots=True)
class _BaseAction:
    """Shared defaults so concrete actions only override what they need."""

    action_id: str = ""
    label: str = ""
    required_feature_id: str = ""
    description: str = ""

    def describe(self) -> str:
        return self.description

    def validate(self, options: Mapping[str, object]) -> list[str]:  # noqa: ARG002
        return []

    def run(self, item: WatchItem, options: Mapping[str, object]) -> WatchActionOutcome:
        raise NotImplementedError


@dataclass(slots=True)
class OpenAction(_BaseAction):
    """Built-in action: hand the file to the editor (WATCH-7).

    The actual open is performed by a caller-supplied callback so this stays
    UI-agnostic; the callback receives the source path and returns nothing.
    """

    action_id: str = "open"
    label: str = "Open in editor"
    description: str = "Open each detected file in a new editor tab."
    on_open: Callable[[Path], None] | None = None

    def validate(self, options: Mapping[str, object]) -> list[str]:  # noqa: ARG002
        if self.on_open is None:
            return ["No open handler is configured for this action."]
        return []

    def run(self, item: WatchItem, options: Mapping[str, object]) -> WatchActionOutcome:  # noqa: ARG002
        if self.on_open is None:
            return WatchActionOutcome.failed("No open handler is configured.")
        try:
            self.on_open(item.source_path)
        except Exception as error:  # surfaced as a failed outcome
            logger.exception("Open watch action failed for %s", item.source_path)
            return WatchActionOutcome.failed(str(error))
        return WatchActionOutcome.done(f"Opened {item.source_path.name}")


@dataclass(slots=True)
class MoveAction(_BaseAction):
    """Built-in action: move each file to a destination folder (WATCH-7)."""

    action_id: str = "move"
    label: str = "Move to folder"
    description: str = "Move each detected file into a chosen destination folder."

    def validate(self, options: Mapping[str, object]) -> list[str]:
        destination = str(options.get("destination", "")).strip()
        if not destination:
            return ["Choose a destination folder for moved files."]
        if not Path(destination).expanduser().is_dir():
            return [f"Destination folder does not exist: {destination}"]
        return []

    def run(self, item: WatchItem, options: Mapping[str, object]) -> WatchActionOutcome:
        problems = self.validate(options)
        if problems:
            return WatchActionOutcome.failed(problems[0])
        destination = Path(str(options.get("destination", "")).strip()).expanduser()
        target = destination / item.source_path.name
        try:
            moved = shutil.move(str(item.source_path), str(target))
        except Exception as error:  # surfaced as a failed outcome
            logger.exception("Move watch action failed for %s", item.source_path)
            return WatchActionOutcome.failed(str(error))
        return WatchActionOutcome.done(f"Moved to {target.name}", result_path=Path(moved))


@dataclass(slots=True)
class UnavailableAction(_BaseAction):
    """Placeholder for an action whose engine has not landed yet (WATCH-8/9).

    It registers under a stable id and feature, but always reports itself
    unavailable with an announced reason until the real action replaces it.
    """

    reason: str = "This action is not available yet."

    def validate(self, options: Mapping[str, object]) -> list[str]:  # noqa: ARG002
        return [self.reason]

    def run(self, item: WatchItem, options: Mapping[str, object]) -> WatchActionOutcome:  # noqa: ARG002
        return WatchActionOutcome.skipped(self.reason)


class WatchActionRegistry:
    """A typed registry mapping action ids to actions, with feature gating."""

    def __init__(self, *, feature_enabled: Callable[[str], bool] | None = None) -> None:
        self._actions: dict[str, WatchAction] = {}
        self._feature_enabled = feature_enabled

    def register(self, action: WatchAction, *, replace: bool = False) -> None:
        """Register ``action`` under its ``action_id``.

        Raises :class:`ValueError` on a duplicate id unless ``replace`` is set,
        which lets a real action (e.g. GLOW) supersede its placeholder.
        """
        action_id = action.action_id
        if not action_id:
            raise ValueError("Watch action must declare a non-empty action_id.")
        if action_id in self._actions and not replace:
            raise ValueError(f"Watch action id already registered: {action_id}")
        self._actions[action_id] = action

    def get(self, action_id: str) -> WatchAction | None:
        return self._actions.get(action_id)

    def actions(self) -> list[WatchAction]:
        """Every registered action, ordered by id for stable presentation."""
        return [self._actions[key] for key in sorted(self._actions)]

    def is_feature_enabled(self, action: WatchAction) -> bool:
        feature_id = action.required_feature_id
        if not feature_id:
            return True
        if self._feature_enabled is None:
            return True
        return bool(self._feature_enabled(feature_id))

    def available_actions(self) -> list[WatchAction]:
        """Registered actions whose required feature is currently enabled."""
        return [action for action in self.actions() if self.is_feature_enabled(action)]

    def is_available(self, action_id: str) -> bool:
        action = self.get(action_id)
        return action is not None and self.is_feature_enabled(action)

    def run(
        self,
        action_id: str,
        item: WatchItem,
        options: Mapping[str, object] | None = None,
    ) -> WatchActionOutcome:
        """Validate, gate, then run ``action_id`` for ``item``.

        Returns a ``failed`` outcome for an unknown action or invalid options,
        and a ``skipped`` outcome when the action's feature is disabled, so the
        queue always receives a definite result rather than an exception.
        """
        action = self.get(action_id)
        if action is None:
            return WatchActionOutcome.failed(f"Unknown watch action: {action_id}")
        if not self.is_feature_enabled(action):
            return WatchActionOutcome.skipped(
                f"The feature for action '{action.label}' is turned off."
            )
        opts: Mapping[str, object] = options or {}
        problems = action.validate(opts)
        if problems:
            return WatchActionOutcome.failed(problems[0])
        try:
            return action.run(item, opts)
        except Exception as error:  # last-resort guard so one file never crashes the loop
            logger.exception("Watch action %s crashed for %s", action_id, item.source_path)
            return WatchActionOutcome.failed(str(error))


def default_registry(
    *,
    feature_enabled: Callable[[str], bool] | None = None,
    on_open: Callable[[Path], None] | None = None,
) -> WatchActionRegistry:
    """Build a registry pre-populated with the built-in actions and placeholders."""
    registry = WatchActionRegistry(feature_enabled=feature_enabled)
    registry.register(OpenAction(on_open=on_open))
    registry.register(MoveAction())
    registry.register(
        UnavailableAction(
            action_id="glow_audit",
            label="Audit and fix accessibility (GLOW)",
            required_feature_id="future.glow",
            description="Run the GLOW audit-and-fix flow over each arriving document.",
            reason="GLOW accessibility auditing is not available yet.",
        )
    )
    registry.register(
        UnavailableAction(
            action_id="bw_transcribe",
            label="Transcribe audio (BITS Whisperer)",
            required_feature_id="future.bits_whisperer",
            description="Transcribe arriving audio into an editable document.",
            reason="BITS Whisperer transcription is not available yet.",
        )
    )
    return registry


__all__ = [
    "OUTCOME_DONE",
    "OUTCOME_FAILED",
    "OUTCOME_SKIPPED",
    "MoveAction",
    "OpenAction",
    "UnavailableAction",
    "WatchAction",
    "WatchActionOutcome",
    "WatchActionRegistry",
    "WatchItem",
    "default_registry",
]
