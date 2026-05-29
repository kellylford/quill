from quill.core.acr import ACRMetadata, render_acr_markdown


def test_render_acr_markdown_includes_metadata() -> None:
    text = render_acr_markdown(
        ACRMetadata(
            product_name="Quill",
            product_version="1.0.0",
            report_date="2026-05-28",
            contact="team@example.com",
        )
    )
    assert "Accessibility Conformance Report (ACR)" in text
    assert "**Quill**" in text
    assert "**1.0.0**" in text
    assert "**2026-05-28**" in text
    assert "**team@example.com**" in text
