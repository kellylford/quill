"""Tests for the pluggable watch-action registry (WATCH-2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.watch_actions import (
    OUTCOME_DONE,
    OUTCOME_FAILED,
    OUTCOME_SKIPPED,
    MoveAction,
    OpenAction,
    UnavailableAction,
    WatchAction,
    WatchActionOutcome,
    WatchActionRegistry,
    WatchItem,
    default_registry,
)


def _item(path: Path) -> WatchItem:
    return WatchItem(source_path=path, profile_id="p1")


def test_outcome_helpers_and_ok_flag() -> None:
    assert WatchActionOutcome.done("hi").ok is True
    assert WatchActionOutcome.failed("nope").ok is False
    assert WatchActionOutcome.skipped("later").status == OUTCOME_SKIPPED


def test_register_and_get_round_trip() -> None:
    registry = WatchActionRegistry()
    action = OpenAction(on_open=lambda _p: None)
    registry.register(action)
    assert registry.get("open") is action
    assert registry.get("missing") is None


def test_register_rejects_empty_id() -> None:
    registry = WatchActionRegistry()
    with pytest.raises(ValueError):
        registry.register(OpenAction(action_id=""))


def test_register_rejects_duplicate_without_replace() -> None:
    registry = WatchActionRegistry()
    registry.register(MoveAction())
    with pytest.raises(ValueError):
        registry.register(MoveAction())


def test_register_replace_supersedes_placeholder() -> None:
    registry = WatchActionRegistry()
    registry.register(UnavailableAction(action_id="glow_audit", label="GLOW", reason="not yet"))
    real = MoveAction(action_id="glow_audit", label="GLOW real")
    registry.register(real, replace=True)
    assert registry.get("glow_audit") is real


def test_actions_are_sorted_by_id() -> None:
    registry = WatchActionRegistry()
    registry.register(OpenAction(on_open=lambda _p: None))
    registry.register(MoveAction())
    ids = [action.action_id for action in registry.actions()]
    assert ids == sorted(ids)


def test_feature_gating_filters_available_actions() -> None:
    enabled = {"future.glow": False}
    registry = WatchActionRegistry(feature_enabled=lambda fid: enabled.get(fid, True))
    registry.register(OpenAction(on_open=lambda _p: None))  # no feature -> always on
    registry.register(
        UnavailableAction(
            action_id="glow_audit",
            label="GLOW",
            required_feature_id="future.glow",
            reason="not yet",
        )
    )
    available_ids = {action.action_id for action in registry.available_actions()}
    assert "open" in available_ids
    assert "glow_audit" not in available_ids
    assert registry.is_available("open") is True
    assert registry.is_available("glow_audit") is False


def test_run_unknown_action_fails_clearly() -> None:
    registry = WatchActionRegistry()
    outcome = registry.run("nope", _item(Path("x.txt")))
    assert outcome.status == OUTCOME_FAILED
    assert "Unknown watch action" in outcome.message


def test_run_disabled_feature_is_skipped_not_failed() -> None:
    registry = WatchActionRegistry(feature_enabled=lambda _fid: False)
    registry.register(
        UnavailableAction(
            action_id="glow_audit",
            label="GLOW",
            required_feature_id="future.glow",
            reason="not yet",
        )
    )
    outcome = registry.run("glow_audit", _item(Path("x.txt")))
    assert outcome.status == OUTCOME_SKIPPED


def test_run_invalid_options_fails_before_running() -> None:
    registry = WatchActionRegistry()
    registry.register(MoveAction())
    outcome = registry.run("move", _item(Path("x.txt")), {"destination": ""})
    assert outcome.status == OUTCOME_FAILED
    assert "destination" in outcome.message.lower()


def test_open_action_invokes_callback(tmp_path: Path) -> None:
    seen: list[Path] = []
    registry = WatchActionRegistry()
    registry.register(OpenAction(on_open=seen.append))
    source = tmp_path / "doc.txt"
    source.write_text("hi", encoding="utf-8")
    outcome = registry.run("open", _item(source))
    assert outcome.status == OUTCOME_DONE
    assert seen == [source]


def test_open_action_without_handler_fails() -> None:
    registry = WatchActionRegistry()
    registry.register(OpenAction())  # no handler
    outcome = registry.run("open", _item(Path("x.txt")))
    assert outcome.status == OUTCOME_FAILED


def test_move_action_moves_file(tmp_path: Path) -> None:
    source = tmp_path / "in" / "doc.txt"
    source.parent.mkdir()
    source.write_text("hi", encoding="utf-8")
    dest = tmp_path / "out"
    dest.mkdir()
    registry = WatchActionRegistry()
    registry.register(MoveAction())
    outcome = registry.run("move", _item(source), {"destination": str(dest)})
    assert outcome.status == OUTCOME_DONE
    assert not source.exists()
    assert (dest / "doc.txt").exists()
    assert outcome.result_path == dest / "doc.txt"


def test_run_guards_against_action_crash() -> None:
    class Boom(MoveAction):
        def validate(self, options) -> list[str]:  # type: ignore[override]
            return []

        def run(self, item: WatchItem, options) -> WatchActionOutcome:  # type: ignore[override]
            raise RuntimeError("kaboom")

    registry = WatchActionRegistry()
    registry.register(Boom(action_id="boom", label="Boom"))
    outcome = registry.run("boom", _item(Path("x.txt")))
    assert outcome.status == OUTCOME_FAILED
    assert "kaboom" in outcome.message


def test_default_registry_has_builtins_and_placeholders() -> None:
    registry = default_registry(on_open=lambda _p: None)
    ids = {action.action_id for action in registry.actions()}
    assert {"open", "move", "glow_audit", "bw_transcribe"} <= ids


def test_actions_satisfy_protocol() -> None:
    for action in (OpenAction(), MoveAction(), UnavailableAction(action_id="x", label="X")):
        assert isinstance(action, WatchAction)
