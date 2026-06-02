from quill.core.selection import (
    block_span,
    expand_selection,
    line_span,
    paragraph_span,
    word_span,
)


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


def test_word_span_selects_current_word() -> None:
    text = "alpha beta gamma"
    start, end = word_span(text, 7)
    assert text[start:end] == "beta"


def test_word_span_on_whitespace_selects_single_character() -> None:
    text = "a  b"
    start, end = word_span(text, 2)
    assert end - start == 1


def test_expand_selection_grows_through_structural_levels() -> None:
    text = "Alpha beta gamma. Delta epsilon.\n\nSecond paragraph here."
    # Start inside the first word.
    start, end = word_span(text, 2)
    assert text[start:end] == "Alpha"

    # word -> sentence (line and sentence share bounds here, line wins first)
    result = expand_selection(text, start, end)
    assert result is not None
    start, end, scope = result
    assert scope in {"line", "sentence"}
    assert text[start:end].startswith("Alpha")

    # Keep expanding until we reach the whole document.
    scopes = [scope]
    for _ in range(10):
        result = expand_selection(text, start, end)
        if result is None:
            break
        start, end, scope = result
        scopes.append(scope)
        if scope == "document":
            break
    assert scopes[-1] == "document"
    assert (start, end) == (0, len(text))


def test_expand_selection_returns_none_when_whole_document_selected() -> None:
    text = "all of it"
    assert expand_selection(text, 0, len(text)) is None


def test_expand_selection_strictly_grows_each_step() -> None:
    text = "one two three\n\nnext block"
    start, end = word_span(text, 0)
    previous_len = end - start
    for _ in range(10):
        result = expand_selection(text, start, end)
        if result is None:
            break
        start, end, _scope = result
        assert (end - start) > previous_len
        previous_len = end - start
