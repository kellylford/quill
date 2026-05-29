from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.spellcheck import (
    add_word_to_scope,
    list_misspellings,
    load_combined_dictionary,
    misspelling_at_position,
    next_misspelling,
    suggest_words,
)


def test_list_misspellings_detects_unknown_word() -> None:
    misspellings = list_misspellings("the qwertyword appears", set())
    assert [item.word for item in misspellings] == ["qwertyword"]


def test_next_misspelling_returns_next_after_cursor() -> None:
    text = "the alpha qwertyword beta"
    misspelling = next_misspelling(text, text.index("alpha"), {"beta"})
    assert misspelling is not None
    assert misspelling.word == "qwertyword"


def test_add_word_to_scope_updates_combined_dictionary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    doc = tmp_path / "note.md"
    doc.write_text("x", encoding="utf-8")
    add_word_to_scope("qwertyword", "personal", doc, tmp_path)
    add_word_to_scope("docword", "document", doc, tmp_path)
    add_word_to_scope("projword", "project", doc, tmp_path)
    combined = load_combined_dictionary(doc, tmp_path)
    assert {"qwertyword", "docword", "projword"}.issubset(combined)


def test_suggest_words_returns_close_matches() -> None:
    suggestions = suggest_words("navigtion", {"navigation", "navigator"})
    assert "navigation" in suggestions


def test_misspelling_at_position_returns_item() -> None:
    text = "the qwertyword appears"
    item = misspelling_at_position(text, text.index("qwertyword"), set())
    assert item is not None
    assert item.word == "qwertyword"


def test_misspelling_at_position_returns_none_on_known_word() -> None:
    text = "alpha bravo charlie"
    item = misspelling_at_position(text, 0, {"alpha", "bravo", "charlie"})
    assert item is None


def test_misspelling_at_position_handles_caret_between_words() -> None:
    # Caret sits on the space between words; no match should be returned.
    text = "alpha bravo"
    item = misspelling_at_position(text, text.index(" "), set())
    assert item is None


def test_next_misspelling_scans_only_after_cursor() -> None:
    # Earlier unknown words should not be returned when the cursor is past
    # them. This guards the short-circuit optimization.
    text = "earlyunknown midword anotherbad"
    item = next_misspelling(text, text.index("midword"), {"midword"})
    assert item is not None
    assert item.word == "anotherbad"
