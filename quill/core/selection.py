from __future__ import annotations

import re


def word_span(text: str, cursor: int) -> tuple[int, int]:
    position = max(0, min(cursor, len(text)))
    length = len(text)
    if not text:
        return 0, 0
    word_char = re.compile(r"\w")
    on_word = position < length and bool(word_char.match(text[position]))
    after_word = position > 0 and bool(word_char.match(text[position - 1]))
    if not on_word and not after_word:
        # Whitespace or boundary: select the single character under the cursor so
        # expansion still has a sensible innermost step.
        if position < length:
            return position, position + 1
        if position > 0:
            return position - 1, position
        return position, position
    anchor = position if on_word else position - 1
    start = anchor
    while start > 0 and word_char.match(text[start - 1]):
        start -= 1
    end = anchor
    while end < length and word_char.match(text[end]):
        end += 1
    return start, end


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


def sentence_span(text: str, cursor: int) -> tuple[int, int]:
    position = max(0, min(cursor, len(text)))
    if not text:
        return 0, 0

    start = 0
    for match in re.finditer(r"[.!?](?:[\]\)\"']+)?\s+", text):
        boundary = match.end()
        if boundary > position:
            break
        start = boundary

    end = len(text)
    for match in re.finditer(r"[.!?](?:[\]\)\"']+)?\s+", text[position:]):
        end = position + match.end()
        break

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


# Ordered innermost-to-outermost structural levels used by expand_selection.
# Each entry pairs a scope label with the span function that computes it.
_EXPANSION_LEVELS: tuple[tuple[str, object], ...] = (
    ("word", word_span),
    ("line", line_span),
    ("sentence", sentence_span),
    ("paragraph", paragraph_span),
    ("block", block_span),
)


def expand_selection(text: str, start: int, end: int) -> tuple[int, int, str] | None:
    """Return the next-larger structural span enclosing the current selection.

    Walks word -> line -> sentence -> paragraph -> block -> document and returns
    the first level whose span strictly contains the current ``(start, end)``
    selection, as ``(new_start, new_end, scope_label)``. Returns ``None`` when the
    selection already spans the whole document.
    """
    length = len(text)
    start = max(0, min(start, length))
    end = max(0, min(end, length))
    if start > end:
        start, end = end, start
    cursor = start
    for label, span_fn in _EXPANSION_LEVELS:
        span_start, span_end = span_fn(text, cursor)  # type: ignore[operator]
        if span_start <= start and span_end >= end and (span_end - span_start) > (end - start):
            return span_start, span_end, label
    if start > 0 or end < length:
        return 0, length, "document"
    return None
