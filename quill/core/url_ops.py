from __future__ import annotations

from urllib.parse import urlparse


def host_for_url(url: str) -> str:
    return urlparse(url).netloc


def is_cross_host_redirect(original_url: str, resolved_url: str) -> bool:
    original_host = host_for_url(original_url).lower()
    resolved_host = host_for_url(resolved_url).lower()
    if not original_host or not resolved_host:
        return False
    return original_host != resolved_host


def format_content_length(content_length: int | None) -> str:
    if content_length is None or content_length < 0:
        return "unknown size"
    if content_length < 1024:
        return f"{content_length} B"
    if content_length < 1024 * 1024:
        return f"{content_length / 1024:.1f} KB"
    return f"{content_length / (1024 * 1024):.1f} MB"
