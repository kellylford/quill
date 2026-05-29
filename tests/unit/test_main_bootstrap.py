from __future__ import annotations

from pathlib import Path

from quill.__main__ import _launch_arguments


def test_launch_arguments_parse_safe_mode_and_paths(tmp_path: Path) -> None:
    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello", encoding="utf-8")

    paths, safe_mode, reset_profile = _launch_arguments(
        ["--safe-mode", str(file_path), "--ignored"]
    )

    assert safe_mode is True
    assert reset_profile is False
    assert paths == [file_path.resolve()]


def test_launch_arguments_parse_reset_profile() -> None:
    paths, safe_mode, reset_profile = _launch_arguments(["--reset-profile"])

    assert paths == []
    assert safe_mode is False
    assert reset_profile is True
