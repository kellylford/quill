from __future__ import annotations

import argparse
from pathlib import Path

from quill.core.plain_language import lint_plain_language


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run controlled-vocabulary plain-language linting."
    )
    parser.add_argument("path", type=Path, help="File to lint")
    args = parser.parse_args()

    text = args.path.read_text(encoding="utf-8")
    issues = lint_plain_language(text)
    if not issues:
        print("No plain-language issues found.")
        return 0
    for issue in issues:
        print(
            f"{args.path}:{issue.line}:{issue.column}: "
            f"replace '{issue.phrase}' with '{issue.suggestion}'"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
