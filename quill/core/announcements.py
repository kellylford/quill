"""Shared announcement grammar for screen-reader output (A11Y-1).

Every status/announcement string a user hears should follow one small,
predictable grammar so screen-reader users can parse outcomes at a glance and
across NVDA, JAWS, and Narrator:

    <Verb> <object>[, <count> <unit>(s)][, <detail>].

Examples:
    Rewrote paragraph, 42 words.
    Summarized document, 1,200 words.
    Saved document.
    Nothing to rewrite.

This module is UI-framework agnostic (no ``wx``) so both the editor shell and
tests can build the exact same phrasing. Use :func:`format_announcement` for
outcomes and :func:`format_progress` for the "starting an action" phrasing.

The written grammar lives in ``docs/accessibility/announcement-style-guide.md``;
keep the two in sync.
"""

from __future__ import annotations

__all__ = [
    "format_announcement",
    "format_progress",
    "pluralize",
]


def pluralize(count: int, unit: str) -> str:
    """Return ``"1 word"`` / ``"42 words"`` with a thousands separator.

    Handles the common English sibilant endings (``match`` -> ``matches``) so
    units like ``match`` and ``box`` read correctly.
    """
    if count == 1:
        plural = unit
    elif unit.endswith(("s", "sh", "ch", "x", "z")):
        plural = f"{unit}es"
    else:
        plural = f"{unit}s"
    return f"{count:,} {plural}"


def _capitalize_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def format_announcement(
    verb: str,
    obj: str | None = None,
    *,
    count: int | None = None,
    unit: str = "word",
    detail: str | None = None,
) -> str:
    """Build an outcome announcement following the shared grammar.

    Args:
        verb: The outcome verb, normally past tense (``"Rewrote"``, ``"Saved"``).
        obj: What was acted on (``"paragraph"``, ``"document"``). Optional for
            verb-only outcomes like ``"Copied"``.
        count: Optional quantity (for example a word count).
        unit: The unit for ``count``; pluralized automatically.
        detail: Optional trailing clause, appended as its own comma segment.

    Returns:
        A single sentence ending in a period, with the first letter capitalized.
    """
    head = verb.strip()
    if obj:
        head = f"{head} {obj.strip()}"
    segments = [head]
    if count is not None:
        segments.append(pluralize(count, unit))
    if detail:
        segments.append(detail.strip())
    sentence = ", ".join(segment for segment in segments if segment)
    sentence = _capitalize_first(sentence)
    if not sentence.endswith((".", "!", "?")):
        sentence += "."
    return sentence


def format_progress(
    verb: str,
    obj: str | None = None,
    *,
    count: int | None = None,
    unit: str = "word",
) -> str:
    """Build a "starting an action" announcement (present participle verb).

    Same grammar as :func:`format_announcement`, used when an action begins so
    the user hears the scope before a potentially slow operation runs, e.g.
    ``"Rewriting paragraph, 42 words."``.

    Pure function: no I/O, no logging, no global state, no side effects.
    Same input always produces the same string. Safe to call from any
    thread, including the wx main thread and worker threads.
    """
    return format_announcement(verb, obj, count=count, unit=unit)
