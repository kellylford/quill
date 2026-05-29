from __future__ import annotations

from dataclasses import dataclass

from quill.core.a11y_regions import RegionTracker
from quill.platform.windows.sr_announce import (
    clear_transcript,
    enable_transcript_capture,
    set_transcript_path,
    transcript_entries,
)
from quill.ui.main_frame import MainFrame


@dataclass
class _DummyDialog:
    result: int

    def ShowModal(self) -> int:
        return self.result


class _DummyWx:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int]] = []

    def MessageBox(self, message: str, caption: str, style: int) -> int:
        self.calls.append((message, caption, style))
        return 7


def test_show_modal_dialog_announces_entry_and_exit() -> None:
    frame = MainFrame.__new__(MainFrame)
    frame._region_tracker = RegionTracker()
    dialog = _DummyDialog(result=42)
    set_transcript_path(None)
    clear_transcript()
    enable_transcript_capture(True)
    try:
        result = frame._show_modal_dialog(dialog, "Find")
        assert result == 42
        assert transcript_entries() == ["Entered Find dialog", "Exited Find dialog"]
    finally:
        enable_transcript_capture(False)
        clear_transcript()


def test_show_message_box_announces_entry_and_exit() -> None:
    frame = MainFrame.__new__(MainFrame)
    frame._region_tracker = RegionTracker()
    frame._wx = _DummyWx()
    set_transcript_path(None)
    clear_transcript()
    enable_transcript_capture(True)
    try:
        result = frame._show_message_box("Body", "Caption", 123)
        assert result == 7
        assert frame._wx.calls == [("Body", "Caption", 123)]
        assert transcript_entries() == ["Entered Caption dialog", "Exited Caption dialog"]
    finally:
        enable_transcript_capture(False)
        clear_transcript()
