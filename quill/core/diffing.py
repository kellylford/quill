from __future__ import annotations

from difflib import unified_diff


def build_unified_diff(
    current_text: str,
    other_text: str,
    current_label: str = "Current document",
    other_label: str = "Other file",
) -> str:
    current_lines = current_text.splitlines(keepends=True)
    other_lines = other_text.splitlines(keepends=True)
    diff_lines = list(
        unified_diff(
            other_lines,
            current_lines,
            fromfile=other_label,
            tofile=current_label,
            lineterm="",
            n=3,
        )
    )
    if not diff_lines:
        return ""
    return "\n".join(diff_lines) + "\n"
