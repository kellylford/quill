from __future__ import annotations

import json
from pathlib import Path

from scripts.build_windows_distribution import build_inno_setup_script, build_windows_distribution


def test_build_windows_distribution_writes_portable_and_installer_files(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "quill"
version = "2.4.6"
""".strip(),
        encoding="utf-8",
    )

    bundle = build_windows_distribution(pyproject, tmp_path / "dist")

    portable_dir = tmp_path / "dist" / "portable"
    installer_script = tmp_path / "dist" / "installer" / "quill.iss"
    assert portable_dir.exists()
    launcher = (portable_dir / "run-quill.cmd").read_text(encoding="utf-8")
    assert launcher.startswith("@echo off")
    assert "set QUILL_PORTABLE=1" in launcher
    assert "set QUILL_APP_ROOT=%~dp0" in launcher
    assert "set QUILL_PORTABLE_ROOT=%~dp0data" in launcher
    # Launcher prefers the bundled embedded Python before falling back to PATH.
    assert "QUILL_BUNDLED_PYTHON" in launcher
    assert "python\\python.exe" in launcher

    readme_text = (portable_dir / "README.txt").read_text(encoding="utf-8")
    assert "Quill Portable 2.4.6" in readme_text
    assert "Blind Information Technology Solutions (BITS)" in readme_text
    assert "first run" in readme_text.lower()
    assert "Pandoc Conversion Wizard" in readme_text

    assert (portable_dir / "docs" / "userguide.md").exists()
    assert (portable_dir / "docs" / "announcement-beta.md").exists()

    manifest_path = portable_dir / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["publisher"] == "Blind Information Technology Solutions (BITS)"
    assert manifest["version"] == "2.4.6"
    assert manifest["bundledPython"] is False
    assert manifest["bundledTools"] == []

    assert installer_script.exists()
    assert bundle["installer_script"] == str(installer_script)


def test_build_inno_setup_script_mentions_portable_bundle() -> None:
    script = build_inno_setup_script("9.9.9")

    assert '#define AppVersion "9.9.9"' in script
    assert 'Source: "..\\portable\\*"' in script
    # Publisher and accessibility-friendly installer flags are present.
    assert "Blind Information Technology Solutions (BITS)" in script
    assert "PrivilegesRequired=lowest" in script
    assert "WizardStyle=modern" in script
    assert "User Guide" in script
    assert "Beta Announcement" in script
    # File-association registry entries use HKCU only (never overwrite defaults).
    assert "HKCU" in script
    assert "HKLM" not in script
    # The script parses as plain ASCII text (catches stray bad characters).
    script.encode("ascii")


def test_build_windows_distribution_can_bundle_external_tools(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "quill"
version = "3.0.0"
""".strip(),
        encoding="utf-8",
    )
    fake_pandoc_dir = tmp_path / "pandoc"
    fake_pandoc_dir.mkdir()
    (fake_pandoc_dir / "pandoc.exe").write_text("binary", encoding="utf-8")

    bundle = build_windows_distribution(
        pyproject,
        tmp_path / "dist",
        bundled_tool_dirs={"pandoc": fake_pandoc_dir},
    )

    manifest = json.loads(
        (tmp_path / "dist" / "portable" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["bundledTools"] == ["pandoc"]
    assert (tmp_path / "dist" / "portable" / "tools" / "pandoc" / "pandoc.exe").exists()
    assert bundle["portable_dir"] == str(tmp_path / "dist" / "portable")
