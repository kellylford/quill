from __future__ import annotations

import pytest

from quill.core import thesaurus


@pytest.mark.skipif(
    not thesaurus.is_available(),
    reason="Thesaurus data file not installed; skipping content-dependent tests.",
)
class TestThesaurusContent:
    def test_lookup_returns_entry_for_common_word(self) -> None:
        entry = thesaurus.lookup("happy")
        assert entry is not None
        assert entry.word == "happy"
        assert len(entry.meanings) >= 1
        assert any("cheerful" in m.synonyms or "glad" in m.synonyms for m in entry.meanings)

    def test_lookup_is_case_insensitive(self) -> None:
        assert thesaurus.lookup("Happy") is not None
        assert thesaurus.lookup("HAPPY") is not None

    def test_lookup_unknown_word_returns_none(self) -> None:
        assert thesaurus.lookup("qwertyzzzword") is None

    def test_meanings_carry_part_of_speech(self) -> None:
        entry = thesaurus.lookup("write")
        assert entry is not None
        pos_set = {m.part_of_speech for m in entry.meanings}
        assert "verb" in pos_set

    def test_all_synonyms_deduplicates(self) -> None:
        entry = thesaurus.lookup("happy")
        assert entry is not None
        synonyms = entry.all_synonyms
        assert len(synonyms) == len({s.lower() for s in synonyms})


def test_word_at_returns_word_under_cursor() -> None:
    result = thesaurus.word_at("Hello there friend", 8)
    assert result == ("there", 6, 11)


def test_word_at_handles_cursor_after_word() -> None:
    text = "Hello"
    # Cursor sits immediately after the word.
    result = thesaurus.word_at(text, len(text))
    assert result is not None
    assert result[0] == "Hello"


def test_word_at_returns_none_outside_word() -> None:
    assert thesaurus.word_at("  ", 0) is None
    assert thesaurus.word_at("", 0) is None


def test_data_path_is_inside_package() -> None:
    path = thesaurus.data_path()
    assert path.name == "th_en_US_v2.dat"
    assert path.parent.name == "data"
