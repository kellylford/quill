from __future__ import annotations

from pathlib import Path

from quill.core.ai.vision import (
    DEFAULT_IMAGE_DESCRIPTION_PROMPT,
    build_image_description_body,
    image_mime_for_path,
)

_B64 = "aGVsbG8="  # "hello"


def test_image_mime_for_path_known_suffixes() -> None:
    assert image_mime_for_path(Path("x.png")) == "image/png"
    assert image_mime_for_path(Path("x.JPG")) == "image/jpeg"
    assert image_mime_for_path(Path("x.jpeg")) == "image/jpeg"
    assert image_mime_for_path(Path("x.gif")) == "image/gif"
    assert image_mime_for_path(Path("x.webp")) == "image/webp"
    assert image_mime_for_path(Path("x.tiff")) == "image/tiff"


def test_image_mime_for_path_defaults_to_png() -> None:
    assert image_mime_for_path(Path("x.unknown")) == "image/png"


def test_default_prompt_mentions_blind_reader() -> None:
    assert "blind reader" in DEFAULT_IMAGE_DESCRIPTION_PROMPT.lower()


def test_openai_body_uses_image_url_data_uri() -> None:
    body = build_image_description_body(
        "openai", "gpt-4o", "Describe", _B64, "image/png", max_tokens=128
    )
    assert body["model"] == "gpt-4o"
    assert body["max_tokens"] == 128
    content = body["messages"][0]["content"]  # type: ignore[index]
    assert content[0] == {"type": "text", "text": "Describe"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"] == f"data:image/png;base64,{_B64}"


def test_claude_body_uses_base64_source_block() -> None:
    body = build_image_description_body(
        "claude", "claude-3-5-sonnet", "Describe", _B64, "image/jpeg"
    )
    assert body["model"] == "claude-3-5-sonnet"
    content = body["messages"][0]["content"]  # type: ignore[index]
    image_part = content[1]
    assert image_part["type"] == "image"
    assert image_part["source"] == {
        "type": "base64",
        "media_type": "image/jpeg",
        "data": _B64,
    }


def test_gemini_body_uses_inline_data() -> None:
    body = build_image_description_body("gemini", "gemini-1.5-pro", "Describe", _B64, "image/png")
    parts = body["contents"][0]["parts"]  # type: ignore[index]
    assert parts[0] == {"text": "Describe"}
    assert parts[1]["inline_data"] == {"mime_type": "image/png", "data": _B64}


def test_ollama_body_attaches_images_array() -> None:
    body = build_image_description_body("ollama", "llava", "Describe", _B64, "image/png")
    message = body["messages"][0]  # type: ignore[index]
    assert message["content"] == "Describe"
    assert message["images"] == [_B64]
    assert body["stream"] is False


def test_provider_match_is_case_insensitive() -> None:
    body = build_image_description_body("  Claude  ", "claude-3", "Describe", _B64, "image/png")
    assert body["messages"][0]["content"][1]["type"] == "image"  # type: ignore[index]
