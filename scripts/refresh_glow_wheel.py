"""Rebuild the vendored GLOW contract wheel from source, reproducibly.

QUILL vendors the ``quill-glow-core`` contract wheel under ``vendor/wheels`` as
the offline floor for the GLOW accessibility engine. When the upstream
``quill-glow-core`` source changes (bug fixes, new rules surfaced through the
contract), run this script to rebuild the wheel from a committed source checkout
and refresh the vendored copy in one reproducible step, instead of copying files
by hand.

Usage (from the QUILL repo root)::

    python scripts/refresh_glow_wheel.py --source s:/code/quill-glow-core

The script:

1. Verifies the source checkout has no uncommitted changes (so the vendored
   wheel always corresponds to a known commit), unless ``--allow-dirty``.
2. Builds the wheel with ``pip wheel`` (the project's declared build backend).
3. Removes any older vendored ``quill_glow_core-*.whl`` and copies the fresh one
   into ``vendor/wheels``.
4. Prints the wheel name, size, and the source commit it was built from.

It deliberately does NOT commit anything; review the diff and commit the
refreshed wheel yourself.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SOURCE = Path("s:/code/quill-glow-core")


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True)


def _git_is_clean(source: Path) -> bool:
    result = _run(["git", "-C", str(source), "status", "--porcelain"])
    return result.returncode == 0 and not result.stdout.strip()


def _git_commit(source: Path) -> str:
    result = _run(["git", "-C", str(source), "rev-parse", "--short", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def refresh(source: Path, vendor_dir: Path, allow_dirty: bool) -> Path:
    if not source.is_dir():
        raise SystemExit(f"Source checkout not found: {source}")
    if not (source / "pyproject.toml").is_file():
        raise SystemExit(f"Not a quill-glow-core checkout (no pyproject.toml): {source}")
    if not allow_dirty and not _git_is_clean(source):
        raise SystemExit(
            f"Source checkout has uncommitted changes: {source}\n"
            "Commit them first (so the vendored wheel maps to a known commit), "
            "or pass --allow-dirty to override."
        )
    vendor_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="glow-wheel-") as tmp:
        build_dir = Path(tmp)
        print(f"Building quill-glow-core wheel from {source}...")
        result = _run(
            [sys.executable, "-m", "pip", "wheel", str(source), "--no-deps", "-w", str(build_dir)],
        )
        if result.returncode != 0:
            raise SystemExit(f"Wheel build failed:\n{result.stdout}\n{result.stderr}")
        built = sorted(build_dir.glob("quill_glow_core-*.whl"))
        if not built:
            raise SystemExit("Build produced no quill_glow_core wheel.")
        fresh = built[0]

        for stale in vendor_dir.glob("quill_glow_core-*.whl"):
            print(f"Removing stale vendored wheel: {stale.name}")
            stale.unlink()

        target = vendor_dir / fresh.name
        shutil.copy2(fresh, target)

    commit = _git_commit(source)
    print(f"Vendored {target.name} ({target.stat().st_size} bytes) from {source} @ {commit}")
    print("Review the diff and commit vendor/wheels yourself.")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Path to the quill-glow-core source checkout (default: {DEFAULT_SOURCE}).",
    )
    parser.add_argument(
        "--vendor-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "vendor" / "wheels",
        help="Destination vendor/wheels directory (default: this repo's).",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Build even if the source checkout has uncommitted changes.",
    )
    args = parser.parse_args()
    refresh(args.source, args.vendor_dir, args.allow_dirty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
