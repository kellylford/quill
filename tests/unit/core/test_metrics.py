from quill.core.metrics import compute_document_stats


def test_compute_document_stats_for_empty_text() -> None:
    stats = compute_document_stats("")
    assert stats.words == 0
    assert stats.lines == 0
    assert stats.characters == 0


def test_compute_document_stats_for_multiline_text() -> None:
    stats = compute_document_stats("hello world\nsecond line")
    assert stats.words == 4
    assert stats.lines == 2
    assert stats.characters == len("hello world\nsecond line")
