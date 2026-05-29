from __future__ import annotations


class LocationRing:
    def __init__(self, max_entries: int = 200) -> None:
        self._max_entries = max_entries
        self._entries: list[int] = []
        self._cursor = -1

    def record(self, position: int) -> None:
        if self._entries and self._entries[self._cursor] == position:
            return
        if self._cursor < len(self._entries) - 1:
            self._entries = self._entries[: self._cursor + 1]
        self._entries.append(position)
        if len(self._entries) > self._max_entries:
            overflow = len(self._entries) - self._max_entries
            self._entries = self._entries[overflow:]
        self._cursor = len(self._entries) - 1

    def back(self, current_position: int) -> int | None:
        if not self._entries:
            self.record(current_position)
        elif self._entries[self._cursor] != current_position:
            self.record(current_position)
        if self._cursor <= 0:
            return None
        self._cursor -= 1
        return self._entries[self._cursor]

    def forward(self, current_position: int) -> int | None:
        if not self._entries:
            self.record(current_position)
            return None
        if self._entries[self._cursor] != current_position:
            self.record(current_position)
            return None
        if self._cursor >= len(self._entries) - 1:
            return None
        self._cursor += 1
        return self._entries[self._cursor]
