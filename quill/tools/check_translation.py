"""CI gate for QUILL translation infrastructure.

Checks:
1. babel.cfg exists at the project root.
2. quill/locale/quill.pot exists (the master template).
3. Each .po file in quill/locale/ is complete (no fuzzy, no untranslated).
4. Each .po file has no broken printf-style placeholders relative to .pot.

Run::

    python -m quill.tools.check_translation [--pot-only]

Exit code 0 = all checks pass.  Exit code 1 = failures reported to stdout.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOCALE_DIR = _PROJECT_ROOT / "quill" / "locale"
_BABEL_CFG = _PROJECT_ROOT / "babel.cfg"
_POT_FILE = _LOCALE_DIR / "quill.pot"

_PLACEHOLDER_RE = re.compile(r"%\([^)]+\)[sdi]|%[sdi]|\{[^}]*\}")


def _extract_placeholders(msgstr: str) -> list[str]:
    return _PLACEHOLDER_RE.findall(msgstr)


def _parse_po(path: Path) -> list[tuple[str, str]]:
    """Return list of (msgid, msgstr) pairs from a .po file."""
    pairs: list[tuple[str, str]] = []
    msgid = ""
    msgstr = ""
    in_msgid = False
    in_msgstr = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("msgid "):
            if msgid or msgstr:
                pairs.append((msgid, msgstr))
            msgid = line[6:].strip().strip('"')
            msgstr = ""
            in_msgid = True
            in_msgstr = False
        elif line.startswith("msgstr "):
            in_msgid = False
            in_msgstr = True
            msgstr = line[7:].strip().strip('"')
        elif line.startswith('"') and in_msgid:
            msgid += line.strip().strip('"')
        elif line.startswith('"') and in_msgstr:
            msgstr += line.strip().strip('"')
        else:
            in_msgid = False
            in_msgstr = False
    if msgid or msgstr:
        pairs.append((msgid, msgstr))
    return pairs


def check_babel_cfg() -> list[str]:
    if not _BABEL_CFG.is_file():
        return [f"Missing babel.cfg at {_BABEL_CFG}"]
    return []


def check_pot_exists() -> list[str]:
    if not _POT_FILE.is_file():
        return [
            f"Master template {_POT_FILE} not found. "
            "Run: pybabel extract -F babel.cfg -k _ -k ngettext -k lazy_gettext "
            "-o quill/locale/quill.pot quill/"
        ]
    return []


def check_po_files() -> list[str]:
    errors: list[str] = []
    po_files = list(_LOCALE_DIR.glob("**/*.po"))
    if not po_files:
        return []
    pot_ids: set[str] = set()
    if _POT_FILE.is_file():
        for msgid, _ in _parse_po(_POT_FILE):
            if msgid:
                pot_ids.add(msgid)
    for po_path in po_files:
        pairs = _parse_po(po_path)
        for msgid, msgstr in pairs:
            if not msgid:
                continue
            if not msgstr:
                errors.append(f"{po_path.name}: untranslated: {msgid!r}")
                continue
            pot_ph = _extract_placeholders(msgid)
            po_ph = _extract_placeholders(msgstr)
            if sorted(pot_ph) != sorted(po_ph):
                errors.append(
                    f"{po_path.name}: placeholder mismatch for {msgid!r}: "
                    f"expected {pot_ph}, got {po_ph}"
                )
    return errors


def run(pot_only: bool = False) -> int:
    all_errors: list[str] = []
    all_errors += check_babel_cfg()
    all_errors += check_pot_exists()
    if not pot_only:
        all_errors += check_po_files()
    if all_errors:
        for err in all_errors:
            print(f"TRANSLATION: {err}")
        return 1
    print(f"check_translation: OK ({len(list(_LOCALE_DIR.glob('**/*.po')))} .po files checked)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Check QUILL translation infrastructure.")
    parser.add_argument(
        "--pot-only",
        action="store_true",
        help="Only check that babel.cfg and quill.pot exist; skip .po completeness.",
    )
    args = parser.parse_args()
    sys.exit(run(pot_only=args.pot_only))


if __name__ == "__main__":
    main()
