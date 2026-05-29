from __future__ import annotations

from quill.platform.windows.shell_integration import (
    APPLICATION_KEY,
    PROGID_HTML,
    PROGID_MARKUP,
    PROGID_TEXT,
    build_shell_integration_plan,
)


def test_build_shell_integration_plan_includes_progids() -> None:
    plan = build_shell_integration_plan('"python.exe" -m quill "%1"')
    paths = {entry.path for entry in plan}

    assert APPLICATION_KEY in paths
    assert rf"{APPLICATION_KEY}\shell\open\command" in paths
    assert rf"{APPLICATION_KEY}\SupportedTypes" in paths
    assert rf"Software\Classes\{PROGID_TEXT}" in paths
    assert rf"Software\Classes\{PROGID_MARKUP}" in paths
    assert rf"Software\Classes\{PROGID_HTML}" in paths


def test_build_shell_integration_plan_includes_extension_open_with_entries() -> None:
    plan = build_shell_integration_plan('"python.exe" -m quill "%1"')
    open_with_paths = [entry.path for entry in plan if entry.path.endswith(r"OpenWithProgids")]

    assert open_with_paths
