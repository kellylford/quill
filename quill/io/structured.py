from __future__ import annotations

import csv
import html
import io
import json
import re
import sqlite3
import tomllib
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from quill.core.document import Document
from quill.core.epub import load_epub_book, render_epub_book
from quill.io.pdf import extract_pdf_text, format_pdf_document


def read_structured_document(path: Path, encoding: str = "utf-8") -> Document:
    suffix = path.suffix.lower()
    if suffix in {".sqlite", ".db"}:
        text = _format_sqlite(path)
        metadata = {"source_kind": "sqlite", "engine": "sqlite", "quality_score": 100}
    elif suffix == ".docx":
        text = _format_docx(path)
        metadata = {"source_kind": "docx", "engine": "docx", "quality_score": 100}
    elif suffix == ".epub":
        text = render_epub_book(load_epub_book(path))
        metadata = {"source_kind": "epub", "engine": "epub", "quality_score": 100}
    elif suffix == ".pdf":
        result = extract_pdf_text(path)
        text = format_pdf_document(result)
        metadata = {
            "source_kind": "pdf",
            "engine": result.engine,
            "quality_score": result.quality_score,
            "page_count": result.page_count,
            "extracted_pages": result.extracted_pages,
            "page_scores": result.page_scores,
        }
    elif suffix == ".odt":
        text = _format_odt(path)
        metadata = {"source_kind": "odt", "engine": "odt", "quality_score": 100}
    elif suffix == ".rtf":
        text = _format_rtf(path)
        metadata = {"source_kind": "rtf", "engine": "rtf", "quality_score": 100}
    else:
        raw_text = path.read_text(encoding=encoding)
        if suffix == ".json":
            text = _format_json(raw_text)
            metadata = {"source_kind": "json", "engine": "json", "quality_score": 100}
        elif suffix == ".toml":
            text = _validate_toml(raw_text)
            metadata = {"source_kind": "toml", "engine": "toml", "quality_score": 100}
        elif suffix in {".xml"}:
            text = _format_xml(raw_text)
            metadata = {"source_kind": "xml", "engine": "xml", "quality_score": 100}
        elif suffix in {".csv", ".tsv"}:
            text = _format_delimited(raw_text, delimiter="\t" if suffix == ".tsv" else ",")
            metadata = {
                "source_kind": suffix.lstrip("."),
                "engine": "delimited",
                "quality_score": 100,
            }
        elif suffix == ".ipynb":
            text = _format_notebook(raw_text)
            metadata = {"source_kind": "ipynb", "engine": "notebook", "quality_score": 100}
        else:
            text = raw_text
            metadata = {"source_kind": "text", "engine": "plain text", "quality_score": 100}

    line_ending = "\r\n" if "\r\n" in text else "\n"
    return Document(
        text=text,
        path=path,
        modified=False,
        encoding=encoding,
        line_ending=line_ending,
        source_metadata=metadata,
    )


def _format_json(text: str) -> str:
    payload = json.loads(text)
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _validate_toml(text: str) -> str:
    tomllib.loads(text)
    return text


def _format_xml(text: str) -> str:
    root = ET.fromstring(text)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode") + "\n"


def _format_delimited(text: str, delimiter: str) -> str:
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    for row in reader:
        writer.writerow(row)
    return output.getvalue()


def _format_notebook(text: str) -> str:
    payload = json.loads(text)
    cells = payload.get("cells", [])
    if not isinstance(cells, list):
        return "# Notebook\n\n(no cells)\n"
    lines = ["# Notebook", ""]
    for index, cell in enumerate(cells, start=1):
        if not isinstance(cell, dict):
            continue
        kind = str(cell.get("cell_type", "unknown"))
        source = cell.get("source", [])
        if isinstance(source, list):
            content = "".join(str(item) for item in source).strip()
        else:
            content = str(source).strip()
        lines.append(f"## Cell {index} ({kind})")
        lines.append(content or "(empty)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _format_sqlite(path: Path) -> str:
    lines = [f"# SQLite Database: {path.name}", ""]
    with sqlite3.connect(path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
        table_names = [row[0] for row in cursor.fetchall()]
        if not table_names:
            lines.append("(no user tables)")
            return "\n".join(lines) + "\n"
        for table in table_names:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cursor.fetchone()[0]
            lines.append(f"- {table}: {count} row(s)")
    lines.append("")
    return "\n".join(lines)


def _format_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ET.fromstring(xml_bytes.decode("utf-8"))
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall(".//w:p", namespace):
        parts = [
            node.text or ""
            for node in paragraph.findall(".//w:t", namespace)
            if isinstance(node.text, str)
        ]
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    lines = ["# DOCX Extract", ""]
    if paragraphs:
        lines.extend(paragraphs)
    else:
        lines.append("(no extractable text)")
    return "\n".join(lines).rstrip() + "\n"


def _format_odt(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        content = archive.read("content.xml").decode("utf-8", errors="ignore")
    text = _strip_markup(content)
    lines = ["# ODT Extract", "", text or "(no extractable text)"]
    return "\n".join(lines).rstrip() + "\n"


def _format_rtf(path: Path) -> str:
    raw = path.read_bytes().decode("latin-1", errors="ignore")
    without_controls = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", raw)
    without_hex = re.sub(r"\\'[0-9a-fA-F]{2}", "", without_controls)
    text = without_hex.replace("{", "").replace("}", "").replace("\\", "")
    normalized = " ".join(text.split())
    lines = ["# RTF Extract", "", normalized or "(no extractable text)"]
    return "\n".join(lines).rstrip() + "\n"


def _strip_markup(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = html.unescape(cleaned)
    return " ".join(cleaned.split())
