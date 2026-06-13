"""Accessibility PR gate (GATE-7) — announcement-grammar conformance.

These checks run on every pull request alongside the keyboard-trap, focus-order,
and screen-reader announcement suites. They assert that the shared announcement
grammar (A11Y-1) stays well-formed so screen-reader users always hear a
predictable outcome sentence.
"""

from __future__ import annotations

import pytest

from quill.core.announcements import format_announcement, format_progress


def _is_well_formed(sentence: str) -> bool:
    return bool(sentence) and sentence[0].isupper() and sentence.endswith((".", "!", "?"))


@pytest.mark.parametrize(
    "verb,obj,count",
    [
        ("Rewrote", "paragraph", 42),
        ("Summarized", "document", 1200),
        ("Replaced", "selection", 1),
        ("Saved", "document", None),
        ("Copied", None, None),
    ],
)
def test_outcome_announcements_are_well_formed(
    verb: str, obj: str | None, count: int | None
) -> None:
    sentence = format_announcement(verb, obj, count=count)
    assert _is_well_formed(sentence), sentence


def test_progress_announcements_are_well_formed() -> None:
    assert _is_well_formed(format_progress("Rewriting", "paragraph", count=42))


def test_key_phrases_match_the_published_grammar() -> None:
    # These exact phrases appear in docs/QUILL-PRD.md
    # and must keep rendering identically.
    assert format_announcement("Rewrote", "paragraph", count=42) == "Rewrote paragraph, 42 words."
    assert (
        format_announcement("Summarized", "document", count=1200)
        == "Summarized document, 1,200 words."
    )
    assert format_announcement("Saved", "document") == "Saved document."
