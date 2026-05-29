from quill.core.line_ops import (
    delete_line,
    duplicate_line,
    join_with_next_line,
    move_line_down,
    move_line_up,
)


def test_duplicate_line() -> None:
    updated, cursor = duplicate_line("a\nb\nc", 2)
    assert updated == "a\nb\nb\nc"
    assert cursor > 0


def test_delete_line() -> None:
    updated, _ = delete_line("a\nb\nc", 2)
    assert updated == "a\nc"


def test_move_line_up() -> None:
    updated, _ = move_line_up("a\nb\nc", 2)
    assert updated == "b\na\nc"


def test_move_line_down() -> None:
    updated, _ = move_line_down("a\nb\nc", 2)
    assert updated == "a\nc\nb"


def test_join_with_next_line() -> None:
    updated, _ = join_with_next_line("a\nb\nc", 0)
    assert updated == "a b\nc"
