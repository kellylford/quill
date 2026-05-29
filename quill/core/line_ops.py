from __future__ import annotations


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


def join_with_next_line(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    if index >= len(lines) - 1:
        return text, cursor
    lines[index] = f"{lines[index].rstrip()} {lines[index + 1].lstrip()}".rstrip()
    del lines[index + 1]
    updated = "\n".join(lines)
    return updated, _line_start(updated, index)


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
