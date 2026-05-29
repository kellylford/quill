from __future__ import annotations

from pathlib import Path

from quill.core.compliance import (
    dependency_names_from_pyproject,
    evaluate_license_gate,
    normalize_requirement_name,
    render_third_party_notices,
)


def test_normalize_requirement_name() -> None:
    assert normalize_requirement_name("wxPython>=4.2.2") == "wxpython"
    assert normalize_requirement_name("pytest-xdist>=3.6 ; extra == 'dev'") == "pytest-xdist"


def test_dependency_names_from_pyproject(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
dependencies = ["requests>=2", "rich==13"]
[project.optional-dependencies]
dev = ["pytest>=8"]
""".strip(),
        encoding="utf-8",
    )

    runtime = dependency_names_from_pyproject(pyproject, include_optional=False)
    all_dependencies = dependency_names_from_pyproject(pyproject, include_optional=True)

    assert runtime == ["requests", "rich"]
    assert all_dependencies == ["pytest", "requests", "rich"]


def test_evaluate_license_gate_and_render_notices() -> None:
    licenses = {"requests": "Apache-2.0", "wxpython": "UNKNOWN"}
    violations = evaluate_license_gate(licenses, {"MIT", "Apache-2.0"})
    assert violations == ["wxpython"]
    notices = render_third_party_notices(licenses)
    assert "| requests | Apache-2.0 |" in notices
    assert "| wxpython | UNKNOWN |" in notices
