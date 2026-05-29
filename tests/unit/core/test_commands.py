import pytest

from quill.core.commands import CommandRegistry


def test_command_registry_runs_registered_command() -> None:
    registry = CommandRegistry()
    called = {"value": False}

    def handler() -> None:
        called["value"] = True

    registry.register("test.run", "Run test", handler, "Ctrl+T")
    registry.run("test.run")
    assert called["value"] is True


def test_command_registry_rejects_duplicate_ids() -> None:
    registry = CommandRegistry()
    registry.register("test.run", "Run test", lambda: None)
    with pytest.raises(ValueError):
        registry.register("test.run", "Run test duplicate", lambda: None)


def test_command_registry_raises_for_unknown_command() -> None:
    registry = CommandRegistry()
    with pytest.raises(KeyError):
        registry.run("missing.command")


def test_command_registry_notifies_run_listener() -> None:
    registry = CommandRegistry()
    called: list[str] = []
    observed: list[str] = []

    def handler() -> None:
        called.append("ran")

    registry.register("test.run", "Run test", handler)
    registry.set_run_listener(observed.append)
    registry.run("test.run")

    assert called == ["ran"]
    assert observed == ["test.run"]


def test_command_registry_clears_run_listener() -> None:
    registry = CommandRegistry()
    observed: list[str] = []
    registry.register("test.run", "Run test", lambda: None)
    registry.set_run_listener(observed.append)
    registry.set_run_listener(None)
    registry.run("test.run")
    assert observed == []
