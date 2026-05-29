from quill.core.transforms import (
    to_lower,
    to_sentence_case,
    to_title,
    to_toggle_case,
    to_upper,
)


def test_to_upper() -> None:
    assert to_upper("Abc") == "ABC"


def test_to_lower() -> None:
    assert to_lower("AbC") == "abc"


def test_to_title() -> None:
    assert to_title("hello world") == "Hello World"


def test_to_toggle_case() -> None:
    assert to_toggle_case("AbC") == "aBc"


def test_to_sentence_case() -> None:
    assert to_sentence_case("hello world. second line!") == "Hello world. Second line!"
