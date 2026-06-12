"""Gate: every command in COMMAND_FEATURE_MAP references a defined feature."""

from __future__ import annotations

from quill.core.feature_command_map import COMMAND_FEATURE_MAP
from quill.core.features import FEATURE_DEFINITIONS
from quill.tools.check_feature_tags import run as run_gate


def test_gate_passes() -> None:
    assert run_gate() == 0, (
        "check_feature_tags gate failed — a command references an undefined feature"
    )


def test_no_undefined_features() -> None:
    undefined = {
        cmd: fid for cmd, fid in COMMAND_FEATURE_MAP.items() if fid not in FEATURE_DEFINITIONS
    }
    assert not undefined, f"Commands reference undefined features: {undefined}"


def test_command_map_not_empty() -> None:
    assert len(COMMAND_FEATURE_MAP) > 50, "COMMAND_FEATURE_MAP looks unexpectedly small"


def test_all_feature_ids_are_strings() -> None:
    for cmd, fid in COMMAND_FEATURE_MAP.items():
        assert isinstance(fid, str) and fid, f"Command {cmd!r} has empty or non-string feature ID"
