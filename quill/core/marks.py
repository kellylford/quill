from __future__ import annotations


class MarkRing:
    def __init__(self, max_size: int = 20) -> None:
        self._max_size = max_size
        self._marks: list[int] = []

    def set_mark(self, position: int) -> None:
        normalized = max(0, position)
        if self._marks and self._marks[-1] == normalized:
            return
        if normalized in self._marks:
            self._marks.remove(normalized)
        self._marks.append(normalized)
        if len(self._marks) > self._max_size:
            self._marks = self._marks[-self._max_size :]

    def pop_mark(self) -> int | None:
        if not self._marks:
            return None
        return self._marks.pop()

    def exchange_point_and_mark(self, position: int) -> int | None:
        if not self._marks:
            return None
        current = max(0, position)
        mark = self._marks[-1]
        self._marks[-1] = current
        return mark

    def list_marks(self) -> tuple[int, ...]:
        return tuple(self._marks)


def line_column_for_position(text: str, position: int) -> tuple[int, int]:
    capped = max(0, min(position, len(text)))
    line = text.count("\n", 0, capped) + 1
    line_start = text.rfind("\n", 0, capped) + 1
    column = capped - line_start + 1
    return line, column
