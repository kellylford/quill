"""Pure text algorithms vendored into the Text Tools Quillin.

These functions were previously ``quill/core/line_ops.number_lines``,
``quill/core/wrap_ops``, ``quill/core/regex_ops``, and ``quill/core/set_ops``.
Per the Quillin conversion roadmap (``docs/quillins.md`` §5,
"thin core, fat Quillin"), the algorithm lives *inside* the Quillin that uses it
so the feature is self-contained and runs in the sandboxed worker, which can only
import modules shipped alongside ``extension.py``.

Everything here is dependency-free and ``wx``-free, so the same byte-for-byte
output the core helpers produced is reproduced and unit-testable on its own.
"""

from __future__ import annotations

import re
import textwrap

__all__ = [
    "RegexError",
    "count_matches",
    "cursor_offset_for_line",
    "extract_matches",
    "format_lines",
    "hard_wrap",
    "lines_common_to_both",
    "lines_in_first_not_second",
    "number_lines",
    "widest_line_width",
]


# -- numbering ----------------------------------------------------------------
def number_lines(text: str, start: int = 1, separator: str = ". ") -> str:
    """Prefix each non-blank line with a consecutive number.

    Numbering starts at ``start`` and increments only for non-blank lines; blank
    lines pass through unchanged.
    """

    number = start
    out: list[str] = []
    for line in text.split("\n"):
        if line.strip() == "":
            out.append(line)
        else:
            out.append(f"{number}{separator}{line}")
            number += 1
    return "\n".join(out)


# -- hard wrap ----------------------------------------------------------------
def widest_line_width(text: str) -> int:
    """Return the length of the longest line in ``text`` (0 for empty text)."""

    return max((len(line) for line in text.splitlines()), default=0)


def hard_wrap(text: str, width: int) -> str:
    """Hard-wrap ``text`` so no produced line exceeds ``width`` characters.

    Consecutive non-blank lines are treated as one paragraph and re-flowed; blank
    lines are preserved as paragraph separators. Long unbreakable words are left
    intact rather than split. A non-positive ``width`` returns ``text`` unchanged.
    """

    if width <= 0:
        return text
    out: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if not paragraph:
            return
        joined = " ".join(line.strip() for line in paragraph)
        wrapped = textwrap.fill(
            joined,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        out.extend(wrapped.split("\n"))
        paragraph.clear()

    for line in text.split("\n"):
        if line.strip() == "":
            flush()
            out.append(line)
        else:
            paragraph.append(line)
    flush()
    return "\n".join(out)


# -- regex --------------------------------------------------------------------
class RegexError(ValueError):
    """Raised when a regular expression cannot be compiled."""


def _compile(pattern: str, flags: int) -> re.Pattern[str]:
    try:
        return re.compile(pattern, flags)
    except re.error as exc:
        raise RegexError(f"Invalid regular expression: {exc}") from exc


def count_matches(text: str, pattern: str, *, flags: int = 0) -> int:
    """Return the number of non-overlapping matches of ``pattern`` in ``text``."""

    return sum(1 for _ in _compile(pattern, flags).finditer(text))


def extract_matches(text: str, pattern: str, *, divider: str = "\n", flags: int = 0) -> str:
    """Return all whole matches (group 0) of ``pattern`` joined by ``divider``."""

    matches = [match.group(0) for match in _compile(pattern, flags).finditer(text)]
    return divider.join(matches)


# -- set operations split at the cursor ---------------------------------------
def cursor_offset_for_line(text: str, line: int) -> int:
    """Return the character offset of the start of 1-based ``line`` in ``text``.

    The sandbox exposes the cursor as a line/column address, not a raw offset, so
    this reconstructs the offset the set-operation split needs from the line.
    """

    if line <= 1:
        return 0
    pieces = text.split("\n")
    return sum(len(piece) + 1 for piece in pieces[: line - 1])


def _split_on_cursor(text: str, cursor: int) -> tuple[list[str], list[str]]:
    cursor = max(0, min(cursor, len(text)))
    line_index = text.count("\n", 0, cursor)
    lines = text.split("\n")
    return lines[:line_index], lines[line_index:]


def _key(line: str, case_sensitive: bool) -> str:
    return line if case_sensitive else line.lower()


def lines_in_first_not_second(text: str, cursor: int, *, case_sensitive: bool = True) -> list[str]:
    """Return lines above the cursor that do not appear below it."""

    first, second = _split_on_cursor(text, cursor)
    second_keys = {_key(line, case_sensitive) for line in second}
    seen: set[str] = set()
    result: list[str] = []
    for line in first:
        key = _key(line, case_sensitive)
        if key not in second_keys and key not in seen:
            seen.add(key)
            result.append(line)
    return result


def lines_common_to_both(text: str, cursor: int, *, case_sensitive: bool = True) -> list[str]:
    """Return lines above the cursor that also appear below it."""

    first, second = _split_on_cursor(text, cursor)
    second_keys = {_key(line, case_sensitive) for line in second}
    seen: set[str] = set()
    result: list[str] = []
    for line in first:
        key = _key(line, case_sensitive)
        if key in second_keys and key not in seen:
            seen.add(key)
            result.append(line)
    return result


def format_lines(lines: list[str]) -> str:
    """Join result lines for emitting into a new buffer."""

    return "\n".join(lines)
