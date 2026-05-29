from __future__ import annotations


def line_span(text: str, cursor: int) -> tuple[int, int]:
    position = max(0, min(cursor, len(text)))
    start = text.rfind("\n", 0, position) + 1
    end = text.find("\n", position)
    if end == -1:
        end = len(text)
    return start, end


def paragraph_span(text: str, cursor: int) -> tuple[int, int]:
    position = max(0, min(cursor, len(text)))
    if not text:
        return 0, 0

    previous_break = text.rfind("\n\n", 0, position)
    start = previous_break + 2 if previous_break >= 0 else 0

    next_break = text.find("\n\n", position)
    end = next_break if next_break >= 0 else len(text)
    return start, end


def block_span(text: str, cursor: int) -> tuple[int, int]:
    position = max(0, min(cursor, len(text)))
    if not text:
        return 0, 0

    start = text.rfind("\n", 0, position) + 1
    end = text.find("\n", position)
    if end == -1:
        end = len(text)

    while start > 0:
        previous_break = text.rfind("\n", 0, start - 1)
        previous_line_start = previous_break + 1
        previous_line = text[previous_line_start : start - 1]
        if not previous_line.strip():
            break
        start = previous_line_start

    text_length = len(text)
    while end < text_length:
        next_break = text.find("\n", end + 1)
        if next_break == -1:
            next_break = text_length
        next_line_start = end + 1
        next_line = text[next_line_start:next_break]
        if not next_line.strip():
            break
        end = next_break

    return start, end
