from __future__ import annotations

import zipfile
from pathlib import Path

from quill.core.epub import load_epub_book, render_epub_book


def test_load_epub_book_reads_ncx_order(tmp_path: Path) -> None:
    target = tmp_path / "book.epub"
    toc = (
        '<?xml version="1.0"?>'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/">'
        "<navMap>"
        '<navPoint id="a">'
        "<navLabel><text>Start</text></navLabel>"
        '<content src="text/ch1.xhtml"/>'
        "</navPoint>"
        "</navMap>"
        "</ncx>"
    )
    chapter = "<html><body><h1>One</h1><p>Hello EPUB</p></body></html>"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("toc.ncx", toc)
        archive.writestr("text/ch1.xhtml", chapter)
    book = load_epub_book(target)
    assert book.chapters[0].title == "Start"
    assert "Hello EPUB" in book.chapters[0].text


def test_render_epub_book_includes_chapter_titles(tmp_path: Path) -> None:
    target = tmp_path / "book.epub"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("chapters/one.xhtml", "<html><body><p>First</p></body></html>")
    book = load_epub_book(target)
    report = render_epub_book(book)
    assert "# EPUB:" in report
    assert "## 1." in report
