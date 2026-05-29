import pytest

from quill.core.search import SearchOptions, SearchPatternError, find_matches, replace_all


def test_find_matches_case_insensitive_by_default() -> None:
    matches = find_matches("Hello HELLO", "hello")
    assert matches == [(0, 5), (6, 11)]


def test_find_matches_whole_word() -> None:
    options = SearchOptions(whole_word=True)
    matches = find_matches("cat catalog cat", "cat", options)
    assert matches == [(0, 3), (12, 15)]


def test_find_matches_wildcard() -> None:
    options = SearchOptions(wildcard=True)
    matches = find_matches("file-1 file-22 file-abc", "file-*", options)
    assert matches == [(0, 5), (7, 12), (15, 20)]


def test_find_matches_reports_regex_errors() -> None:
    options = SearchOptions(use_regex=True)
    with pytest.raises(SearchPatternError) as error:
        find_matches("abc", "(abc", options)
    assert "closing parenthesis" in str(error.value)


def test_replace_all_returns_updated_text_and_count() -> None:
    updated, count = replace_all("red blue red", "red", "green")
    assert updated == "green blue green"
    assert count == 2
