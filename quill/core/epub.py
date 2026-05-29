from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EpubChapter:
    title: str
    href: str
    text: str


@dataclass(frozen=True, slots=True)
class EpubBook:
    title: str
    chapters: tuple[EpubChapter, ...]


def load_epub_book(path: Path) -> EpubBook:
    with zipfile.ZipFile(path) as archive:
        chapter_files = _chapter_files(archive)
        toc = _read_toc(archive)
        title = _read_book_title(archive) or path.stem
        chapters: list[EpubChapter] = []
        ordered = toc if toc else [(Path(name).stem, name) for name in chapter_files]
        for label, href in ordered:
            matched = _resolve_href(chapter_files, href)
            if matched is None:
                continue
            content = archive.read(matched).decode("utf-8", errors="ignore")
            text = _extract_text(content)
            chapters.append(EpubChapter(title=label or Path(matched).stem, href=matched, text=text))
    return EpubBook(title=title, chapters=tuple(chapters))


def render_epub_book(book: EpubBook) -> str:
    lines = [f"# EPUB: {book.title}", ""]
    if not book.chapters:
        lines.append("(no chapters)")
        return "\n".join(lines) + "\n"
    for index, chapter in enumerate(book.chapters, start=1):
        lines.append(f"## {index}. {chapter.title}")
        lines.append(chapter.text or "(empty chapter)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _chapter_files(archive: zipfile.ZipFile) -> list[str]:
    return sorted(
        name for name in archive.namelist() if name.lower().endswith((".xhtml", ".html", ".htm"))
    )


def _read_toc(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    toc_entries: list[tuple[str, str]] = []
    toc_names = [name for name in archive.namelist() if name.lower().endswith(".ncx")]
    for toc_name in toc_names:
        xml_text = archive.read(toc_name).decode("utf-8", errors="ignore")
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            continue
        namespace = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}
        for navpoint in root.findall(".//ncx:navPoint", namespace):
            label = "".join(
                node.text or "" for node in navpoint.findall("./ncx:navLabel/ncx:text", namespace)
            ).strip()
            content = navpoint.find("./ncx:content", namespace)
            if content is None:
                continue
            src = content.attrib.get("src", "").strip()
            if src:
                toc_entries.append((label, src))
    return toc_entries


def _read_book_title(archive: zipfile.ZipFile) -> str | None:
    opf_names = [name for name in archive.namelist() if name.lower().endswith(".opf")]
    for opf_name in opf_names:
        xml_text = archive.read(opf_name).decode("utf-8", errors="ignore")
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            continue
        namespace = {"dc": "http://purl.org/dc/elements/1.1/"}
        title_node = root.find(".//dc:title", namespace)
        if title_node is not None and title_node.text:
            candidate = title_node.text.strip()
            if candidate:
                return candidate
    return None


def _resolve_href(chapter_files: list[str], href: str) -> str | None:
    normalized = href.split("#", 1)[0].replace("\\", "/").strip()
    if not normalized:
        return None
    if normalized in chapter_files:
        return normalized
    for entry in chapter_files:
        if entry.endswith(normalized):
            return entry
    return None


def _extract_text(content: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", content)
    decoded = html.unescape(without_tags)
    return " ".join(decoded.split())
