from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quill.io.pandoc import (
    PandocConversionError,
    PandocUnavailableError,
    convert_document_with_pandoc,
)


def test_convert_document_with_pandoc_requires_installed_tool(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "quill.io.pandoc.get_external_tool_status",
        lambda _tool_id: type("Status", (), {"installed": False, "path": None})(),
    )

    with pytest.raises(PandocUnavailableError):
        convert_document_with_pandoc(tmp_path / "sample.docx", "markdown")


def test_convert_document_with_pandoc_returns_stdout(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "sample.docx"
    source.write_text("placeholder", encoding="utf-8")
    tool_status = type("Status", (), {"installed": True, "path": "C:/Tools/pandoc.exe"})()

    class Completed:
        stdout = "# Converted\n"

    monkeypatch.setattr("quill.io.pandoc.subprocess.run", lambda *args, **kwargs: Completed())

    result = convert_document_with_pandoc(source, "markdown", tool_status=tool_status)

    assert result.text == "# Converted\n"
    assert result.output_kind == "markdown"
    assert result.source_path == source


def test_convert_document_with_pandoc_raises_on_error(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "sample.docx"
    source.write_text("placeholder", encoding="utf-8")
    tool_status = type("Status", (), {"installed": True, "path": "C:/Tools/pandoc.exe"})()

    def raise_error(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["pandoc"], stderr="bad input")

    monkeypatch.setattr("quill.io.pandoc.subprocess.run", raise_error)

    with pytest.raises(PandocConversionError, match="bad input"):
        convert_document_with_pandoc(source, "markdown", tool_status=tool_status)
