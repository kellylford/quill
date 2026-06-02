"""Consented, off-by-default boundary to external engines over stdio (AI-24).

QUILL is a Python app, but some capabilities are best served by an engine
written in another language (for example a Node accessibility backend). Rather
than embedding a foreign runtime, QUILL drives such an engine as a *local
subprocess* that speaks one JSON object per line (JSONL) on stdin/stdout. This
module defines that single boundary once so every future integration reuses it.

Design guarantees:

* **Off by default.** Nothing spawns until the user both turns on external
  engines (a master consent switch) and enables the specific engine.
* **Spawned on demand.** A process is created per request and torn down; there
  is no long-lived daemon holding state.
* **Clean unavailable path.** When an engine is disabled, unconfigured, or its
  executable is missing, callers get a structured ``EngineResult`` with
  ``unavailable=True`` and a human reason — never an exception to handle.
* **Local, not network.** The boundary spawns a local process and exchanges
  JSONL over pipes; it opens no sockets. Any network access an engine performs
  is the engine's own concern and is outside QUILL's GATE-9 egress surface,
  which inventories QUILL's own ``urlopen``/``urlretrieve`` calls.

The module is UI-framework-agnostic (no ``wx`` imports) and strict-typed. The
subprocess runner is injectable so the boundary is fully testable without
spawning real processes.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic

_CONFIG_FILE = "external-engines.json"

# A runner takes (command, stdin_text, timeout_seconds) and returns
# (returncode, stdout_text, stderr_text). Injectable for tests.
Runner = Callable[[list[str], str, float], "tuple[int, str, str]"]


# ---------------------------------------------------------------------------
# Configuration (persisted, off by default)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EngineConfig:
    """How to reach one external engine."""

    engine_id: str
    command: tuple[str, ...] = ()
    enabled: bool = False
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "enabled": self.enabled,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, engine_id: str, data: dict[str, Any]) -> EngineConfig:
        command_raw = data.get("command", [])
        command = tuple(str(part) for part in command_raw) if isinstance(command_raw, list) else ()
        return cls(
            engine_id=engine_id,
            command=command,
            enabled=bool(data.get("enabled", False)),
            description=str(data.get("description", "")),
        )


def _config_path() -> Path:
    return app_data_dir() / "ai" / _CONFIG_FILE


def _load_document() -> dict[str, Any]:
    raw = read_json(_config_path(), default={})
    if not isinstance(raw, dict):
        return {"master_enabled": False, "engines": {}}
    engines = raw.get("engines")
    return {
        "master_enabled": bool(raw.get("master_enabled", False)),
        "engines": engines if isinstance(engines, dict) else {},
    }


def external_engines_enabled() -> bool:
    """The master consent switch for external engines (default off)."""

    return bool(_load_document()["master_enabled"])


def set_external_engines_enabled(enabled: bool) -> None:
    document = _load_document()
    document["master_enabled"] = bool(enabled)
    write_json_atomic(_config_path(), document)


def load_engine_config(engine_id: str) -> EngineConfig:
    """Load one engine's config, or an empty disabled config if unset."""

    engines = _load_document()["engines"]
    data = engines.get(engine_id)
    if isinstance(data, dict):
        return EngineConfig.from_dict(engine_id, data)
    return EngineConfig(engine_id=engine_id)


def save_engine_config(config: EngineConfig) -> None:
    document = _load_document()
    engines = dict(document["engines"])
    engines[config.engine_id] = config.to_dict()
    document["engines"] = engines
    write_json_atomic(_config_path(), document)


def set_engine_enabled(engine_id: str, enabled: bool) -> EngineConfig:
    config = load_engine_config(engine_id)
    updated = EngineConfig(
        engine_id=config.engine_id,
        command=config.command,
        enabled=bool(enabled),
        description=config.description,
    )
    save_engine_config(updated)
    return updated


# ---------------------------------------------------------------------------
# Availability probing and the clean unavailable path
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EngineStatus:
    engine_id: str
    available: bool
    reason: str


def probe_engine(
    config: EngineConfig,
    *,
    master_enabled: bool | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> EngineStatus:
    """Decide whether an engine can run right now, with a human reason."""

    master = external_engines_enabled() if master_enabled is None else master_enabled
    if not master:
        return EngineStatus(
            config.engine_id,
            False,
            "External engines are turned off. Enable them in Settings to use this feature.",
        )
    if not config.enabled:
        return EngineStatus(
            config.engine_id,
            False,
            f"The {config.engine_id} engine is off by default. Enable it in Settings.",
        )
    if not config.command:
        return EngineStatus(
            config.engine_id, False, f"No command is configured for the {config.engine_id} engine."
        )
    executable = config.command[0]
    if which(executable) is None and not Path(executable).exists():
        return EngineStatus(
            config.engine_id, False, f"The program '{executable}' was not found on this computer."
        )
    return EngineStatus(config.engine_id, True, "Ready.")


# ---------------------------------------------------------------------------
# JSONL request / response
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class JsonlRequest:
    method: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_line(self) -> str:
        return json.dumps({"method": self.method, "params": self.params}, ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class EngineResult:
    ok: bool
    response: dict[str, Any] | None = None
    error: str | None = None
    unavailable: bool = False


def _default_runner(command: list[str], stdin_text: str, timeout: float) -> tuple[int, str, str]:
    completed = subprocess.run(  # noqa: S603 - command is user-consented and configured
        command,
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def run_request(
    config: EngineConfig,
    request: JsonlRequest,
    *,
    master_enabled: bool | None = None,
    which: Callable[[str], str | None] = shutil.which,
    runner: Runner = _default_runner,
    timeout: float = 30.0,
) -> EngineResult:
    """Drive an engine for a single request, returning a structured result.

    Never raises for the ordinary failure modes (disabled, missing program,
    bad JSON, non-zero exit, timeout); each maps to a clean ``EngineResult``.
    """

    status = probe_engine(config, master_enabled=master_enabled, which=which)
    if not status.available:
        return EngineResult(ok=False, error=status.reason, unavailable=True)

    try:
        returncode, stdout, stderr = runner(list(config.command), request.to_line() + "\n", timeout)
    except subprocess.TimeoutExpired:
        return EngineResult(ok=False, error=f"The {config.engine_id} engine timed out.")
    except OSError as error:
        return EngineResult(
            ok=False, error=f"Could not start the {config.engine_id} engine: {error}"
        )

    if returncode != 0:
        detail = stderr.strip() or f"exit code {returncode}"
        return EngineResult(ok=False, error=f"The {config.engine_id} engine failed: {detail}")

    line = stdout.strip().splitlines()[0] if stdout.strip() else ""
    if not line:
        return EngineResult(ok=False, error=f"The {config.engine_id} engine returned no output.")
    try:
        parsed = json.loads(line)
    except json.JSONDecodeError as error:
        return EngineResult(
            ok=False, error=f"The {config.engine_id} engine sent invalid JSON: {error}"
        )
    if not isinstance(parsed, dict):
        return EngineResult(ok=False, error="The engine response was not a JSON object.")
    if parsed.get("error"):
        return EngineResult(ok=False, error=str(parsed["error"]), response=parsed)
    return EngineResult(ok=True, response=parsed)
