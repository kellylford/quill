from quill.core.selection import block_span, line_span, paragraph_span


def test_line_span_selects_current_line() -> None:
    text = "first\nsecond\nthird"
    start, end = line_span(text, 7)
    assert text[start:end] == "second"


def test_line_span_handles_end_of_document() -> None:
    text = "only"
    start, end = line_span(text, 50)
    assert (start, end) == (0, 4)


def test_paragraph_span_selects_block_between_blank_lines() -> None:
    text = "alpha\nbeta\n\none\ntwo\n\nomega"
    start, end = paragraph_span(text, text.index("o", 8))
    assert text[start:end] == "one\ntwo"


def test_paragraph_span_handles_single_paragraph() -> None:
    text = "single paragraph"
    start, end = paragraph_span(text, 4)
    assert text[start:end] == text


def test_block_span_selects_contiguous_non_blank_lines() -> None:
    text = "alpha\nbeta\n\ngamma\ndelta\n\nomega"
    start, end = block_span(text, text.index("a", 13))
    assert text[start:end] == "gamma\ndelta"
