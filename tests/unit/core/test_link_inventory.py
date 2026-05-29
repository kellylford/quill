from __future__ import annotations

from quill.core.link_inventory import collect_link_inventory, render_link_inventory_report


def test_collect_link_inventory_captures_markdown_and_html_entries() -> None:
    text = (
        "[Docs](https://example.com/docs)\n"
        "![Chart](images/chart.png)\n"
        '<a href="https://example.com/help">Help</a>\n'
        '<img src="images/logo.png" alt="Company logo" />\n'
    )
    inventory = collect_link_inventory(text)
    assert len(inventory.links) == 2
    assert len(inventory.images) == 2
    assert inventory.links[0].target == "https://example.com/docs"
    assert inventory.images[1].alt_text == "Company logo"


def test_render_link_inventory_report_marks_missing_alt_text() -> None:
    inventory = collect_link_inventory('<img src="missing-alt.png" />')
    report = render_link_inventory_report(inventory)
    assert "missing-alt.png" in report
    assert "(missing alt text)" in report
