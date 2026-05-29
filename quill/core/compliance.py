from __future__ import annotations

import re
import tomllib
from pathlib import Path

_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+")


def normalize_requirement_name(requirement: str) -> str:
    token = requirement.strip()
    match = _NAME_PATTERN.match(token)
    if match is None:
        return token.lower()
    return match.group(0).lower()


def dependency_names_from_pyproject(path: Path, include_optional: bool = True) -> list[str]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    project = data.get("project", {})
    if not isinstance(project, dict):
        return []
    dependencies: list[str] = []
    raw_dependencies = project.get("dependencies", [])
    if isinstance(raw_dependencies, list):
        dependencies.extend(item for item in raw_dependencies if isinstance(item, str))
    if include_optional:
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for values in optional.values():
                if isinstance(values, list):
                    dependencies.extend(item for item in values if isinstance(item, str))
    names = sorted({normalize_requirement_name(item) for item in dependencies if item.strip()})
    return names


def evaluate_license_gate(
    dependency_licenses: dict[str, str],
    allowed_licenses: set[str],
) -> list[str]:
    violations: list[str] = []
    for dependency, license_name in sorted(dependency_licenses.items()):
        normalized = license_name.strip()
        if not normalized or normalized not in allowed_licenses:
            violations.append(dependency)
    return violations


def render_third_party_notices(dependency_licenses: dict[str, str]) -> str:
    lines = ["Third-Party Notices", ""]
    if not dependency_licenses:
        lines.append("No third-party dependencies were declared.")
        return "\n".join(lines) + "\n"
    lines.append("| Dependency | License |")
    lines.append("| --- | --- |")
    for dependency, license_name in sorted(dependency_licenses.items()):
        lines.append(f"| {dependency} | {license_name or 'UNKNOWN'} |")
    lines.append("")
    return "\n".join(lines)
