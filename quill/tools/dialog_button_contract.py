"""Dialog escape/affirmative button-wiring audit (A11Y-4 / DLG-3 reinforcement).

The dialog inventory (``dialog_inventory.py``) proves every dialog *surface* is
registered and classified, and the focus helpers in ``dialog_contract`` are unit
tested in isolation. Neither, however, verifies that when a dialog declares its
Escape id via ``apply_modal_ids(...)`` there is an actual button carrying that
id. That gap let #124 ship: ``PromptStudioDialog`` called
``apply_modal_ids(escape_id=wx.ID_CANCEL)`` but built no ``wx.ID_CANCEL`` button,
so ``SetEscapeId(wx.ID_CANCEL)`` had nothing to activate and Escape could not
close the dialog (a keyboard trap, WCAG 2.1.2).

Why a naive check does not work (and why #124 slipped through): a dialog's
buttons and its ``apply_modal_ids`` call are frequently in *different* methods
(``__init__`` builds the buttons, ``show`` declares the ids), and stock/native
wx dialogs (``wx.MessageDialog`` and friends) supply OK/Cancel/Yes/No buttons
*implicitly*. A per-function or native-inclusive scan therefore drowns in false
positives. This audit narrows to the only surface that must wire its own
buttons -- a raw ``wx.Dialog(...)`` (the sanctioned ``hardened_custom`` base) --
and collects the backing buttons across the right scope:

* a **dedicated dialog class** (one that stores ``self.<attr> = wx.Dialog(...)``)
  is scanned as a whole, because it builds one dialog in ``__init__`` and refers
  to it across ``show`` / handler methods;
* a **function-local** raw ``wx.Dialog(...)`` is scanned within that function.

Only ``escape_id`` is audited: an unbacked ``affirmative_id`` (Enter) is benign
because dialogs routinely accept Enter via a char hook, whereas an unbacked
``escape_id`` with no manual ``WXK_ESCAPE`` handler is a keyboard trap. For each
standard ``wx.ID_*`` escape id in such a scope, the audit checks that a matching
button exists -- an explicit ``wx.Button(..., id=wx.ID_*)`` (keyword or
positional) or a ``CreateButtonSizer`` / ``CreateStdDialogButtonSizer`` /
``CreateSeparatedButtonSizer`` flag that synthesizes it -- or that the scope
handles ``WXK_ESCAPE`` itself. Non-standard ids (custom ``self.ID_*`` constants)
are skipped because their backing buttons cannot be resolved statically.

The escape-id check can be opted out for a single call by adding a trailing
``# noqa: dialog_button_contract`` comment on the ``apply_modal_ids`` line.
This is the documented escape hatch for stock wx dialogs (MessageDialog and
friends) where the synthetic YES / NO buttons live below the AST horizon. A
call without the pragma is still audited strictly, so the original WCAG
keyboard trap cannot reappear by accident.

Run directly (``python -m quill.tools.dialog_button_contract``) to print any
violations; the gate lives in ``tests/unit/tools/test_dialog_button_contract.py``
and in the Security CI banned-pattern job.
"""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PACKAGE_ROOT = _REPO_ROOT / "quill"

# Trailing ``# noqa: dialog_button_contract`` comments on an
# ``apply_modal_ids`` call opt the call out of the static escape-id audit.
# This is the documented escape hatch for stock wx dialogs whose YES/NO
# buttons are synthesised at runtime (the static walk cannot see them).
_NOAQA_RE = re.compile(
    r"""\#\s*noqa\s*:\s*dialog_button_contract""",
    re.VERBOSE,
)


def _source_has_noqa(source: str, line: int) -> bool:
    """Return True when ``source`` carries the audit opt-out near ``line``.

    Checks the call's own line and the next two lines so a trailing
    comment on the same statement is recognised even when the line wrap
    places the comment on a continuation row.
    """
    lines = source.splitlines()
    for offset in range(0, 3):
        index = line - 1 + offset
        if 0 <= index < len(lines) and _NOAQA_RE.search(lines[index]):
            return True
    return False


def _pragma_for_call(source: str, node: ast.Call) -> bool:
    """True when the ``apply_modal_ids`` call at ``node`` is pragma-exempt."""
    line = getattr(node, "lineno", None)
    if line is None:
        return False
    return _source_has_noqa(source, line)


#: Standard wx id -> the CreateButtonSizer flag that synthesizes its button.
_ID_TO_FLAG = {
    "ID_OK": "OK",
    "ID_CANCEL": "CANCEL",
    "ID_YES": "YES",
    "ID_NO": "NO",
    "ID_CLOSE": "CLOSE",
    "ID_APPLY": "APPLY",
    "ID_HELP": "HELP",
    "ID_SAVE": "SAVE",
}
_FLAG_TO_ID = {flag: wx_id for wx_id, flag in _ID_TO_FLAG.items()}
# Used below in `_verifiable_ids_in_dialog` to translate a
# CreateButtonSizer flag string ("YES", "NO", "APPLY", ...) back to the
# wx id it synthesizes ("ID_YES", "ID_NO", ...). Not part of the
# public surface.

#: Standard ids we can statically verify. Anything else (custom ``ID_INSERT``,
#: ``ID_DISCARD``, ``wx.ID_ANY``/``wx.ID_NONE`` sentinels) is skipped.
_VERIFIABLE_IDS = frozenset(_ID_TO_FLAG)

_BUTTON_SIZER_FACTORIES = frozenset({
    "CreateButtonSizer",
    "CreateStdDialogButtonSizer",
    "CreateSeparatedButtonSizer",
})


@dataclass(frozen=True)
class Violation:
    module: str
    scope: str
    wx_id: str

    def __str__(self) -> str:
        return (
            f"{self.module}::{self.scope}: apply_modal_ids escape_id="
            f"wx.{self.wx_id} but the dialog neither creates a button with that "
            f"id nor handles WXK_ESCAPE itself, so Escape cannot close it -- a "
            f"keyboard trap (WCAG 2.1.2, #124). Add wx.Button(id=wx.{self.wx_id}) "
            f"(or a CreateButtonSizer flag) or a WXK_ESCAPE char-hook handler."
        )


def _attr_name(node: ast.AST) -> str | None:
    """Return the trailing attribute name of an expression, else ``None``.

    ``wx.ID_CANCEL`` -> ``"ID_CANCEL"``; ``self._wx.ID_OK`` -> ``"ID_OK"``.
    """
    return node.attr if isinstance(node, ast.Attribute) else None


def _flag_names(node: ast.AST) -> set[str]:
    """Collect button-sizer flag names from ``wx.OK`` / ``wx.OK | wx.CANCEL``."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _flag_names(node.left) | _flag_names(node.right)
    name = _attr_name(node)
    return {name} if name else set()


def _call_attr(node: ast.Call) -> str | None:
    return node.func.attr if isinstance(node.func, ast.Attribute) else None


def _constructs_raw_dialog(node: ast.AST) -> bool:
    """True when ``node`` is a ``wx.Dialog(...)`` / ``self._wx.Dialog(...)`` call."""
    return isinstance(node, ast.Call) and _call_attr(node) == "Dialog"


def _collect_button_ids(bodies: list[ast.AST]) -> set[str]:
    """Return standard wx ids whose buttons are built anywhere under ``bodies``."""
    ids: set[str] = set()
    for root in bodies:
        for node in ast.walk(root):
            if not isinstance(node, ast.Call):
                continue
            attr = _call_attr(node)
            if attr == "Button":
                # wx.Button(parent, id=..., ...) or the positional form
                # wx.Button(parent, ID_OK, label=...): the id is the second
                # positional argument when present.
                if len(node.args) >= 2 and (name := _attr_name(node.args[1])):
                    ids.add(name)
                for kw in node.keywords:
                    if kw.arg == "id" and (name := _attr_name(kw.value)):
                        ids.add(name)
            elif attr in _BUTTON_SIZER_FACTORIES:
                for arg in node.args:
                    for flag in _flag_names(arg):
                        if flag in _FLAG_TO_ID:
                            ids.add(_FLAG_TO_ID[flag])
    return ids


def _call_has_audit_pragma(source: str, node: ast.Call) -> bool:
    """True when the ``apply_modal_ids`` call carries the audit opt-out pragma.

    The pragma is a deliberate opt-out for the rare case the static audit
    cannot see the dialog's actual buttons -- e.g. a stock
    ``wx.MessageDialog(wx.YES_NO | ...)``, where YES/NO are synthesised at
    runtime and the static walk has no way to find them. The pragma forces a
    conscious reviewer decision and keeps the no-pragma path strict so the
    original WCAG 2.1.2 (#124) keyboard trap cannot reappear.
    """
    return _pragma_for_call(source, node)


def _collect_escape_ids(source: str, bodies: list[ast.AST]) -> list[tuple[str, bool]]:
    """Return ``(escape_id, has_pragma)`` pairs from ``apply_modal_ids`` calls."""
    found: list[tuple[str, bool]] = []
    for root in bodies:
        for node in ast.walk(root):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Name) and node.func.id == "apply_modal_ids"):
                continue
            pragma = _call_has_audit_pragma(source, node)
            for kw in node.keywords:
                if kw.arg == "escape_id" and (name := _attr_name(kw.value)):
                    found.append((name, pragma))
    return found


def _handles_escape_manually(bodies: list[ast.AST]) -> bool:
    """True when the scope references ``WXK_ESCAPE`` (a manual Escape handler)."""
    for root in bodies:
        for node in ast.walk(root):
            if isinstance(node, ast.Attribute) and node.attr == "WXK_ESCAPE":
                return True
    return False


def _audit_scope(module: str, scope: str, source: str, bodies: list[ast.AST]) -> list[Violation]:
    escape_ids = _collect_escape_ids(source, bodies)
    if not escape_ids:
        return []
    if _handles_escape_manually(bodies):
        return []
    buttons = _collect_button_ids(bodies)
    violations: list[Violation] = []
    for wx_id, has_pragma in escape_ids:
        if has_pragma:
            continue
        if wx_id in _VERIFIABLE_IDS and wx_id not in buttons:
            violations.append(Violation(module, scope, wx_id))
    return violations


def _stores_dialog_attribute(cls: ast.ClassDef) -> bool:
    """True when the class assigns ``self.<attr> = wx.Dialog(...)`` somewhere."""
    for node in ast.walk(cls):
        if isinstance(node, ast.Assign) and _constructs_raw_dialog(node.value):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    return True
    return False


def _function_builds_local_dialog(func: ast.AST) -> bool:
    """True when the function assigns a local ``name = wx.Dialog(...)``."""
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and _constructs_raw_dialog(node.value):
            if any(isinstance(t, ast.Name) for t in node.targets):
                return True
    return False


def _audit_module(module: str, source: str, tree: ast.Module) -> list[Violation]:
    violations: list[Violation] = []

    def _walk(node: ast.AST, prefix: str, inside_dialog_class: bool) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                qual = f"{prefix}{child.name}"
                if _stores_dialog_attribute(child):
                    # Dedicated dialog class: buttons in __init__, ids in show/
                    # handlers -- audit the whole class body as one scope.
                    violations.extend(_audit_scope(module, qual, source, list(child.body)))
                    _walk(child, f"{qual}.", True)
                else:
                    _walk(child, f"{qual}.", inside_dialog_class)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{prefix}{child.name}"
                if not inside_dialog_class and _function_builds_local_dialog(child):
                    violations.extend(_audit_scope(module, qual, source, [child]))
                _walk(child, f"{qual}.", inside_dialog_class)
            else:
                _walk(child, prefix, inside_dialog_class)

    _walk(tree, "", False)
    return violations


def find_violations(package_root: Path = _PACKAGE_ROOT) -> list[Violation]:
    """Scan the package for hardened_custom dialogs with unbacked escape ids."""
    violations: list[Violation] = []
    for path in sorted(package_root.rglob("*.py")):
        rel = path.relative_to(_REPO_ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        violations.extend(_audit_module(rel, source, tree))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit dialog escape-id button wiring (#124).")
    parser.parse_args()
    violations = find_violations()
    if not violations:
        print("Dialog button-contract audit: OK")
        return 0
    print("Dialog button-contract violations:")
    for violation in violations:
        print(f"  {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
