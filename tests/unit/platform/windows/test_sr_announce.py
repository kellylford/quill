from __future__ import annotations

from pathlib import Path

from quill.platform.windows import sr_announce


def setup_function() -> None:
    sr_announce.enable_transcript_capture(False)
    sr_announce.clear_transcript()
    sr_announce.set_announce_handler(lambda _message: None)
    sr_announce.set_transcript_path(None)


def test_announce_records_transcript_entries_when_enabled() -> None:
    sr_announce.enable_transcript_capture(True)
    sr_announce.announce("alpha")
    sr_announce.announce("beta")

    assert sr_announce.transcript_entries() == ["alpha", "beta"]


def test_announce_writes_transcript_file_when_path_set(tmp_path: Path) -> None:
    target = tmp_path / "a11y.log"
    sr_announce.enable_transcript_capture(True)
    sr_announce.set_transcript_path(target)
    sr_announce.announce("hello")

    assert target.read_text(encoding="utf-8") == "hello\n"
