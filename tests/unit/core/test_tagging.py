from quill.core.tagging import (
    build_html_code_block,
    build_html_insertion,
    build_html_table,
    build_markdown_code_block,
    build_markdown_insertion,
    build_markdown_table,
    parse_attribute_pairs,
)


def test_parse_attribute_pairs_supports_key_value_and_boolean() -> None:
    parsed = parse_attribute_pairs("class=note; id=main; disabled")
    assert parsed == {"class": "note", "id": "main", "disabled": ""}


def test_build_html_insertion_wraps_selected_text() -> None:
    result = build_html_insertion("strong", "hello", {"class": "callout"})
    assert result.inserted_text == '<strong class="callout">hello</strong>'
    assert result.caret_offset == len(result.inserted_text)


def test_build_html_insertion_for_void_tag() -> None:
    result = build_html_insertion("img", "", {"src": "image.png", "alt": "Sample"})
    assert result.inserted_text == '<img src="image.png" alt="Sample" />'


def test_build_markdown_link_uses_target() -> None:
    result = build_markdown_insertion("Link", "docs", "https://example.com")
    assert result.inserted_text == "[docs](https://example.com)"


def test_build_markdown_table_template() -> None:
    result = build_markdown_insertion("Table", "")
    assert "| Column 1 | Column 2 |" in result.inserted_text


def test_build_markdown_table_with_custom_dimensions() -> None:
    result = build_markdown_table(3, 4, include_header=True)
    assert result.inserted_text.count("| --- | --- | --- | --- |") == 1
    assert result.inserted_text.count("|  |  |  |  |") == 3


def test_build_html_table_with_header() -> None:
    result = build_html_table(2, 3, include_header=True)
    assert "<thead>" in result.inserted_text
    assert result.inserted_text.count("<th>") == 3
    assert result.inserted_text.count("<td></td>") == 6


def test_build_markdown_code_block_with_language_hint() -> None:
    result = build_markdown_code_block("print('hi')", language_hint="python")
    assert result.inserted_text.startswith("```python\n")


def test_build_html_code_block_with_language_hint() -> None:
    result = build_html_code_block("console.log('hi')", language_hint="javascript")
    assert '<code class="language-javascript">' in result.inserted_text


def test_build_markdown_bold_without_selection_inserts_pair() -> None:
    result = build_markdown_insertion("Bold", "")
    assert result.inserted_text == "****"
    assert result.caret_offset == 2


def test_build_markdown_italic_without_selection_inserts_pair() -> None:
    result = build_markdown_insertion("Italic", "")
    assert result.inserted_text == "**"
    assert result.caret_offset == 1
