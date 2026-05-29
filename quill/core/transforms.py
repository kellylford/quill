from __future__ import annotations

import re


def to_upper(text: str) -> str:
    return text.upper()


def to_lower(text: str) -> str:
    return text.lower()


def to_title(text: str) -> str:
    return text.title()


def to_toggle_case(text: str) -> str:
    return text.swapcase()


def to_sentence_case(text: str) -> str:
    lowered = text.lower()
    if not lowered:
        return lowered

    pieces = re.split(r"([.!?]\s+)", lowered)
    transformed: list[str] = []
    for piece in pieces:
        if not piece:
            continue
        if re.fullmatch(r"[.!?]\s+", piece):
            transformed.append(piece)
            continue
        transformed.append(_capitalize_first_alpha(piece))
    return "".join(transformed)


def _capitalize_first_alpha(text: str) -> str:
    for index, char in enumerate(text):
        if char.isalpha():
            return text[:index] + char.upper() + text[index + 1 :]
    return text
