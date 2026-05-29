from __future__ import annotations

import argparse
import json
from pathlib import Path

from quill.core.compliance import (
    dependency_names_from_pyproject,
    evaluate_license_gate,
    render_third_party_notices,
)

DEFAULT_ALLOWED_LICENSES = {"MIT", "BSD-3-Clause", "BSD-2-Clause", "Apache-2.0", "ISC", "PSF-2.0"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate third-party notices and enforce license gate."
    )
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--licenses", type=Path, default=Path("third_party_licenses.json"))
    parser.add_argument("--output", type=Path, default=Path("THIRD_PARTY_NOTICES.txt"))
    parser.add_argument("--runtime-only", action="store_true")
    args = parser.parse_args()

    dependencies = dependency_names_from_pyproject(
        args.pyproject,
        include_optional=not args.runtime_only,
    )
    declared = _load_license_map(args.licenses)
    dependency_licenses = {
        dependency: declared.get(dependency, "UNKNOWN") for dependency in dependencies
    }

    args.output.write_text(render_third_party_notices(dependency_licenses), encoding="utf-8")
    violations = evaluate_license_gate(dependency_licenses, DEFAULT_ALLOWED_LICENSES)
    if violations:
        print(f"License gate failed for: {', '.join(violations)}")
        return 1
    print(f"Wrote {args.output} ({len(dependency_licenses)} dependencies)")
    return 0


def _load_license_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str):
            normalized[key.lower()] = value.strip()
    return normalized


if __name__ == "__main__":
    raise SystemExit(main())
