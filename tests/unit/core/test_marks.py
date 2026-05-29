from quill.core.marks import MarkRing, line_column_for_position


def test_mark_ring_set_and_pop() -> None:
    ring = MarkRing(max_size=3)
    ring.set_mark(5)
    ring.set_mark(10)
    assert ring.pop_mark() == 10
    assert ring.pop_mark() == 5
    assert ring.pop_mark() is None


def test_mark_ring_exchange_point_and_mark() -> None:
    ring = MarkRing()
    ring.set_mark(8)
    target = ring.exchange_point_and_mark(3)
    assert target == 8
    assert ring.list_marks() == (3,)


def test_mark_ring_deduplicates_and_caps_size() -> None:
    ring = MarkRing(max_size=2)
    ring.set_mark(1)
    ring.set_mark(2)
    ring.set_mark(1)
    ring.set_mark(3)
    assert ring.list_marks() == (1, 3)


def test_line_column_for_position() -> None:
    text = "one\ntwo\nthree"
    assert line_column_for_position(text, 5) == (2, 2)
