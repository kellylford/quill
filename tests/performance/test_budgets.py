"""PERF-9: enforced performance budgets for the startup-critical paths.

Each test asserts a hard ceiling on an operation that a user feels at launch or
on first interaction: the startup lexical warm-up, the first spell check, the
first thesaurus lookup, and building the Quick Nav landmark index ("prewarm").
The budgets are deliberately generous relative to local timings so they catch
order-of-magnitude regressions on shared CI runners without being flaky. If a
change makes one of these paths materially slower, the budget fails in CI and
the regression is caught before release.

The lexical caches are module-global, so the startup and first-interaction
tests reset them to a cold state to measure the real cost.
"""

from __future__ import annotations

from time import perf_counter

from quill.core import spellcheck, thesaurus
from quill.core.quick_nav import build_nav_index

# Hard ceilings (seconds). Lower is better; never raise these to hide a
# regression -- fix the regression instead.
STARTUP_LEXICAL_WARMUP_BUDGET = 3.0
FIRST_SPELL_CHECK_BUDGET = 0.05
FIRST_THESAURUS_LOOKUP_BUDGET = 0.05
QUICK_NAV_PREWARM_BUDGET = 0.5


def _reset_spellcheck_cache() -> None:
    spellcheck._WORDLIST_CACHE = None
    spellcheck._ENCHANT_DICT = None
    spellcheck._ENCHANT_TRIED = False


def _reset_thesaurus_cache() -> None:
    thesaurus._INDEX = None
    thesaurus._LOAD_ERROR = None


def test_startup_lexical_warmup_within_budget() -> None:
    """The off-UI-thread startup warm-up (PERF-1/PERF-2) stays cheap."""
    _reset_spellcheck_cache()
    _reset_thesaurus_cache()
    try:
        start = perf_counter()
        spellcheck.preload()
        thesaurus.preload()
        elapsed = perf_counter() - start
        assert elapsed < STARTUP_LEXICAL_WARMUP_BUDGET, (
            f"startup lexical warm-up took {elapsed:.3f}s (budget {STARTUP_LEXICAL_WARMUP_BUDGET}s)"
        )
    finally:
        _reset_spellcheck_cache()
        _reset_thesaurus_cache()


def test_first_spell_check_within_budget() -> None:
    """After warm-up the first spell check pays no file-load cost."""
    _reset_spellcheck_cache()
    try:
        spellcheck.preload()
        start = perf_counter()
        spellcheck.is_known_word("document")
        elapsed = perf_counter() - start
        assert elapsed < FIRST_SPELL_CHECK_BUDGET, (
            f"first spell check took {elapsed:.3f}s (budget {FIRST_SPELL_CHECK_BUDGET}s)"
        )
    finally:
        _reset_spellcheck_cache()


def test_first_thesaurus_lookup_within_budget() -> None:
    """After warm-up the first thesaurus lookup pays no file-load cost."""
    _reset_thesaurus_cache()
    try:
        thesaurus.preload()
        start = perf_counter()
        thesaurus.lookup("happy")
        elapsed = perf_counter() - start
        assert elapsed < FIRST_THESAURUS_LOOKUP_BUDGET, (
            f"first thesaurus lookup took {elapsed:.3f}s (budget {FIRST_THESAURUS_LOOKUP_BUDGET}s)"
        )
    finally:
        _reset_thesaurus_cache()


def test_quick_nav_prewarm_within_budget() -> None:
    """Building the Quick Nav index for a large document stays responsive."""
    landmark_count = 5000
    text = "".join(f"# Heading {i}\nbody line {i}\n" for i in range(landmark_count))
    headings_by_level = {1: list(range(0, landmark_count * 4, 4))}
    context: dict[str, object] = {
        "headings_by_level": headings_by_level,
        "links": list(range(0, landmark_count)),
        "lists": [],
        "list_items": [],
        "tables": list(range(0, landmark_count)),
        "block_quotes": [],
        "bookmarks": list(range(0, landmark_count)),
        "code_blocks": [],
    }

    start = perf_counter()
    items = build_nav_index(text, context)
    elapsed = perf_counter() - start

    assert items
    assert elapsed < QUICK_NAV_PREWARM_BUDGET, (
        f"Quick Nav prewarm took {elapsed:.3f}s (budget {QUICK_NAV_PREWARM_BUDGET}s)"
    )
