from __future__ import annotations

import re


def page_starts(text: str) -> list[int]:
    starts = [0]
    for index, char in enumerate(text):
        if char == "\f":
            starts.append(index + 1)
    return starts


def page_start_for_number(text: str, page_number: int) -> int | None:
    starts = page_starts(text)
    if page_number < 1 or page_number > len(starts):
        return None
    return starts[page_number - 1]


def parse_line_column(value: str) -> tuple[int, int | None]:
    raw = value.strip()
    if not raw:
        raise ValueError("Line number is required")
    if "," not in raw:
        return int(raw), None
    line_raw, column_raw = (part.strip() for part in raw.split(",", 1))
    if not line_raw or not column_raw:
        raise ValueError("Line and column are required")
    return int(line_raw), int(column_raw)


def next_heading_start(text: str, cursor: int, markup_kind: str) -> int | None:
    starts = _heading_starts(text, markup_kind)
    for start in starts:
        if start > cursor:
            return start
    return None


def previous_heading_start(text: str, cursor: int, markup_kind: str) -> int | None:
    starts = _heading_starts(text, markup_kind)
    previous: int | None = None
    for start in starts:
        if start >= cursor:
            break
        previous = start
    return previous


def next_block_start(text: str, cursor: int) -> int | None:
    blocks = _block_starts(text)
    for start in blocks:
        if start > cursor:
            return start
    return None


def previous_block_start(text: str, cursor: int) -> int | None:
    blocks = _block_starts(text)
    previous: int | None = None
    for start in blocks:
        if start >= cursor:
            break
        previous = start
    return previous


def _heading_starts(text: str, markup_kind: str) -> list[int]:
    if markup_kind == "markdown":
        pattern = re.compile(r"^[ \t]{0,3}#{1,6}\s+\S", re.MULTILINE)
    elif markup_kind == "html":
        pattern = re.compile(r"^[ \t]*<h[1-6]\b[^>]*>", re.MULTILINE | re.IGNORECASE)
    else:
        return []
    return [match.start() for match in pattern.finditer(text)]


def _block_starts(text: str) -> list[int]:
    starts: list[int] = []
    lines = text.splitlines(keepends=True)
    if not lines:
        return starts
    offset = 0
    in_block = False
    for line in lines:
        if line.strip():
            if not in_block:
                starts.append(offset)
                in_block = True
        else:
            in_block = False
        offset += len(line)
    return starts
