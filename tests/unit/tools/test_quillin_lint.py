"""Tests for the Quillin submission linter (``quill.tools.quillin_lint``).

These exercise the three lint lenses independently: the executable JSON-Schema
subset, the contract validator, and the submission structure/capability hygiene
checks -- plus the directory-discovery and CLI exit-code behaviour CI relies on.
"""

from __future__ import annotations

import json
from pathlib import Path

from quill.tools import quillin_lint as ql

_VALID_MANIFEST = {
    "schema": "quill.extension/1",
    "id": "com.example.demo",
    "name": "Demo",
    "version": "1.0.0",
    "author": "Example",
    "description": "A demo Quillin.",
    "license": "MIT",
    "capabilities": ["editor.read", "editor.write", "ui.announce", "ui.command"],
    "main": "extension.py",
    "contributes": {
        "commands": [
            {"id": "ext.demo.snip", "title": "Snip", "run": {"snippet": "hi ${selection}"}},
            {"id": "ext.demo.run", "title": "Run", "run": {"handler": "go"}},
        ],
        "menus": [{"parent": "Format", "command": "ext.demo.run"}],
    },
}


def _write_quillin(directory: Path, manifest: object, *, with_main: bool = True) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.json").write_text(
        json.dumps(manifest) if not isinstance(manifest, str) else manifest,
        encoding="utf-8",
    )
    if with_main:
        (directory / "extension.py").write_text("def register(api):\n    pass\n", encoding="utf-8")
        (directory / "README.md").write_text("# Demo\n", encoding="utf-8")
    return directory


# -- schema subset -------------------------------------------------------------


def test_schema_accepts_a_valid_manifest() -> None:
    assert ql._schema_errors(_VALID_MANIFEST, ql.load_schema(), "$") == []


def test_schema_rejects_unknown_top_level_property() -> None:
    bad = {**_VALID_MANIFEST, "surprise": True}
    errors = ql._schema_errors(bad, ql.load_schema(), "$")
    assert any("unknown property 'surprise'" in e for e in errors)


def test_schema_rejects_wrong_const_and_enum() -> None:
    schema = ql.load_schema()
    bad_schema = ql._schema_errors({**_VALID_MANIFEST, "schema": "quill.extension/9"}, schema, "$")
    assert any("must equal" in e for e in bad_schema)
    bad_cap = {**_VALID_MANIFEST, "capabilities": ["editor.read", "telepathy"]}
    assert any("is not one of" in e for e in ql._schema_errors(bad_cap, schema, "$"))


def test_schema_enforces_pattern_and_oneof_run() -> None:
    schema = ql.load_schema()
    bad_id = json.loads(json.dumps(_VALID_MANIFEST))
    bad_id["contributes"]["commands"][0]["id"] = "demo.snip"  # missing ext. prefix
    assert ql._schema_errors(bad_id, schema, "$")
    both = json.loads(json.dumps(_VALID_MANIFEST))
    both["contributes"]["commands"][0]["run"] = {"snippet": "x", "handler": "y"}
    assert ql._schema_errors(both, schema, "$")


def test_schema_if_then_requires_main_for_handler() -> None:
    schema = ql.load_schema()
    no_main = json.loads(json.dumps(_VALID_MANIFEST))
    del no_main["main"]
    errors = ql._schema_errors(no_main, schema, "$")
    assert any("missing required property 'main'" in e for e in errors)


# -- agreement with the authority ---------------------------------------------


def test_schema_and_validator_agree_on_valid_manifest() -> None:
    # Both lenses must accept a clean manifest -- proves no drift between the
    # published schema artifact and the runtime validator.
    assert ql.lint_manifest_object(_VALID_MANIFEST) == []


# -- directory lint ------------------------------------------------------------


def test_valid_directory_passes_strict(tmp_path: Path) -> None:
    directory = _write_quillin(tmp_path / "demo", _VALID_MANIFEST)
    report = ql.lint_quillin(directory)
    assert report.ok(strict=True), report.render()


def test_missing_manifest_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    report = ql.lint_quillin(tmp_path / "empty")
    assert not report.ok()
    assert any(p.code == ql.CODE_STRUCTURE for p in report.errors)


def test_invalid_json_is_reported(tmp_path: Path) -> None:
    directory = _write_quillin(tmp_path / "broken", "{ not json", with_main=False)
    report = ql.lint_quillin(directory)
    assert any(p.code == ql.CODE_JSON for p in report.errors)


def test_declared_main_must_exist(tmp_path: Path) -> None:
    directory = _write_quillin(tmp_path / "nomain", _VALID_MANIFEST, with_main=False)
    report = ql.lint_quillin(directory)
    assert any("does not exist" in p.message for p in report.errors)


def test_missing_readme_and_license_warn(tmp_path: Path) -> None:
    manifest = {k: v for k, v in _VALID_MANIFEST.items() if k != "license"}
    directory = tmp_path / "warn"
    directory.mkdir()
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / "extension.py").write_text("def register(api):\n    pass\n", encoding="utf-8")
    report = ql.lint_quillin(directory)
    assert report.ok()  # warnings only
    assert not report.ok(strict=True)
    codes = {p.message for p in report.warnings}
    assert any("README" in m for m in codes)
    assert any("license" in m for m in codes)


def test_consent_gated_capability_warns(tmp_path: Path) -> None:
    manifest = json.loads(json.dumps(_VALID_MANIFEST))
    manifest["capabilities"].append("net")
    directory = _write_quillin(tmp_path / "net", manifest)
    report = ql.lint_quillin(directory)
    assert any(p.code == ql.CODE_CAPABILITY and "net" in p.message for p in report.warnings)


# -- discovery + CLI -----------------------------------------------------------


def test_discover_collection_and_single(tmp_path: Path) -> None:
    _write_quillin(tmp_path / "collection" / "a", _VALID_MANIFEST)
    _write_quillin(tmp_path / "collection" / "b", _VALID_MANIFEST)
    found = ql.discover_quillins(tmp_path / "collection")
    assert {p.name for p in found} == {"a", "b"}
    single = ql.discover_quillins(tmp_path / "collection" / "a")
    assert [p.name for p in single] == ["a"]


def test_cli_returns_zero_for_valid_and_one_for_invalid(tmp_path: Path) -> None:
    good = _write_quillin(tmp_path / "good", _VALID_MANIFEST)
    assert ql.main([str(good), "--strict"]) == 0
    bad = _write_quillin(tmp_path / "bad", {**_VALID_MANIFEST, "schema": "nope"})
    assert ql.main([str(bad)]) == 1


def test_cli_fails_on_path_with_no_quillin(tmp_path: Path) -> None:
    (tmp_path / "nothing").mkdir()
    assert ql.main([str(tmp_path / "nothing")]) == 1


def test_bundled_quillin_passes_strict() -> None:
    # The shipped bundled Quillin must itself be an exemplary submission.
    bundled = ql._REPO_ROOT / "quill" / "quillins_bundled"
    found = ql.discover_quillins(bundled)
    assert found, "expected at least one bundled Quillin"
    for directory in found:
        report = ql.lint_quillin(directory)
        assert report.ok(strict=True), report.render(strict=True)
