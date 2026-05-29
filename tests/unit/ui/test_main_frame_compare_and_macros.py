from __future__ import annotations

from pathlib import Path

from quill.core.document import Document
from quill.ui.main_frame import MainFrame


class _Editor:
    def __init__(self, text: str) -> None:
        self._text = text
        self._insertion_point = 0
        self.selection = (0, 0)

    def GetValue(self) -> str:
        return self._text

    def SetInsertionPoint(self, position: int) -> None:
        self._insertion_point = position

    def SetSelection(self, start: int, end: int) -> None:
        self.selection = (start, end)


class _MacroSink:
    def __init__(self) -> None:
        self.steps: list[str] = []

    def record(self, command_id: str) -> None:
        self.steps.append(command_id)


class _Event:
    def __init__(self, menu_id: int) -> None:
        self._menu_id = menu_id
        self.skipped = False

    def GetId(self) -> int:
        return self._menu_id

    def Skip(self) -> None:
        self.skipped = True


def _build_frame(text: str = "alpha\nbeta\n") -> MainFrame:
    frame = MainFrame.__new__(MainFrame)
    frame.document = Document(path=Path("note.md"), text=text)
    frame.editor = _Editor(text)
    frame._status_message = "Ready"
    frame._compare_session = None
    frame._compare_ignore_trailing_spaces = True
    frame._compare_ignore_line_endings = True
    frame._set_status = lambda message: setattr(frame, "_status_message", message)
    return frame


def test_macro_recording_ignores_macro_control_commands() -> None:
    frame = _build_frame()
    frame.macros = _MacroSink()

    frame._record_macro_step("tools.play_last_macro")
    frame._record_macro_step("edit.find")

    assert frame.macros.steps == ["edit.find"]


def test_menu_command_activity_records_known_command_id() -> None:
    frame = _build_frame()
    captured: list[str] = []
    frame._command_to_menu_id_map = lambda: {"edit.find": 100}  # type: ignore[assignment]
    frame._record_macro_step = captured.append  # type: ignore[assignment]

    event = _Event(menu_id=100)
    frame._on_menu_command_activity(event)

    assert captured == ["edit.find"]
    assert event.skipped is True


def test_compare_session_builds_and_navigates_differences() -> None:
    frame = _build_frame("line1\nline2\n")

    started = frame._start_compare_session(
        [("left.txt", "line1\nline2\n"), ("right.txt", "line1\nLINE2\n")]
    )

    assert started is True
    assert frame._compare_session is not None
    assert len(frame._compare_session.groups) == 1
    assert frame._compare_session.groups[0].kind == "case-only"
    frame.compare_next_difference()
    assert "Difference 1 of 1" in frame._status_message


def test_compare_summary_contains_document_names_and_differences() -> None:
    frame = _build_frame("line1\nline2\n")
    frame._start_compare_session([("left.txt", "line1\nline2\n"), ("right.txt", "line1\nlineX\n")])
    session = frame._compare_session
    assert session is not None

    summary = frame._build_compare_summary_text(session)

    assert "Compare Summary" in summary
    assert "left.txt, right.txt" in summary
    assert "differences found" in summary
