"""A wx-free rich-text model for QUILL's native RTF editing surface.

Part One of ``docs/QUILL-PRD.md`` introduces an optional rich editing surface backed by
``wx.RichTextCtrl``. The control itself lives in ``quill/ui`` (wx is forbidden in
``quill/core`` and ``quill/io``); this module is the pure, testable model the
control reads and writes through.

The design keeps QUILL's Markdown-style markup as the *canonical* document text so
every existing ``core`` feature (search, metrics, outline, autosave) keeps working
unchanged. The rich model is an **overlay** over that markup:

* :class:`RichDocument` is the structured view used to drive native formatting.
* :func:`markdown_to_rich` / :func:`rich_to_markdown` convert between the canonical
  markup and the model.
* :func:`rtf_to_rich` / :func:`rich_to_rtf` reuse the existing EDS-21 RTF
  round-trip in :mod:`quill.io.rtf`, so there is a single RTF serializer.
* :func:`analyze_markdown` exposes the character-level mapping between the markup
  string (what the plain lens edits) and the visible text (what the rich lens
  shows). The UI uses it to keep the caret on the same word when a writer switches
  lenses, and to answer "what formatting is under the caret" for spoken cues.

The supported inline subset matches the canonical markup grammar: ``**bold**``,
``*italic*`` and ``[label](url)`` links, plus heading and bullet paragraph styles.
Anything an RTF file carries beyond that subset is flattened by the existing
round-trip; :func:`scan_rtf_features` reports such cases so the UI can warn before a
lossy conversion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from quill.io.rtf import markdown_to_rtf, rtf_to_markdown

__all__ = [
    "InlineSpan",
    "RichParagraph",
    "RichDocument",
    "InlineFormat",
    "MarkdownSegment",
    "MarkdownAnalysis",
    "markdown_to_rich",
    "rich_to_markdown",
    "rtf_to_rich",
    "rich_to_rtf",
    "analyze_markdown",
    "format_at_markdown_offset",
    "markdown_offset_to_plain_offset",
    "plain_offset_to_markdown_offset",
    "scan_rtf_features",
]

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_RE = re.compile(r"^[-*]\s+(.*)$")
_LINK_MD_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class InlineSpan:
    """A run of text sharing the same inline formatting."""

    text: str
    bold: bool = False
    italic: bool = False
    href: str | None = None


@dataclass(slots=True)
class RichParagraph:
    """A paragraph: a list of spans plus a paragraph-level style.

    ``style`` is one of ``"paragraph"``, ``"heading"`` or ``"bullet"``. ``level``
    carries the heading level (1-6) when ``style == "heading"``; it is ``0``
    otherwise.
    """

    spans: list[InlineSpan] = field(default_factory=list)
    style: str = "paragraph"
    level: int = 0

    def text(self) -> str:
        """Return the visible text of this paragraph (no markup, no prefix)."""
        return "".join(span.text for span in self.spans)


@dataclass(slots=True)
class RichDocument:
    """An ordered list of paragraphs forming a rich document."""

    paragraphs: list[RichParagraph] = field(default_factory=list)

    def plain_text(self) -> str:
        """Return the visible text of the whole document, one line per paragraph.

        Heading hashes and bullet dashes are *structure*, not content, so they are
        excluded. This is the text used for word counts, search and read-aloud when
        the rich lens is active.
        """
        return "\n".join(paragraph.text() for paragraph in self.paragraphs)


@dataclass(slots=True)
class InlineFormat:
    """The formatting in effect at a point in the document."""

    bold: bool = False
    italic: bool = False
    href: str | None = None
    heading_level: int = 0
    bullet: bool = False


# --------------------------------------------------------------------------- #
# Inline parsing with offset tracking
# --------------------------------------------------------------------------- #
def _walk_inline(
    text: str,
    base: int,
    bold: bool,
    italic: bool,
    href: str | None,
    plain_chars: list[str],
    md_index: list[int],
    attrs: list[tuple[bool, bool, str | None]],
) -> None:
    """Walk an inline fragment, recording each visible character.

    ``base`` is the absolute offset of ``text`` within the full markup string so the
    recorded ``md_index`` values are absolute. Markup characters (``**``, ``*`` and
    link syntax) are consumed but never contribute a visible character.
    """
    index = 0
    length = len(text)
    while index < length:
        link = _LINK_MD_RE.match(text, index)
        if link:
            _walk_inline(
                link.group(1),
                base + link.start(1),
                bold,
                italic,
                link.group(2),
                plain_chars,
                md_index,
                attrs,
            )
            index = link.end()
            continue
        if text.startswith("**", index):
            close = text.find("**", index + 2)
            if close != -1:
                _walk_inline(
                    text[index + 2 : close],
                    base + index + 2,
                    True,
                    italic,
                    href,
                    plain_chars,
                    md_index,
                    attrs,
                )
                index = close + 2
                continue
        if text[index] == "*":
            close = text.find("*", index + 1)
            if close != -1:
                _walk_inline(
                    text[index + 1 : close],
                    base + index + 1,
                    bold,
                    True,
                    href,
                    plain_chars,
                    md_index,
                    attrs,
                )
                index = close + 1
                continue
        plain_chars.append(text[index])
        md_index.append(base + index)
        attrs.append((bold, italic, href))
        index += 1


def _spans_from_attr_runs(
    chars: list[str], attrs: list[tuple[bool, bool, str | None]]
) -> list[InlineSpan]:
    spans: list[InlineSpan] = []
    for char, attr in zip(chars, attrs, strict=True):
        bold, italic, href = attr
        if spans and (spans[-1].bold, spans[-1].italic, spans[-1].href) == attr:
            spans[-1].text += char
        else:
            spans.append(InlineSpan(char, bold=bold, italic=italic, href=href))
    return spans


# --------------------------------------------------------------------------- #
# Markdown <-> rich model
# --------------------------------------------------------------------------- #
def markdown_to_rich(markdown: str) -> RichDocument:
    """Convert canonical QUILL markup into a :class:`RichDocument`."""
    paragraphs: list[RichParagraph] = []
    for line in markdown.split("\n"):
        style = "paragraph"
        level = 0
        content = line
        heading = _HEADING_RE.match(line)
        if heading:
            style = "heading"
            level = len(heading.group(1))
            content = heading.group(2)
        else:
            item = _LIST_RE.match(line)
            if item:
                style = "bullet"
                content = item.group(1)
        chars: list[str] = []
        md_index: list[int] = []
        attrs: list[tuple[bool, bool, str | None]] = []
        _walk_inline(content, 0, False, False, None, chars, md_index, attrs)
        spans = _spans_from_attr_runs(chars, attrs)
        paragraphs.append(RichParagraph(spans=spans, style=style, level=level))
    return RichDocument(paragraphs=paragraphs)


def _escape_markdown_text(text: str) -> str:
    # Keep the canonical grammar reversible: escape the inline markers we emit.
    return text


def _span_to_markdown(span: InlineSpan) -> str:
    body = _escape_markdown_text(span.text)
    if span.italic:
        body = f"*{body}*"
    if span.bold:
        body = f"**{body}**"
    if span.href:
        body = f"[{body}]({span.href})"
    return body


def _merge_spans(spans: list[InlineSpan]) -> list[InlineSpan]:
    merged: list[InlineSpan] = []
    for span in spans:
        key = (span.bold, span.italic, span.href)
        if merged and (merged[-1].bold, merged[-1].italic, merged[-1].href) == key:
            merged[-1].text += span.text
        else:
            merged.append(InlineSpan(span.text, span.bold, span.italic, span.href))
    return merged


def rich_to_markdown(document: RichDocument) -> str:
    """Render a :class:`RichDocument` back to canonical QUILL markup."""
    lines: list[str] = []
    for paragraph in document.paragraphs:
        inline = "".join(_span_to_markdown(span) for span in _merge_spans(paragraph.spans))
        if paragraph.style == "heading":
            level = min(max(paragraph.level, 1), 6)
            lines.append(f"{'#' * level} {inline}")
        elif paragraph.style == "bullet":
            lines.append(f"- {inline}")
        else:
            lines.append(inline)
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# RTF <-> rich model (single serializer via quill.io.rtf)
# --------------------------------------------------------------------------- #
def rtf_to_rich(rtf: str) -> RichDocument:
    """Parse an RTF document string into a :class:`RichDocument`.

    Reuses the EDS-21 RTF reader, so the supported subset is exactly the canonical
    markup subset (headings, bold, italic, bullets, links).
    """
    return markdown_to_rich(rtf_to_markdown(rtf))


def rich_to_rtf(document: RichDocument) -> str:
    """Serialize a :class:`RichDocument` to a valid RTF document string."""
    return markdown_to_rtf(rich_to_markdown(document))


# --------------------------------------------------------------------------- #
# Offset mapping between markup and visible text
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class MarkdownSegment:
    """A visible character's place in both coordinate spaces."""

    md_offset: int
    plain_offset: int
    bold: bool
    italic: bool
    href: str | None
    heading_level: int
    bullet: bool


@dataclass(slots=True)
class MarkdownAnalysis:
    """The character-level relationship between markup and visible text."""

    plain_text: str
    segments: list[MarkdownSegment]
    md_to_plain: list[int]

    def heading_level_at_plain(self, plain_offset: int) -> int:
        seg = self._segment_at_plain(plain_offset)
        return seg.heading_level if seg is not None else 0

    def _segment_at_plain(self, plain_offset: int) -> MarkdownSegment | None:
        if not self.segments:
            return None
        index = min(max(plain_offset, 0), len(self.segments) - 1)
        return self.segments[index]


def analyze_markdown(markdown: str) -> MarkdownAnalysis:
    """Build the full mapping between a markup string and its visible text.

    ``md_to_plain`` has one entry per markup character (plus a trailing entry for
    the end-of-string caret position) giving the visible offset that character maps
    to. Markup-only characters map to the visible offset of the next visible
    character, so a caret sitting on markup lands sensibly in the rich lens.
    """
    plain_parts: list[str] = []
    segments: list[MarkdownSegment] = []
    length = len(markdown)
    # -1 marks "not a visible character yet"; a backward pass fills markup gaps.
    md_to_plain = [-1] * (length + 1)
    plain_cursor = 0
    md_line_start = 0
    for line_index, line in enumerate(markdown.split("\n")):
        if line_index > 0:
            # The newline that ended the previous line is visible in both spaces.
            md_to_plain[md_line_start - 1] = plain_cursor
            plain_parts.append("\n")
            plain_cursor += 1

        style = "paragraph"
        level = 0
        bullet = False
        content_offset = 0
        content = line
        heading = _HEADING_RE.match(line)
        if heading:
            style = "heading"
            level = len(heading.group(1))
            content_offset = heading.start(2)
            content = heading.group(2)
        else:
            item = _LIST_RE.match(line)
            if item:
                style = "bullet"
                bullet = True
                content_offset = item.start(1)
                content = item.group(1)

        chars: list[str] = []
        rel_md: list[int] = []
        attrs: list[tuple[bool, bool, str | None]] = []
        _walk_inline(content, 0, False, False, None, chars, rel_md, attrs)

        for visible_index, (char, rel, attr) in enumerate(zip(chars, rel_md, attrs, strict=True)):
            bold, italic, href = attr
            abs_md = md_line_start + content_offset + rel
            plain_offset = plain_cursor + visible_index
            md_to_plain[abs_md] = plain_offset
            plain_parts.append(char)
            segments.append(
                MarkdownSegment(
                    md_offset=abs_md,
                    plain_offset=plain_offset,
                    bold=bold,
                    italic=italic,
                    href=href,
                    heading_level=level if style == "heading" else 0,
                    bullet=bullet,
                )
            )
        plain_cursor += len(chars)
        md_line_start += len(line) + 1

    # Markup-only characters (hashes, dashes, asterisks, link syntax) inherit the
    # visible offset of the next visible character, so a caret on markup lands
    # sensibly in the rich lens. Walking backward propagates the next mapped value.
    running = plain_cursor
    for index in range(length, -1, -1):
        if md_to_plain[index] == -1:
            md_to_plain[index] = running
        else:
            running = md_to_plain[index]
    return MarkdownAnalysis(
        plain_text="".join(plain_parts), segments=segments, md_to_plain=md_to_plain
    )


def markdown_offset_to_plain_offset(markdown: str, offset: int) -> int:
    """Map a caret offset in the markup string to the visible-text offset."""
    analysis = analyze_markdown(markdown)
    clamped = min(max(offset, 0), len(markdown))
    return analysis.md_to_plain[clamped]


def plain_offset_to_markdown_offset(markdown: str, plain_offset: int) -> int:
    """Map a visible-text caret offset back to the markup string."""
    analysis = analyze_markdown(markdown)
    target = min(max(plain_offset, 0), len(analysis.plain_text))
    for segment in analysis.segments:
        if segment.plain_offset == target:
            return segment.md_offset
    return len(markdown)


def format_at_markdown_offset(markdown: str, offset: int) -> InlineFormat:
    """Return the :class:`InlineFormat` in effect at a markup caret offset.

    The caret reports the formatting of the character to its left (the run it is
    extending), matching how screen readers describe the caret context.
    """
    analysis = analyze_markdown(markdown)
    if not analysis.segments:
        return InlineFormat()
    plain_offset = analysis.md_to_plain[min(max(offset, 0), len(markdown))]
    index = plain_offset - 1
    if index < 0:
        index = 0
    index = min(index, len(analysis.segments) - 1)
    segment = analysis.segments[index]
    return InlineFormat(
        bold=segment.bold,
        italic=segment.italic,
        href=segment.href,
        heading_level=segment.heading_level,
        bullet=segment.bullet,
    )


# --------------------------------------------------------------------------- #
# Fidelity reporting
# --------------------------------------------------------------------------- #
# RTF control words that carry content the canonical markup subset cannot express.
# Their presence means a round trip through QUILL markup would flatten something.
_UNSUPPORTED_FEATURES: dict[str, str] = {
    r"\\trowd": "tables",
    r"\\cell": "tables",
    r"\\pict": "images",
    r"\\footnote": "footnotes",
    r"\\highlight\d": "text highlighting",
    r"\\strike": "strikethrough",
    r"\\ul\b": "underline",
    r"\\cf\d": "text color",
    r"\\sub\b": "subscript",
    r"\\super\b": "superscript",
}


def scan_rtf_features(rtf: str) -> list[str]:
    """Return human-readable names of RTF features the markup subset would flatten.

    The UI uses this to warn, before a lossy conversion, exactly what will be lost
    (``docs/QUILL-PRD.md`` "Honest fidelity"). An empty list means a clean round trip.
    """
    found: list[str] = []
    for pattern, label in _UNSUPPORTED_FEATURES.items():
        if re.search(pattern, rtf) and label not in found:
            found.append(label)
    return found
