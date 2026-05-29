from __future__ import annotations

from quill.core.outline import extract_outline_entries

_OPEN_TO_CLOSE = {"(": ")", "[": "]", "{": "}"}
_CLOSE_TO_OPEN = {value: key for key, value in _OPEN_TO_CLOSE.items()}


def find_matching_bracket(text: str, cursor: int) -> int | None:
    if not text:
        return None
    candidate_positions = [cursor]
    if cursor > 0:
        candidate_positions.append(cursor - 1)
    for position in candidate_positions:
        if position < 0 or position >= len(text):
            continue
        char = text[position]
        if char in _OPEN_TO_CLOSE:
            return _scan_forward(text, position, char, _OPEN_TO_CLOSE[char])
        if char in _CLOSE_TO_OPEN:
            return _scan_backward(text, position, _CLOSE_TO_OPEN[char], char)
    return None


def next_structure_position(text: str, cursor: int, markup_kind: str) -> int | None:
    markers = _structure_markers(text, markup_kind)
    for marker in markers:
        if marker > cursor:
            return marker
    return None


def previous_structure_position(text: str, cursor: int, markup_kind: str) -> int | None:
    markers = _structure_markers(text, markup_kind)
    for marker in reversed(markers):
        if marker < cursor:
            return marker
    return None


def _structure_markers(text: str, markup_kind: str) -> list[int]:
    markers = {entry.position for entry in extract_outline_entries(text, markup_kind)}
    markers.update(index for index, char in enumerate(text) if char in "()[]{}")
    return sorted(markers)


def _scan_forward(text: str, start: int, opening: str, closing: str) -> int | None:
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index
    return None


def _scan_backward(text: str, start: int, opening: str, closing: str) -> int | None:
    depth = 0
    for index in range(start, -1, -1):
        char = text[index]
        if char == closing:
            depth += 1
        elif char == opening:
            depth -= 1
            if depth == 0:
                return index
    return None
