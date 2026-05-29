from __future__ import annotations

from quill.core.diffing import build_unified_diff


def test_build_unified_diff_returns_patch_text() -> None:
    diff_text = build_unified_diff("line one\nline two\n", "line one\nline 2\n")
    assert "--- Other file" in diff_text
    assert "+++ Current document" in diff_text
    assert "-line 2" in diff_text
    assert "+line two" in diff_text


def test_build_unified_diff_returns_empty_when_identical() -> None:
    assert build_unified_diff("same\n", "same\n") == ""
