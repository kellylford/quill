"""Tests for the consented external-engine stdio boundary (AI-24)."""

from __future__ import annotations

import json
import subprocess

import pytest

from quill.core.ai import external_engine as ee


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    return tmp_path


def _echo_runner(payload: dict) -> ee.Runner:
    def runner(command, stdin_text, timeout):
        request = json.loads(stdin_text)
        out = dict(payload)
        out.setdefault("echo", request)
        return 0, json.dumps(out) + "\n", ""

    return runner


def test_master_switch_off_by_default():
    assert ee.external_engines_enabled() is False
    config = ee.load_engine_config("a11y")
    assert config.enabled is False
    assert config.command == ()


def test_disabled_engine_takes_clean_unavailable_path():
    ee.set_external_engines_enabled(True)
    config = ee.load_engine_config("a11y")  # still per-engine disabled
    result = ee.run_request(config, ee.JsonlRequest("ping"))
    assert result.ok is False
    assert result.unavailable is True
    assert "off by default" in result.error


def test_master_off_blocks_even_enabled_engine():
    ee.save_engine_config(ee.EngineConfig("a11y", command=("node", "x.js"), enabled=True))
    config = ee.load_engine_config("a11y")
    status = ee.probe_engine(config, master_enabled=False)
    assert status.available is False
    assert "turned off" in status.reason


def test_missing_executable_is_unavailable():
    ee.set_external_engines_enabled(True)
    config = ee.set_engine_enabled("a11y", True)
    config = ee.EngineConfig("a11y", command=("definitely-not-a-real-prog",), enabled=True)
    ee.save_engine_config(config)
    result = ee.run_request(
        ee.load_engine_config("a11y"),
        ee.JsonlRequest("ping"),
        which=lambda name: None,
    )
    assert result.unavailable is True
    assert "not found" in result.error


def test_successful_round_trip_with_injected_runner():
    ee.set_external_engines_enabled(True)
    ee.save_engine_config(ee.EngineConfig("a11y", command=("node", "engine.js"), enabled=True))
    config = ee.load_engine_config("a11y")
    result = ee.run_request(
        config,
        ee.JsonlRequest("audit", {"text": "hi"}),
        which=lambda name: "/usr/bin/node",
        runner=_echo_runner({"result": "ok"}),
    )
    assert result.ok is True
    assert result.response["result"] == "ok"
    assert result.response["echo"] == {"method": "audit", "params": {"text": "hi"}}


def test_engine_error_field_surfaces():
    ee.set_external_engines_enabled(True)
    ee.save_engine_config(ee.EngineConfig("a11y", command=("node", "x.js"), enabled=True))

    def runner(command, stdin_text, timeout):
        return 0, json.dumps({"error": "bad input"}) + "\n", ""

    result = ee.run_request(
        ee.load_engine_config("a11y"),
        ee.JsonlRequest("audit"),
        which=lambda name: "/usr/bin/node",
        runner=runner,
    )
    assert result.ok is False
    assert result.error == "bad input"


def test_nonzero_exit_reports_stderr():
    ee.set_external_engines_enabled(True)
    ee.save_engine_config(ee.EngineConfig("a11y", command=("node", "x.js"), enabled=True))

    def runner(command, stdin_text, timeout):
        return 2, "", "boom"

    result = ee.run_request(
        ee.load_engine_config("a11y"),
        ee.JsonlRequest("audit"),
        which=lambda name: "/usr/bin/node",
        runner=runner,
    )
    assert result.ok is False
    assert "boom" in result.error


def test_invalid_json_is_reported():
    ee.set_external_engines_enabled(True)
    ee.save_engine_config(ee.EngineConfig("a11y", command=("node", "x.js"), enabled=True))

    def runner(command, stdin_text, timeout):
        return 0, "not json\n", ""

    result = ee.run_request(
        ee.load_engine_config("a11y"),
        ee.JsonlRequest("audit"),
        which=lambda name: "/usr/bin/node",
        runner=runner,
    )
    assert result.ok is False
    assert "invalid JSON" in result.error


def test_timeout_is_reported():
    ee.set_external_engines_enabled(True)
    ee.save_engine_config(ee.EngineConfig("a11y", command=("node", "x.js"), enabled=True))

    def runner(command, stdin_text, timeout):
        raise subprocess.TimeoutExpired(cmd=command, timeout=timeout)

    result = ee.run_request(
        ee.load_engine_config("a11y"),
        ee.JsonlRequest("audit"),
        which=lambda name: "/usr/bin/node",
        runner=runner,
    )
    assert result.ok is False
    assert "timed out" in result.error


def test_config_persists_round_trip():
    ee.set_external_engines_enabled(True)
    ee.save_engine_config(
        ee.EngineConfig("a11y", command=("node", "a.js"), enabled=True, description="A11y backend")
    )
    reloaded = ee.load_engine_config("a11y")
    assert reloaded.command == ("node", "a.js")
    assert reloaded.enabled is True
    assert reloaded.description == "A11y backend"
    assert ee.external_engines_enabled() is True
