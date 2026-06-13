"""Render Ask Quill chat content for insertion into the document.

Pure and wx-free so it is unit-tested without a UI: turns a single message or a
whole transcript into plain text, Markdown, or HTML, which the chat dialog drops
into the document in the format the user picks.
"""

from __future__ import annotations

from collections.abc import Iterable
from html import escape

FORMATS: tuple[str, ...] = ("plain", "markdown", "html")


def normalize_format(fmt: str) -> str:
    """Return a supported format id, defaulting to ``plain``."""
    value = (fmt or "").strip().lower()
    return value if value in FORMATS else "plain"


def render_message(speaker: str, text: str, fmt: str) -> str:
    """Render one message. An empty *speaker* renders just the content."""
    fmt = normalize_format(fmt)
    name = (speaker or "").strip()
    body = text or ""
    if fmt == "html":
        safe_body = escape(body).replace("\n", "<br>\n")
        if name:
            return f"<p><strong>{escape(name)}:</strong> {safe_body}</p>"
        return f"<p>{safe_body}</p>"
    if fmt == "markdown":
        return f"**{name}:** {body}" if name else body
    # plain
    return f"{name}: {body}" if name else body


def render_transcript(messages: Iterable[tuple[str, str]], fmt: str) -> str:
    """Render a whole transcript of ``(speaker, text)`` turns."""
    fmt = normalize_format(fmt)
    rendered = [render_message(speaker, text, fmt) for speaker, text in messages]
    if not rendered:
        return ""
    separator = "\n" if fmt == "html" else "\n\n"
    return separator.join(rendered) + "\n"
