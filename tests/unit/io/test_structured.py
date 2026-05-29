import sqlite3
import zipfile
from pathlib import Path

from quill.io.pdf import PdfExtractionResult
from quill.io.structured import read_structured_document


def test_read_structured_json_formats_document(tmp_path: Path) -> None:
    target = tmp_path / "sample.json"
    target.write_text('{"b":2,"a":1}', encoding="utf-8")
    document = read_structured_document(target)
    assert document.path == target
    assert document.text == '{\n  "a": 1,\n  "b": 2\n}\n'


def test_read_structured_toml_validates_document(tmp_path: Path) -> None:
    target = tmp_path / "sample.toml"
    target.write_text('name = "quill"\n', encoding="utf-8")
    document = read_structured_document(target)
    assert document.text == 'name = "quill"\n'


def test_read_structured_xml_formats_document(tmp_path: Path) -> None:
    target = tmp_path / "sample.xml"
    target.write_text("<root><a>1</a></root>", encoding="utf-8")
    document = read_structured_document(target)
    assert "<root>" in document.text
    assert "  <a>1</a>" in document.text


def test_read_structured_csv_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "sample.csv"
    target.write_text("a,b\n1,2\n", encoding="utf-8")
    document = read_structured_document(target)
    assert document.text == "a,b\n1,2\n"


def test_read_structured_notebook_renders_cells(tmp_path: Path) -> None:
    target = tmp_path / "sample.ipynb"
    notebook = (
        '{"cells":['
        '{"cell_type":"markdown","source":["# Title\\n"]},'
        '{"cell_type":"code","source":"print(1)"}'
        "]} "
    ).strip()
    target.write_text(
        notebook,
        encoding="utf-8",
    )
    document = read_structured_document(target)
    assert "## Cell 1 (markdown)" in document.text
    assert "## Cell 2 (code)" in document.text


def test_read_structured_sqlite_renders_table_summary(tmp_path: Path) -> None:
    target = tmp_path / "sample.sqlite"
    with sqlite3.connect(target) as connection:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT)")
        cursor.execute("INSERT INTO notes (body) VALUES ('hello')")
        connection.commit()
    document = read_structured_document(target)
    assert "# SQLite Database: sample.sqlite" in document.text
    assert "- notes: 1 row(s)" in document.text


def test_read_structured_docx_extracts_text(tmp_path: Path) -> None:
    target = tmp_path / "sample.docx"
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>Hello</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>World</w:t></w:r></w:p>"
        "</w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    document = read_structured_document(target)
    assert "# DOCX Extract" in document.text
    assert "Hello" in document.text
    assert "World" in document.text


def test_read_structured_epub_extracts_text(tmp_path: Path) -> None:
    target = tmp_path / "sample.epub"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("OEBPS/chapter1.xhtml", "<html><body><p>Hello EPUB</p></body></html>")
    document = read_structured_document(target)
    assert "# EPUB:" in document.text
    assert "Hello EPUB" in document.text


def test_read_structured_odt_extracts_text(tmp_path: Path) -> None:
    target = tmp_path / "sample.odt"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("content.xml", "<office><text:p>Hello ODT</text:p></office>")
    document = read_structured_document(target)
    assert "# ODT Extract" in document.text
    assert "Hello ODT" in document.text


def test_read_structured_rtf_extracts_text(tmp_path: Path) -> None:
    target = tmp_path / "sample.rtf"
    target.write_text(r"{\rtf1\ansi Hello RTF}", encoding="latin-1")
    document = read_structured_document(target)
    assert "# RTF Extract" in document.text
    assert "Hello RTF" in document.text


def test_read_structured_pdf_attaches_metadata(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "sample.pdf"
    target.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(
        "quill.io.structured.extract_pdf_text",
        lambda _path: PdfExtractionResult(
            text="Extracted PDF text\n",
            quality_score=81,
            engine="pdfplumber",
            page_count=2,
            extracted_pages=2,
            page_scores=[81, 79],
        ),
    )
    document = read_structured_document(target)
    assert document.source_metadata["source_kind"] == "pdf"
    assert document.source_metadata["quality_score"] == 81
    assert document.source_metadata["page_count"] == 2
