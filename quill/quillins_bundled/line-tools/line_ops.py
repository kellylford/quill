"""Cursor-aware line operations vendored into the Line Tools Quillin.

These pure text transforms were previously ``quill/core/line_ops.py``. Vendored
here so the feature is entirely self-contained in the sandboxed worker. Each
function takes the full document text and an integer cursor offset, and returns
a ``(new_text, new_cursor)`` tuple so the extension can apply the operation as a
single undoable edit followed by a cursor reposition.
"""

from __future__ import annotations

__all__ = [
    "duplicate_line",
    "delete_line",
    "move_line_up",
    "move_line_down",
    "join_paragraph",
    "join_with_next_line",
]


def duplicate_line(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    lines.insert(index + 1, lines[index])
    updated = "\n".join(lines)
    return updated, _line_start(updated, index + 1)


def delete_line(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    if len(lines) == 1:
        return "", 0
    del lines[index]
    if index >= len(lines):
        index = len(lines) - 1
    updated = "\n".join(lines)
    return updated, _line_start(updated, index)


def move_line_up(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    if index == 0:
        return text, cursor
    lines[index - 1], lines[index] = lines[index], lines[index - 1]
    updated = "\n".join(lines)
    return updated, _line_start(updated, index - 1)


def move_line_down(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    if index >= len(lines) - 1:
        return text, cursor
    lines[index], lines[index + 1] = lines[index + 1], lines[index]
    updated = "\n".join(lines)
    return updated, _line_start(updated, index + 1)


def join_paragraph(text: str, cursor: int) -> tuple[str, int]:
    """Join the paragraph containing the cursor into a single line.

    A paragraph is a run of consecutive non-blank lines. A blank line is a
    no-op. A single-line paragraph is also a no-op.
    """
    lines = _lines(text)
    index = _line_index(text, cursor)
    if lines[index].strip() == "":
        return text, cursor
    first = index
    last = index
    while last < len(lines) - 1 and lines[last + 1].strip() != "":
        last += 1
    if first == last:
        return text, cursor
    joined = " ".join(part.strip() for part in lines[first:last + 1])
    new_lines = lines[:first] + [joined] + lines[last + 1:]
    updated = "\n".join(new_lines)
    return updated, _line_start(updated, first)


def join_with_next_line(text: str, cursor: int) -> tuple[str, int]:
    """Join the cursor's line with the line immediately below it."""
    lines = _lines(text)
    index = _line_index(text, cursor)
    if index >= len(lines) - 1:
        return text, cursor
    lines[index] = f"{lines[index].rstrip()} {lines[index + 1].lstrip()}".rstrip()
    del lines[index + 1]
    updated = "\n".join(lines)
    return updated, _line_start(updated, index)


# -- private helpers ----------------------------------------------------------

def _lines(text: str) -> list[str]:
    if text == "":
        return [""]
    return text.split("\n")


def _line_index(text: str, cursor: int) -> int:
    if cursor <= 0:
        return 0
    return text[:cursor].count("\n")


def _line_start(text: str, index: int) -> int:
    if index <= 0:
        return 0
    position = 0
    current = 0
    while current < index and position < len(text):
        if text[position] == "\n":
            current += 1
        position += 1
    return position
