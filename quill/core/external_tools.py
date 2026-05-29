from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExternalToolDefinition:
    tool_id: str
    name: str
    description: str
    capabilities: tuple[str, ...]
    bundled_subpath: str
    executable_names: tuple[str, ...]
    website_url: str
    install_command: str


@dataclass(frozen=True, slots=True)
class ExternalToolStatus:
    definition: ExternalToolDefinition
    installed: bool
    path: str | None
    source: str
    version: str | None

    @property
    def tool_id(self) -> str:
        return self.definition.tool_id

    @property
    def name(self) -> str:
        return self.definition.name


TOOL_DEFINITIONS: tuple[ExternalToolDefinition, ...] = (
    ExternalToolDefinition(
        tool_id="pandoc",
        name="Pandoc",
        description=(
            "General-purpose document conversion engine for moving between Word, "
            "Markdown, HTML, EPUB, and many other text-centric formats."
        ),
        capabilities=(
            "Convert Word, Markdown, HTML, EPUB, and more into Quill-readable text",
            "Open Markdown, HTML, and plain-text conversion results as Quill tabs",
            "Prepare documents for downstream GLOW text workflows",
        ),
        bundled_subpath=r"pandoc\pandoc.exe",
        executable_names=("pandoc.exe", "pandoc"),
        website_url="https://pandoc.org/",
        install_command="winget install --id JohnMacFarlane.Pandoc -e",
    ),
    ExternalToolDefinition(
        tool_id="tesseract",
        name="Tesseract OCR",
        description=(
            "Local optical character recognition for screenshots, scans, and image-heavy "
            "document workflows."
        ),
        capabilities=(
            "OCR images into editable Quill text",
            "Improve low-confidence scanned document workflows",
            "Extend PDF and image ingestion without cloud services",
        ),
        bundled_subpath="tesseract\tesseract.exe",
        executable_names=("tesseract.exe", "tesseract"),
        website_url="https://tesseract-ocr.github.io/",
        install_command="winget install --id UB-Mannheim.TesseractOCR -e",
    ),
    ExternalToolDefinition(
        tool_id="libreoffice",
        name="LibreOffice",
        description=(
            "Optional office conversion helper for legacy and edge-case document imports."
        ),
        capabilities=(
            "Improve compatibility for older office formats",
            "Provide a stronger conversion fallback path for difficult documents",
        ),
        bundled_subpath=r"libreoffice\program\soffice.exe",
        executable_names=("soffice.exe", "soffice", "libreoffice"),
        website_url="https://www.libreoffice.org/",
        install_command="winget install --id TheDocumentFoundation.LibreOffice -e",
    ),
    ExternalToolDefinition(
        tool_id="ghostscript",
        name="Ghostscript",
        description=(
            "PDF and PostScript helper for advanced render and conversion workflows."
        ),
        capabilities=(
            "Improve PDF-related conversion pipelines",
            "Support print-oriented and PostScript-heavy workflows",
        ),
        bundled_subpath=r"ghostscript\bin\gswin64c.exe",
        executable_names=("gswin64c.exe", "gswin32c.exe", "gs"),
        website_url="https://ghostscript.com/",
        install_command="winget install --id ArtifexSoftware.GhostScript -e",
    ),
)


def get_external_tool_statuses() -> list[ExternalToolStatus]:
    return [detect_tool(definition) for definition in TOOL_DEFINITIONS]


def get_external_tool_status(tool_id: str) -> ExternalToolStatus:
    for definition in TOOL_DEFINITIONS:
        if definition.tool_id == tool_id:
            return detect_tool(definition)
    raise KeyError(tool_id)


def detect_tool(definition: ExternalToolDefinition) -> ExternalToolStatus:
    bundled = _bundled_tool_path(definition)
    if bundled is not None:
        return ExternalToolStatus(
            definition=definition,
            installed=True,
            path=str(bundled),
            source="bundled",
            version=_tool_version(bundled, definition.tool_id),
        )
    for executable_name in definition.executable_names:
        discovered = shutil.which(executable_name)
        if discovered:
            return ExternalToolStatus(
                definition=definition,
                installed=True,
                path=discovered,
                source="system",
                version=_tool_version(Path(discovered), definition.tool_id),
            )
    return ExternalToolStatus(
        definition=definition,
        installed=False,
        path=None,
        source="missing",
        version=None,
    )


def format_tool_status_report(statuses: list[ExternalToolStatus] | None = None) -> str:
    current_statuses = statuses or get_external_tool_statuses()
    lines = ["External Tools and Format Support", ""]
    for status in current_statuses:
        lines.append(f"## {status.name}")
        lines.append(status.definition.description)
        lines.append("")
        if status.installed:
            lines.append(f"Status: installed via {status.source}")
            if status.path:
                lines.append(f"Path: {status.path}")
            if status.version:
                lines.append(f"Version: {status.version}")
        else:
            lines.append("Status: not installed")
            lines.append(f"Install command: {status.definition.install_command}")
        lines.append("Capabilities:")
        for capability in status.definition.capabilities:
            lines.append(f"- {capability}")
        lines.append(f"Learn more: {status.definition.website_url}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def copyable_install_command(tool_id: str) -> str:
    return get_external_tool_status(tool_id).definition.install_command


def _bundled_tool_path(definition: ExternalToolDefinition) -> Path | None:
    app_root = os.environ.get("QUILL_APP_ROOT", "").strip()
    if app_root:
        candidate = Path(app_root) / "tools" / definition.bundled_subpath
        if candidate.exists():
            return candidate.resolve()
    return None


def _tool_version(executable: Path, tool_id: str) -> str | None:
    command = [str(executable), "--version"]
    if tool_id == "ghostscript":
        command = [str(executable), "-v"]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0].strip() if output else None
