from quill.core.navigation import (
    next_block_start,
    next_heading_start,
    page_start_for_number,
    page_starts,
    parse_line_column,
    previous_block_start,
    previous_heading_start,
)


def test_page_starts_from_form_feed_markers() -> None:
    text = "page1\fpage2\fpage3"
    assert page_starts(text) == [0, 6, 12]


def test_page_start_for_number_validates_range() -> None:
    text = "a\fb"
    assert page_start_for_number(text, 1) == 0
    assert page_start_for_number(text, 2) == 2
    assert page_start_for_number(text, 3) is None


def test_markdown_heading_navigation() -> None:
    text = "# One\npara\n\n## Two\nbody\n\n### Three\n"
    second = text.index("## Two")
    third = text.index("### Three")
    assert next_heading_start(text, 0, "markdown") == second
    assert next_heading_start(text, second + 1, "markdown") == third
    assert previous_heading_start(text, third, "markdown") == second
    assert previous_heading_start(text, 12, "markdown") == 0


def test_html_heading_navigation() -> None:
    text = "<h1>One</h1>\n<p>x</p>\n\n<h2 class='a'>Two</h2>\n"
    second = text.index("<h2")
    assert next_heading_start(text, 0, "html") == second
    assert previous_heading_start(text, second, "html") == 0


def test_block_navigation() -> None:
    text = "first\nline\n\nsecond\n\nthird\n"
    second = text.index("second")
    third = text.index("third")
    assert next_block_start(text, 0) == second
    assert next_block_start(text, second) == third
    assert previous_block_start(text, third) == second


def test_parse_line_column_supports_optional_column() -> None:
    assert parse_line_column("42") == (42, None)
    assert parse_line_column("42,7") == (42, 7)
