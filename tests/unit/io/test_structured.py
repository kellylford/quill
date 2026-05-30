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


def test_read_structured_pptx_extracts_headings_lists_tables_and_notes(tmp_path: Path) -> None:
    target = tmp_path / "sample.pptx"
    slide_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        "<p:cSld><p:spTree>"
        "<p:sp><p:nvSpPr><p:nvPr><p:ph type=\"title\"/></p:nvPr></p:nvSpPr>"
        "<p:txBody><a:p><a:r><a:t>Slide Title</a:t></a:r></a:p></p:txBody></p:sp>"
        "<p:sp><p:nvSpPr><p:nvPr><p:ph type=\"body\"/></p:nvPr></p:nvSpPr><p:txBody>"
        "<a:p><a:pPr lvl=\"0\"/><a:r><a:t>Top item</a:t></a:r></a:p>"
        "<a:p><a:pPr lvl=\"1\"/><a:r><a:t>Nested item</a:t></a:r></a:p>"
        "</p:txBody></p:sp>"
        "<p:graphicFrame><a:graphic><a:graphicData>"
        "<a:tbl><a:tr><a:tc><a:txBody><a:p><a:r><a:t>H1</a:t></a:r></a:p></a:txBody></a:tc>"
        "<a:tc><a:txBody><a:p><a:r><a:t>H2</a:t></a:r></a:p></a:txBody></a:tc></a:tr>"
        "<a:tr><a:tc><a:txBody><a:p><a:r><a:t>A</a:t></a:r></a:p></a:txBody></a:tc>"
        "<a:tc><a:txBody><a:p><a:r><a:t>B</a:t></a:r></a:p></a:txBody></a:tc></a:tr>"
        "</a:tbl></a:graphicData></a:graphic></p:graphicFrame>"
        "</p:spTree></p:cSld></p:sld>"
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" '
        'Target="../notesSlides/notesSlide1.xml"/>'
        "</Relationships>"
    )
    notes_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:notes xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        "<p:cSld><p:spTree><p:sp><p:txBody>"
        "<a:p><a:r><a:t>Speaker note line</a:t></a:r></a:p>"
        "</p:txBody></p:sp></p:spTree></p:cSld></p:notes>"
    )
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide_xml)
        archive.writestr("ppt/slides/_rels/slide1.xml.rels", rels_xml)
        archive.writestr("ppt/notesSlides/notesSlide1.xml", notes_xml)

    document = read_structured_document(target)

    assert "# Slide Title" in document.text
    assert "- Top item" in document.text
    assert "  - Nested item" in document.text
    assert "| H1 | H2 |" in document.text
    assert "## Notes" in document.text
    assert "Speaker note line" in document.text


def test_read_structured_pages_gracefully_handles_missing_deps(tmp_path: Path, monkeypatch) -> None:
    """Test that Pages import shows a helpful message when dependencies are missing."""
    target = tmp_path / "sample.pages"
    # Create a minimal ZIP file (Pages files are ZIPs)
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("Index/Document.iwa", b"fake iwa data")
    
    # Mock both Pages readers to fail (simulating missing deps)
    from unittest.mock import Mock
    from quill.io import pages
    
    monkeypatch.setattr(pages, "_read_pages_via_iwa", Mock(side_effect=ImportError("keynote-parser not available")))
    monkeypatch.setattr(pages, "_read_pages_via_libreoffice", Mock(side_effect=ImportError("markitdown not available")))
    
    document = read_structured_document(target)
    
    assert "Pages import not available" in document.text
    assert "pip install keynote-parser" in document.text
    assert "pip install markitdown" in document.text
    assert document.source_metadata["source_kind"] == "pages"
    assert document.source_metadata["quality_score"] == 0
