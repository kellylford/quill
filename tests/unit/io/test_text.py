from pathlib import Path

import pytest

from quill.core.document import Document
from quill.io.text import read_text_document, write_text_document


def test_read_text_document(tmp_path: Path) -> None:
    target = tmp_path / "example.txt"
    target.write_text("hello\nworld\n", encoding="utf-8")

    document = read_text_document(target)
    assert document.text == "hello\nworld\n"
    assert document.path == target
    assert document.modified is False


def test_write_text_document(tmp_path: Path) -> None:
    target = tmp_path / "save.txt"
    document = Document(text="line1\nline2", line_ending="\r\n")

    write_text_document(document, target)
    assert target.read_text(encoding="utf-8") == "line1\nline2"
    assert document.path == target
    assert document.modified is False


def test_write_text_document_requires_path() -> None:
    document = Document(text="x")
    with pytest.raises(ValueError):
        write_text_document(document)
