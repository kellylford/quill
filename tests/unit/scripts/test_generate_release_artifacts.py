from __future__ import annotations

from pathlib import Path

from scripts.generate_release_artifacts import build_provenance, build_sbom


def test_build_sbom_includes_project_and_dependencies(monkeypatch, tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "quill"
version = "1.2.3"
dependencies = ["alpha>=1.0"]

[project.optional-dependencies]
ui = ["beta>=2.0"]
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "scripts.generate_release_artifacts._installed_version",
        lambda name: f"{name}-version",
    )

    sbom = build_sbom(pyproject, include_optional=True)

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["metadata"]["component"]["version"] == "1.2.3"
    assert [component["name"] for component in sbom["components"]] == ["quill", "alpha", "beta"]


def test_build_provenance_lists_artifacts(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "quill"
version = "1.2.3"
""".strip(),
        encoding="utf-8",
    )
    provenance = build_provenance(pyproject, tmp_path / "sbom.json", {"status": "skipped"})

    assert provenance["project"]["version"] == "1.2.3"
    assert provenance["artifacts"][0]["kind"] == "sbom"
    assert provenance["vulnerabilityScan"]["status"] == "skipped"
