from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from quill.core.external_tools import ExternalToolStatus, get_external_tool_status


class PandocUnavailableError(RuntimeError):
    pass


class PandocConversionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PandocConversionResult:
    text: str
    output_kind: str
    source_path: Path
    pandoc_path: str


WRITER_MAP: dict[str, str] = {
    "markdown": "gfm",
    "html": "html5",
    "plain": "plain",
}


def convert_document_with_pandoc(
    source_path: Path,
    output_kind: str,
    tool_status: ExternalToolStatus | None = None,
) -> PandocConversionResult:
    status = tool_status or get_external_tool_status("pandoc")
    if not status.installed or not status.path:
        raise PandocUnavailableError("Pandoc is not installed or bundled with Quill.")
    writer = WRITER_MAP.get(output_kind)
    if writer is None:
        raise ValueError(f"Unsupported Pandoc output kind: {output_kind}")
    command = [str(status.path), str(source_path), "--to", writer, "--wrap=none"]
    if output_kind == "html":
        command.append("--standalone")
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=True,
            text=True,
            timeout=60,
        )
    except OSError as error:
        raise PandocUnavailableError(str(error)) from error
    except subprocess.CalledProcessError as error:
        details = error.stderr.strip() or error.stdout.strip() or str(error)
        raise PandocConversionError(details) from error
    except subprocess.TimeoutExpired as error:
        raise PandocConversionError("Pandoc conversion timed out.") from error
    return PandocConversionResult(
        text=completed.stdout,
        output_kind=output_kind,
        source_path=source_path,
        pandoc_path=str(status.path),
    )
