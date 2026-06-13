"""Version consistency gate (GATE-VC).

Ensures that all version-bearing files in the repo agree with the
authoritative version in ``quill/__init__.py``.

Files checked:

- ``quill/__init__.py`` -- authoritative source (read first)
- ``pyproject.toml``    -- must use ``dynamic = ["version"]`` (not a static
                           ``version =`` field); ``[tool.hatch.version] path``
                           must point at ``quill/__init__.py``
- ``installer/quill.iss`` -- ``#define AppVersion`` must match
- ``CHANGELOG.md``     -- the topmost version heading (``## <version>``) must match

Exit 0 on success, 1 with diagnostics on any mismatch.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


def _authoritative_version(repo_root: Path) -> str:
    init_py = repo_root / "quill" / "__init__.py"
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init_py.read_text(), re.M)
    if not match:
        raise RuntimeError(f"Could not find __version__ in {init_py}")
    return match.group(1)


def _check_pyproject(repo_root: Path, canonical: str) -> list[str]:
    errors: list[str] = []
    pyproject = repo_root / "pyproject.toml"
    with pyproject.open("rb") as fh:
        data = tomllib.load(fh)

    project = data.get("project", {})
    if "version" in project:
        errors.append(
            f"pyproject.toml: static 'version = \"{project['version']}\"' found. "
            "Remove it; quill/__init__.py is the authoritative source. "
            'Use dynamic = ["version"] + [tool.hatch.version] path = "quill/__init__.py".'
        )

    dynamic = project.get("dynamic", [])
    if "version" not in dynamic:
        errors.append(
            "pyproject.toml: 'version' is not in project.dynamic. "
            'Add dynamic = ["version"] and [tool.hatch.version] path = "quill/__init__.py".'
        )

    hatch_version = data.get("tool", {}).get("hatch", {}).get("version", {})
    path_val = hatch_version.get("path", "")
    if path_val != "quill/__init__.py":
        errors.append(
            f'pyproject.toml: [tool.hatch.version] path = "{path_val}" '
            'does not point at "quill/__init__.py".'
        )

    return errors


def _check_iss(repo_root: Path, canonical: str) -> list[str]:
    errors: list[str] = []
    iss = repo_root / "installer" / "quill.iss"
    if not iss.exists():
        return errors  # not required for all contributors

    text = iss.read_text(encoding="utf-8")
    match = re.search(r'#define AppVersion "([^"]+)"', text)
    if not match:
        errors.append("installer/quill.iss: could not find #define AppVersion line.")
        return errors

    iss_version = match.group(1)
    if iss_version != canonical:
        errors.append(
            f'installer/quill.iss: AppVersion is "{iss_version}", '
            f'expected "{canonical}" (from quill/__init__.py).'
        )

    # OutputBaseFilename should also match
    fn_match = re.search(r"OutputBaseFilename=Quill-Setup-([^\r\n]+)", text)
    if fn_match:
        fn_version = fn_match.group(1).strip()
        if fn_version != canonical:
            errors.append(
                f'installer/quill.iss: OutputBaseFilename contains version "{fn_version}", '
                f'expected "{canonical}".'
            )

    return errors


def _check_changelog(repo_root: Path, canonical: str) -> list[str]:
    errors: list[str] = []
    changelog = repo_root / "CHANGELOG.md"
    if not changelog.exists():
        return errors

    text = changelog.read_text(encoding="utf-8")
    # Find first ## heading that looks like a version (e.g. "## 0.5.0" or "## 0.5.0 (2026-...)")
    match = re.search(r"^## (\d+\.\d+[\w.]*)[\s(]", text, re.M)
    if not match:
        errors.append("CHANGELOG.md: could not find a version heading (## X.Y.Z).")
        return errors

    top_version = match.group(1)
    if top_version != canonical:
        errors.append(
            f'CHANGELOG.md: top version heading is "{top_version}", '
            f'expected "{canonical}" (from quill/__init__.py). '
            "Add a new ## entry for the current release."
        )

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        canonical = _authoritative_version(repo_root)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"GATE-VC FAIL: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors.extend(_check_pyproject(repo_root, canonical))
    errors.extend(_check_iss(repo_root, canonical))
    errors.extend(_check_changelog(repo_root, canonical))

    if errors:
        print("GATE-VC FAIL: version inconsistency detected.", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(
            f"\nAuthoritative version (quill/__init__.py): {canonical}",
            file=sys.stderr,
        )
        return 1

    print(f"GATE-VC OK: all version references agree on {canonical}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
