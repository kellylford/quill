from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentStats:
    characters: int
    words: int
    lines: int


def compute_document_stats(text: str) -> DocumentStats:
    words = [token for token in text.split() if token]
    lines = 0 if text == "" else text.count("\n") + 1
    return DocumentStats(
        characters=len(text),
        words=len(words),
        lines=lines,
    )
