"""CI gate: every feature ID in COMMAND_FEATURE_MAP must exist in FEATURE_DEFINITIONS.

Catches typos and stale mappings before they become silent runtime failures — a
command mapped to a non-existent feature would either crash or never be filtered
correctly.

Run::

    python -m quill.tools.check_feature_tags

Exit 0 = all checks pass.  Exit 1 = failures reported to stdout.
"""

from __future__ import annotations

import sys


def run() -> int:
    from quill.core.feature_command_map import COMMAND_FEATURE_MAP
    from quill.core.features import FEATURE_DEFINITIONS

    errors: list[str] = []
    for command_id, feature_id in sorted(COMMAND_FEATURE_MAP.items()):
        if feature_id not in FEATURE_DEFINITIONS:
            errors.append(f"command {command_id!r} references unknown feature {feature_id!r}")

    if errors:
        for err in errors:
            print(f"FEATURE_TAGS: {err}")
        return 1

    print(
        f"check_feature_tags: OK "
        f"({len(COMMAND_FEATURE_MAP)} commands, "
        f"{len(set(COMMAND_FEATURE_MAP.values()))} features)"
    )
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
