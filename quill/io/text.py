from __future__ import annotations

from pathlib import Path

from quill.core.document import Document


def read_text_document(path: Path, encoding: str = "utf-8") -> Document:
    text = path.read_text(encoding=encoding)
    line_ending = "\r\n" if "\r\n" in text else "\n"
    return Document(
        text=text,
        path=path,
        modified=False,
        encoding=encoding,
        line_ending=line_ending,
        source_metadata={"source_kind": "text", "engine": "plain text", "quality_score": 100},
    )


def write_text_document(document: Document, path: Path | None = None) -> Path:
    target_path = path or document.path
    if target_path is None:
        raise ValueError("A path is required to save this document.")

    text = _normalize_line_endings(document.text, document.line_ending)
    with target_path.open("w", encoding=document.encoding, newline="") as file_handle:
        file_handle.write(text)
    document.mark_saved(target_path)
    return target_path


def _normalize_line_endings(text: str, line_ending: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if line_ending == "\n":
        return normalized
    return normalized.replace("\n", line_ending)
