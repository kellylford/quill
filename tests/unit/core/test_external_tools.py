from __future__ import annotations

from pathlib import Path

from quill.core.external_tools import (
    format_tool_status_report,
    get_external_tool_status,
)


def test_detect_tool_prefers_bundled_path(monkeypatch, tmp_path: Path) -> None:
    tool_root = tmp_path / "tools" / "pandoc"
    tool_root.mkdir(parents=True)
    executable = tool_root / "pandoc.exe"
    executable.write_text("binary", encoding="utf-8")
    monkeypatch.setenv("QUILL_APP_ROOT", str(tmp_path))
    monkeypatch.setattr("quill.core.external_tools._tool_version", lambda *_args: "Pandoc 3.0")

    status = get_external_tool_status("pandoc")

    assert status.installed is True
    assert status.source == "bundled"
    assert status.path == str(executable.resolve())
    assert status.version == "Pandoc 3.0"


def test_format_tool_status_report_mentions_install_command(monkeypatch) -> None:
    monkeypatch.delenv("QUILL_APP_ROOT", raising=False)
    monkeypatch.setattr("quill.core.external_tools.shutil.which", lambda _name: None)

    report = format_tool_status_report()

    assert "Pandoc" in report
    assert "Install command:" in report
    assert "HTML Tidy" in report
    assert "PyMarkdown" in report
