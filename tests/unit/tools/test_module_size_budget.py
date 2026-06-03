"""Tests for the GATE-11 module-size budget gate."""

from __future__ import annotations

import json
from pathlib import Path

from quill.tools.module_size_budget import (
    Violation,
    find_violations,
    iter_module_sizes,
    load_budget,
)


def test_repository_is_within_module_size_budget() -> None:
    # The live tree must always satisfy the ratchet.
    assert find_violations() == []


def test_budget_file_parses_and_tracks_the_known_large_modules() -> None:
    budgets, default_cap = load_budget()
    assert default_cap == 600
    # main_frame.py is the file GATE-11 exists to freeze.
    assert "quill/ui/main_frame.py" in budgets
    assert budgets["quill/ui/main_frame.py"] >= 1


def test_every_budget_entry_at_least_matches_current_size_or_smaller_is_fine() -> None:
    # A budget must never be set below a file's current size (that would be an
    # instant self-inflicted failure); the live tree proves this via
    # test_repository_is_within_module_size_budget, but assert the invariant
    # explicitly for the tracked files.
    budgets, _ = load_budget()
    sizes = iter_module_sizes()
    for path, budget in budgets.items():
        if path in sizes:
            assert sizes[path] <= budget, f"{path} exceeds its budget"


def test_tracked_file_over_budget_is_flagged(tmp_path: Path) -> None:
    pkg = tmp_path / "quill"
    (pkg / "ui").mkdir(parents=True)
    big = pkg / "ui" / "main_frame.py"
    big.write_text("\n".join(f"x = {i}" for i in range(100)), encoding="utf-8")
    budget_file = tmp_path / "budgets.json"
    budget_file.write_text(
        json.dumps({"_default_cap": 600, "budgets": {"quill/ui/main_frame.py": 50}}),
        encoding="utf-8",
    )

    violations = find_violations(package_root=pkg, budget_file=budget_file)

    assert len(violations) == 1
    assert "budget is 50" in str(violations[0])


def test_untracked_file_over_default_cap_is_flagged(tmp_path: Path) -> None:
    pkg = tmp_path / "quill"
    (pkg / "core").mkdir(parents=True)
    big = pkg / "core" / "sprawl.py"
    big.write_text("\n".join(f"x = {i}" for i in range(700)), encoding="utf-8")
    budget_file = tmp_path / "budgets.json"
    budget_file.write_text(json.dumps({"_default_cap": 600, "budgets": {}}), encoding="utf-8")

    violations = find_violations(package_root=pkg, budget_file=budget_file)

    assert len(violations) == 1
    assert "default cap" in str(violations[0])


def test_untracked_file_under_cap_is_allowed(tmp_path: Path) -> None:
    pkg = tmp_path / "quill"
    (pkg / "core").mkdir(parents=True)
    small = pkg / "core" / "tidy.py"
    small.write_text("\n".join(f"x = {i}" for i in range(50)), encoding="utf-8")
    budget_file = tmp_path / "budgets.json"
    budget_file.write_text(json.dumps({"_default_cap": 600, "budgets": {}}), encoding="utf-8")

    assert find_violations(package_root=pkg, budget_file=budget_file) == []


def test_stale_budget_entry_for_missing_file_is_flagged(tmp_path: Path) -> None:
    pkg = tmp_path / "quill"
    (pkg / "core").mkdir(parents=True)
    budget_file = tmp_path / "budgets.json"
    budget_file.write_text(
        json.dumps({"_default_cap": 600, "budgets": {"quill/core/gone.py": 100}}),
        encoding="utf-8",
    )

    violations = find_violations(package_root=pkg, budget_file=budget_file)

    assert len(violations) == 1
    assert "no longer exists" in str(violations[0])


def test_violation_str_is_readable() -> None:
    assert str(Violation("a/b.py", "boom")) == "a/b.py: boom"
