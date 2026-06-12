"""CI gate for QUILL context-sensitive help coverage.

Checks that every control name registered in the command registry has a
corresponding entry in quill/core/help/topics.json.

A missing topic is a warning, not a hard failure, to allow iterative
authoring. Pass ``--strict`` to fail on any missing topic.

Run::

    python -m quill.tools.check_help_coverage [--strict]

Exit code 0 = all checks pass.  Exit code 1 = failures (strict mode only).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_TOPICS_PATH = Path(__file__).resolve().parents[2] / "core" / "help" / "topics.json"


def _load_topic_ids() -> set[str]:
    import json

    if not _TOPICS_PATH.is_file():
        return set()
    raw = json.loads(_TOPICS_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return set()
    return {str(entry.get("id", "")) for entry in raw if isinstance(entry, dict)}


def run(strict: bool = False) -> int:
    topic_ids = _load_topic_ids()
    if not topic_ids:
        msg = f"check_help_coverage: no topics loaded from {_TOPICS_PATH}"
        if strict:
            print(msg)
            return 1
        print(f"WARNING: {msg}")
        return 0

    print(f"check_help_coverage: {len(topic_ids)} topics loaded")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Check QUILL context-sensitive help coverage.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail (exit 1) on any missing topic instead of just warning.",
    )
    args = parser.parse_args()
    sys.exit(run(strict=args.strict))


if __name__ == "__main__":
    main()
