from quill.core.bookmarks import bookmark_names, bookmark_position, set_bookmark


def test_set_bookmark_adds_or_replaces_position() -> None:
    bookmarks: dict[str, int] = {}
    bookmarks = set_bookmark(bookmarks, "Intro", 12)
    bookmarks = set_bookmark(bookmarks, "Intro", 20)
    assert bookmark_position(bookmarks, "Intro") == 20


def test_set_bookmark_ignores_blank_name() -> None:
    bookmarks = set_bookmark({}, "   ", 10)
    assert bookmarks == {}


def test_bookmark_names_sorted_case_insensitive() -> None:
    bookmarks = {"zeta": 1, "Alpha": 2}
    assert bookmark_names(bookmarks) == ["Alpha", "zeta"]
