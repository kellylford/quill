"""Gate: every bundled Quillin must pass ``quillin_lint --strict``.

Bundled Quillins ship inside QUILL, so they are held to the same submission
bar CI enforces on third-party authors. This test discovers every Quillin under
``quill/quillins_bundled`` and fails if any has a lint error *or* an unresolved
advisory (``--strict`` parity), so a bundled extension can never regress below
the standard we ask contributors to meet.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quill.tools.quillin_lint import discover_quillins, lint_quillin

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BUNDLED_ROOT = _REPO_ROOT / "quill" / "quillins_bundled"

_BUNDLED_QUILLINS = discover_quillins(_BUNDLED_ROOT)


def test_bundled_quillins_are_discovered() -> None:
    assert _BUNDLED_QUILLINS, f"no bundled Quillins found under {_BUNDLED_ROOT}"


@pytest.mark.parametrize(
    "quillin_dir",
    _BUNDLED_QUILLINS,
    ids=[directory.name for directory in _BUNDLED_QUILLINS],
)
def test_bundled_quillin_passes_strict_lint(quillin_dir: Path) -> None:
    report = lint_quillin(quillin_dir)
    assert report.ok(strict=True), report.render(strict=True)


@pytest.mark.parametrize(
    "quillin_dir",
    _BUNDLED_QUILLINS,
    ids=[directory.name for directory in _BUNDLED_QUILLINS],
)
def test_bundled_quillin_ships_a_license_file(quillin_dir: Path) -> None:
    # Bundled Quillins are the gold-standard example contributors copy from, so
    # they must carry an explicit LICENSE file -- a manifest 'license' field
    # alone (which the linter accepts) is not enough for a shipped extension.
    license_names = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
    assert any((quillin_dir / name).is_file() for name in license_names), (
        f"{quillin_dir.name} must ship one of {license_names}"
    )
