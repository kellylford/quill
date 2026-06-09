"""Module-size budget gate (GATE-11).

A ratcheting size budget that prevents new growth in the largest Python
modules and shrinks as extraction proceeds (CQ-1). The budget lives in
``module_size_budgets.json`` next to this file:

* Every tracked module has an explicit maximum line count (Python
  ``splitlines`` count). The gate fails when a tracked module grows past its
  budget. Budgets are a one-way ratchet maintained by hand: lower them as
  ``main_frame.py`` and friends are decomposed; never raise them to paper over
  growth.
* Any module that is *not* tracked must stay at or below the default cap
  (``_default_cap``, 600 lines). A new module that crosses the cap fails the
  gate until it is either split or given a deliberate, reviewed budget entry.

This makes "the largest files may not grow" un-regressable and steers new work
toward extraction (CQ-1) and cohesive modules instead of piling onto
``main_frame.py``.

Run directly (``python -m quill.tools.module_size_budget``) or via pytest
(``tests/unit/tools/test_module_size_budget.py``). Use ``--measure`` to print
current sizes (read-only) when ratcheting budgets down. Exit code is non-zero
when any violation is found.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PACKAGE_ROOT = _REPO_ROOT / "quill"
_BUDGET_FILE = Path(__file__).resolve().parent / "module_size_budgets.json"


class Violation:
    __slots__ = ("path", "message")

    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def _count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _rel(path: Path, base: Path) -> str:
    return str(path.relative_to(base)).replace("\\", "/")


def load_budget(budget_file: Path = _BUDGET_FILE) -> tuple[dict[str, int], int]:
    """Return ``(budgets, default_cap)`` parsed from the budget JSON."""
    data = json.loads(budget_file.read_text(encoding="utf-8"))
    # JSON5-style ``_comment`` keys are preserved for the human reader
    # (see ``quill/tools/module_size_budgets.md``) and stripped here so
    # downstream keys are guaranteed to be ``int`` budget values. Long-form
    # rationale belongs in the sibling markdown file, not in this JSON.
    budgets = {str(k): int(v) for k, v in data["budgets"].items() if not str(k).startswith("_")}
    default_cap = int(data["_default_cap"])
    return budgets, default_cap


def iter_module_sizes(package_root: Path = _PACKAGE_ROOT) -> dict[str, int]:
    """Map every tracked ``quill`` module path to its current line count."""
    base = package_root.parent
    sizes: dict[str, int] = {}
    for path in sorted(package_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        sizes[_rel(path, base)] = _count_lines(path)
    return sizes


def find_violations(
    package_root: Path = _PACKAGE_ROOT,
    budget_file: Path = _BUDGET_FILE,
) -> list[Violation]:
    """Return every module that violates the size budget."""
    budgets, default_cap = load_budget(budget_file)
    sizes = iter_module_sizes(package_root)
    violations: list[Violation] = []

    for rel_path, lines in sizes.items():
        if rel_path in budgets:
            budget = budgets[rel_path]
            if lines > budget:
                violations.append(
                    Violation(
                        rel_path,
                        f"is {lines} lines but the budget is {budget}; "
                        f"extract code into a new module instead of growing it "
                        f"(GATE-11). Do not raise the budget.",
                    )
                )
        elif lines > default_cap:
            violations.append(
                Violation(
                    rel_path,
                    f"is {lines} lines, over the {default_cap}-line default cap; "
                    f"split it, or add a deliberate, reviewed budget entry to "
                    f"quill/tools/module_size_budgets.json (GATE-11).",
                )
            )

    # A budget entry for a file that no longer exists is stale and should be
    # removed so the ratchet stays honest.
    for tracked in budgets:
        if tracked not in sizes:
            violations.append(
                Violation(
                    tracked,
                    "has a budget entry but no longer exists; remove the stale "
                    "entry from quill/tools/module_size_budgets.json (GATE-11).",
                )
            )

    return violations


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--measure" in args:
        for rel_path, lines in sorted(iter_module_sizes().items(), key=lambda kv: -kv[1]):
            print(f"{lines:6d}  {rel_path}")
        return 0

    violations = find_violations()
    if violations:
        print("GATE-11 module-size budget violations:", file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        return 1
    print("GATE-11 module-size budget: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
