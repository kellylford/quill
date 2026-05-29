from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.search_history import add_search_term, load_search_history


def test_add_search_term_prepends_and_dedupes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    add_search_term("alpha")
    add_search_term("beta")
    terms = add_search_term("alpha")
    assert terms == ["alpha", "beta"]


def test_add_search_term_honors_limit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    for index in range(5):
        add_search_term(f"term-{index}", limit=3)
    assert load_search_history() == ["term-4", "term-3", "term-2"]
