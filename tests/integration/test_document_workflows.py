from __future__ import annotations

from pathlib import Path

from quill.core.backups import backup_document
from quill.core.document import Document
from quill.io.text import read_text_document, write_text_document


def test_text_document_roundtrip_and_backup(tmp_path: Path) -> None:
    target = tmp_path / "sample.md"
    original = Document(
        text="# Title\n\nHello world.\n",
        path=target,
        modified=True,
        encoding="utf-8",
        line_ending="\n",
    )
    write_text_document(original)
    backup_document(original)

    loaded = read_text_document(target)
    assert loaded.text == original.text
    assert loaded.path == target
    assert loaded.modified is False


def test_html_document_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "page.html"
    source = "<h1>Quill</h1>\n<p>Integration path</p>\n"
    document = Document(
        text=source,
        path=target,
        modified=True,
        encoding="utf-8",
        line_ending="\n",
    )
    write_text_document(document)

    loaded = read_text_document(target)
    assert loaded.text == source
    assert loaded.path == target
