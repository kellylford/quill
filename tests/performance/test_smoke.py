from __future__ import annotations

from time import perf_counter

from quill.core.line_ops import move_line_down
from quill.core.search import find_matches, replace_all


def test_find_matches_large_document_smoke() -> None:
    text = ("alpha beta gamma delta\n" * 20000) + "needle\n" + ("alpha\n" * 20000)
    start = perf_counter()
    matches = find_matches(text, "needle")
    elapsed = perf_counter() - start
    assert matches
    assert elapsed < 0.5


def test_replace_all_large_document_smoke() -> None:
    text = "foo bar baz\n" * 30000
    start = perf_counter()
    updated, count = replace_all(text, "foo", "qux")
    elapsed = perf_counter() - start
    assert count == 30000
    assert updated.startswith("qux")
    assert elapsed < 0.8


def test_line_move_large_document_smoke() -> None:
    lines = [f"line-{index}" for index in range(40000)]
    text = "\n".join(lines)
    cursor = len("line-0\nline-1\n")
    start = perf_counter()
    updated, new_cursor = move_line_down(text, cursor)
    elapsed = perf_counter() - start
    assert "line-1\nline-3\nline-2" in updated
    assert new_cursor > cursor
    assert elapsed < 0.8
