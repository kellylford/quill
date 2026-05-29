from quill.core.url_ops import format_content_length, is_cross_host_redirect


def test_is_cross_host_redirect_detects_host_change() -> None:
    assert is_cross_host_redirect("https://a.example.com/x", "https://b.example.com/y")
    assert not is_cross_host_redirect("https://a.example.com/x", "https://a.example.com/y")


def test_format_content_length_human_readable() -> None:
    assert format_content_length(None) == "unknown size"
    assert format_content_length(700) == "700 B"
    assert format_content_length(2048) == "2.0 KB"
    assert format_content_length(2 * 1024 * 1024) == "2.0 MB"
