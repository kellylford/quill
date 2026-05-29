from __future__ import annotations

from quill.core.glow import build_audit_report, fix_text


def test_glow_audit_report_finds_markdown_heading_spacing() -> None:
    report = build_audit_report(
        "note.md",
        "#Heading\n\nSee [click here](https://example.com)",
        "markdown",
        "current document",
    )

    assert "GLOW-MD-HEADING-SPACING" in report
    assert "GLOW-MD-LINK-TEXT" in report
    assert "Automatically fixable: 1" in report


def test_glow_fix_markdown_inserts_heading_space() -> None:
    result = fix_text("#Heading\n", "markdown")

    assert result.text == "# Heading\n"
    assert any("heading markers" in fix.description.lower() for fix in result.fixes)


def test_glow_fix_html_adds_lang_and_alt() -> None:
    result = fix_text("<html><body><img src='x.png'></body></html>", "html")

    assert '<html lang="en">' in result.text
    assert 'alt=""' in result.text
    assert len(result.fixes) == 2


def test_glow_audit_report_clean_scope_reports_no_findings() -> None:
    report = build_audit_report(
        "clean.md",
        "# Heading\n\nA short paragraph.",
        "markdown",
        "selection",
    )

    assert "No deterministic GLOW findings detected" in report