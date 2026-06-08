"""Submission linter for Quillins: validator + schema check + structure gate.

This is the single front door an author (or CI) runs before a Quillin is
submitted for bundling or listing. It is deliberately dependency-free and
``wx``-free so it runs anywhere ``quill`` imports, and it layers three
independent checks so a problem is caught by whichever lens sees it first:

1. **Schema check** -- the published JSON Schema artifact
   (``quill/core/schemas/extension.json``) is made *executable* here by a small,
   self-contained validator covering the JSON-Schema subset that schema uses
   (``type``/``const``/``enum``/``pattern``/length/``required``/``properties``/
   ``additionalProperties``/``items``/``uniqueItems``/``oneOf``/``allOf``/
   ``if``-``then``/``contains``). This grounds every error in the same schema
   external tools and editors consume, and proves the published schema and the
   runtime validator cannot silently drift.
2. **Manifest validation** -- :func:`quill.core.quillins.validation.validate_manifest`,
   the authority the loader actually enforces, runs next and reports any
   contract problem the schema subset does not encode (e.g. the handler -> main
   + ``ui.command`` rule).
3. **Submission structure & capability hygiene** -- the entry module exists when
   declared, a README and a license are present, and every consent-gated
   capability (``fs.*``/``net``) is surfaced for deliberate reviewer scrutiny.

Errors fail the lint (non-zero exit); warnings are advisory unless ``--strict``
is passed, which CI uses so a submission cannot land with unresolved advisories.

Run directly::

    python -m quill.tools.quillin_lint path\\to\\quillin
    python -m quill.tools.quillin_lint quill\\quillins_bundled --strict

A path that itself contains ``manifest.json`` is linted as one Quillin; a path
that does not is treated as a *collection* and every immediate child directory
holding a ``manifest.json`` is linted.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from quill.core.quillins.model import CONSENT_GATED_CAPABILITIES
from quill.core.quillins.validation import validate_manifest

_REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = _REPO_ROOT / "quill" / "core" / "schemas" / "extension.json"
_MANIFEST_FILENAME = "manifest.json"

ERROR = "error"
WARNING = "warning"

#: Severity-tagged problem codes, grouped by the lens that emits them.
CODE_JSON = "json"
CODE_SCHEMA = "schema"
CODE_MANIFEST = "manifest"
CODE_STRUCTURE = "structure"
CODE_CAPABILITY = "capability"


@dataclass(frozen=True)
class LintProblem:
    """One finding: an error blocks submission, a warning advises review."""

    severity: str
    code: str
    message: str

    def render(self) -> str:
        return f"  [{self.severity}:{self.code}] {self.message}"


@dataclass
class LintReport:
    """The collected findings for one Quillin directory."""

    path: Path
    problems: list[LintProblem] = field(default_factory=list)

    def add(self, severity: str, code: str, message: str) -> None:
        self.problems.append(LintProblem(severity, code, message))

    @property
    def errors(self) -> list[LintProblem]:
        return [p for p in self.problems if p.severity == ERROR]

    @property
    def warnings(self) -> list[LintProblem]:
        return [p for p in self.problems if p.severity == WARNING]

    def ok(self, *, strict: bool = False) -> bool:
        if self.errors:
            return False
        return not (strict and self.warnings)

    def render(self, *, strict: bool = False) -> str:
        status = "PASS" if self.ok(strict=strict) else "FAIL"
        lines = [f"{status}  {self.path}"]
        lines.extend(problem.render() for problem in self.problems)
        if not self.problems:
            lines.append("  (no problems)")
        return "\n".join(lines)


# -- executable JSON-Schema subset --------------------------------------------

_JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def _type_ok(value: object, expected: str) -> bool:
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    python_type = _JSON_TYPES.get(expected)
    if python_type is None:
        return True
    return isinstance(value, python_type)


def _schema_matches(value: object, schema: dict[str, object]) -> bool:
    """True when ``value`` satisfies ``schema`` (used for oneOf/if branches)."""

    return not _schema_errors(value, schema, "$")


def _schema_errors(value: object, schema: dict[str, object], path: str) -> list[str]:
    """Validate ``value`` against the JSON-Schema ``schema`` subset.

    Returns a list of human-readable problems, each prefixed with the JSON path
    at which it was found. Supports only the keywords ``extension.json`` uses.
    """

    errors: list[str] = []

    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _type_ok(value, expected_type):
        errors.append(f"{path}: expected type '{expected_type}'")
        # Type mismatch makes deeper checks meaningless.
        return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")

    enum = schema.get("enum")
    if isinstance(enum, list) and value not in enum:
        errors.append(f"{path}: {value!r} is not one of {enum}")

    if isinstance(value, str):
        errors.extend(_string_errors(value, schema, path))
    if isinstance(value, list):
        errors.extend(_array_errors(value, schema, path))
    if isinstance(value, dict):
        errors.extend(_object_errors(value, schema, path))

    one_of = schema.get("oneOf")
    if isinstance(one_of, list):
        errors.extend(_combinator_errors(value, one_of, "oneOf", path))

    # allOf propagates the *real* inner errors (e.g. the if/then "main is
    # required for a handler command" rule) rather than a generic message.
    all_of = schema.get("allOf")
    if isinstance(all_of, list):
        for sub in all_of:
            if isinstance(sub, dict):
                errors.extend(_schema_errors(value, sub, path))

    if "if" in schema:
        errors.extend(_conditional_errors(value, schema, path))

    return errors


def _string_errors(value: str, schema: dict[str, object], path: str) -> list[str]:
    errors: list[str] = []
    pattern = schema.get("pattern")
    if isinstance(pattern, str) and re.search(pattern, value) is None:
        errors.append(f"{path}: {value!r} does not match pattern '{pattern}'")
    minimum = schema.get("minLength")
    if isinstance(minimum, int) and len(value) < minimum:
        errors.append(f"{path}: shorter than minLength {minimum}")
    maximum = schema.get("maxLength")
    if isinstance(maximum, int) and len(value) > maximum:
        errors.append(f"{path}: longer than maxLength {maximum}")
    return errors


def _array_errors(value: list[object], schema: dict[str, object], path: str) -> list[str]:
    errors: list[str] = []
    if schema.get("uniqueItems") is True:
        seen: list[object] = []
        for item in value:
            if item in seen:
                errors.append(f"{path}: items must be unique (duplicate {item!r})")
                break
            seen.append(item)
    items = schema.get("items")
    if isinstance(items, dict):
        for index, item in enumerate(value):
            errors.extend(_schema_errors(item, items, f"{path}[{index}]"))
    contains = schema.get("contains")
    if isinstance(contains, dict) and not any(_schema_matches(item, contains) for item in value):
        errors.append(f"{path}: no item satisfies the 'contains' schema")
    return errors


def _object_errors(value: dict[str, object], schema: dict[str, object], path: str) -> list[str]:
    errors: list[str] = []
    required = schema.get("required")
    if isinstance(required, list):
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property '{key}'")
    properties = schema.get("properties")
    properties = properties if isinstance(properties, dict) else {}
    if schema.get("additionalProperties") is False:
        for key in value:
            if key not in properties:
                errors.append(f"{path}: unknown property '{key}'")
    for key, subschema in properties.items():
        if key in value and isinstance(subschema, dict):
            errors.extend(_schema_errors(value[key], subschema, f"{path}.{key}"))
    return errors


def _combinator_errors(
    value: object, subschemas: list[object], combinator: str, path: str
) -> list[str]:
    matches = [_schema_matches(value, sub) for sub in subschemas if isinstance(sub, dict)]
    if combinator == "oneOf" and sum(matches) != 1:
        return [f"{path}: must match exactly one of the {len(matches)} schemas"]
    return []


def _conditional_errors(value: object, schema: dict[str, object], path: str) -> list[str]:
    if_schema = schema.get("if")
    then_schema = schema.get("then")
    else_schema = schema.get("else")
    if not isinstance(if_schema, dict):
        return []
    if _schema_matches(value, if_schema):
        if isinstance(then_schema, dict):
            return _schema_errors(value, then_schema, path)
    elif isinstance(else_schema, dict):
        return _schema_errors(value, else_schema, path)
    return []


def load_schema() -> dict[str, object]:
    """Load the published extension manifest JSON Schema."""

    return dict(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


# -- the submission lint -------------------------------------------------------


def lint_manifest_object(manifest: object, schema: dict[str, object] | None = None) -> list[str]:
    """Schema-check then contract-validate an in-memory manifest object.

    Returns a flat list of error strings (schema findings first). This is the
    pure, IO-free core used by both the directory linter and the test suite.
    """

    schema = schema if schema is not None else load_schema()
    problems = list(_schema_errors(manifest, schema, "$"))
    problems.extend(validate_manifest(manifest))
    return problems


def lint_quillin(directory: Path, *, schema: dict[str, object] | None = None) -> LintReport:
    """Lint a single Quillin directory and return its report."""

    report = LintReport(path=directory)
    manifest_path = directory / _MANIFEST_FILENAME
    if not manifest_path.is_file():
        report.add(ERROR, CODE_STRUCTURE, f"no {_MANIFEST_FILENAME} found")
        return report

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        report.add(ERROR, CODE_JSON, f"{_MANIFEST_FILENAME} is not valid JSON: {exc}")
        return report

    schema = schema if schema is not None else load_schema()
    for problem in _schema_errors(raw, schema, "$"):
        report.add(ERROR, CODE_SCHEMA, problem)
    for problem in validate_manifest(raw):
        report.add(ERROR, CODE_MANIFEST, problem)

    if isinstance(raw, dict):
        _check_structure(raw, directory, report)
        _check_capability_hygiene(raw, report)
    return report


def _check_structure(manifest: dict[str, object], directory: Path, report: LintReport) -> None:
    main = manifest.get("main")
    if isinstance(main, str) and main:
        entry = (directory / main).resolve()
        if directory.resolve() not in entry.parents and entry != directory.resolve():
            report.add(ERROR, CODE_STRUCTURE, f"main '{main}' escapes the Quillin directory")
        elif not entry.is_file():
            report.add(ERROR, CODE_STRUCTURE, f"main module '{main}' does not exist on disk")

    if not _has_file(directory, ("README.md", "README.rst", "README.txt", "README")):
        report.add(WARNING, CODE_STRUCTURE, "no README found (recommended for submission)")

    has_license_file = _has_file(directory, ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"))
    declares_license = bool(str(manifest.get("license", "")).strip())
    if not has_license_file and not declares_license:
        report.add(
            WARNING,
            CODE_STRUCTURE,
            "no license declared (manifest 'license' field) or LICENSE file present",
        )

    if not str(manifest.get("description", "")).strip():
        report.add(WARNING, CODE_STRUCTURE, "no description provided (recommended for listing)")
    if not str(manifest.get("author", "")).strip():
        report.add(WARNING, CODE_STRUCTURE, "no author provided (recommended for listing)")


def _check_capability_hygiene(manifest: dict[str, object], report: LintReport) -> None:
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list):
        return
    for capability in capabilities:
        if capability in CONSENT_GATED_CAPABILITIES:
            report.add(
                WARNING,
                CODE_CAPABILITY,
                f"declares consent-gated capability '{capability}' -- "
                "reviewers must confirm it is necessary and used transparently",
            )


def _has_file(directory: Path, names: Iterable[str]) -> bool:
    return any((directory / name).is_file() for name in names)


def discover_quillins(path: Path) -> list[Path]:
    """Resolve a path into the Quillin directories it names.

    A directory holding ``manifest.json`` is one Quillin; otherwise it is a
    collection and every immediate child holding a ``manifest.json`` is returned.
    """

    if (path / _MANIFEST_FILENAME).is_file():
        return [path]
    if not path.is_dir():
        return []
    return [
        child
        for child in sorted(path.iterdir(), key=lambda p: p.name)
        if child.is_dir() and (child / _MANIFEST_FILENAME).is_file()
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Quillin directories (or collections of them) to lint.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (used by submission CI).",
    )
    args = parser.parse_args(argv)

    schema = load_schema()
    targets: list[Path] = []
    for path in args.paths:
        found = discover_quillins(path)
        if not found:
            print(f"FAIL  {path}\n  [error:structure] no Quillin (manifest.json) found here")
            return 1
        targets.extend(found)

    failed = 0
    for directory in targets:
        report = lint_quillin(directory, schema=schema)
        print(report.render(strict=args.strict))
        if not report.ok(strict=args.strict):
            failed += 1

    total = len(targets)
    passed = total - failed
    print(f"\nLinted {total} Quillin(s): {passed} passed, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
