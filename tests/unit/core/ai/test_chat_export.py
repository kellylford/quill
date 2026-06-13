from __future__ import annotations

from quill.core.ai.chat_export import (
    normalize_format,
    render_message,
    render_transcript,
)


def test_normalize_format_defaults_to_plain() -> None:
    assert normalize_format("nonsense") == "plain"
    assert normalize_format("HTML") == "html"
    assert normalize_format("") == "plain"


def test_render_message_plain_with_and_without_speaker() -> None:
    assert render_message("Quill", "hello", "plain") == "Quill: hello"
    assert render_message("", "hello", "plain") == "hello"


def test_render_message_markdown() -> None:
    assert render_message("Quill", "hello", "markdown") == "**Quill:** hello"
    assert render_message("", "hello", "markdown") == "hello"


def test_render_message_html_escapes() -> None:
    out = render_message("You", "a < b & c", "html")
    assert "<strong>You:</strong>" in out
    assert "a &lt; b &amp; c" in out
    assert out.startswith("<p>") and out.endswith("</p>")


def test_render_message_html_newlines_to_br() -> None:
    out = render_message("", "line1\nline2", "html")
    assert "line1<br>\nline2" in out


def test_render_transcript_plain() -> None:
    out = render_transcript([("You", "hi"), ("Quill", "hello")], "plain")
    assert out == "You: hi\n\nQuill: hello\n"


def test_render_transcript_markdown() -> None:
    out = render_transcript([("You", "hi"), ("Quill", "hello")], "markdown")
    assert out == "**You:** hi\n\n**Quill:** hello\n"


def test_render_transcript_html_joins_with_newline() -> None:
    out = render_transcript([("You", "hi"), ("Quill", "hello")], "html")
    assert out == "<p><strong>You:</strong> hi</p>\n<p><strong>Quill:</strong> hello</p>\n"


def test_render_transcript_empty_is_empty_string() -> None:
    assert render_transcript([], "plain") == ""
    assert render_transcript([], "html") == ""
