from __future__ import annotations

from quill.ui.sticky_notes import StickyNoteEditorDialog
from quill.ui.web_form import _WebFormDialog


class _FakeDialog:
    def __init__(self) -> None:
        self.result: int | None = None

    def EndModal(self, result: int) -> None:
        self.result = result


class _FakeWx:
    ID_OK = 1
    ID_CANCEL = 2


def test_web_form_accepts_json_string_messages() -> None:
    dialog = _WebFormDialog.__new__(_WebFormDialog)
    dialog._wx = _FakeWx()
    dialog.dialog = _FakeDialog()
    dialog._result = None

    dialog._on_message('{"type":"save","values":{"style":"balanced"}}')

    assert dialog._result == {"style": "balanced"}
    assert dialog.dialog.result == _FakeWx.ID_OK


def test_web_form_cancel_from_json_string_closes_dialog() -> None:
    dialog = _WebFormDialog.__new__(_WebFormDialog)
    dialog._wx = _FakeWx()
    dialog.dialog = _FakeDialog()
    dialog._result = None

    dialog._on_message('{"type":"cancel"}')

    assert dialog.dialog.result == _FakeWx.ID_CANCEL


def test_sticky_note_editor_accepts_json_string_messages() -> None:
    dialog = StickyNoteEditorDialog.__new__(StickyNoteEditorDialog)
    dialog._wx = _FakeWx()
    dialog.dialog = _FakeDialog()
    dialog._result = None

    dialog._on_message('{"type":"save","title":"Title","body":"Body"}')

    assert dialog._result == "Title\nBody"
    assert dialog.dialog.result == _FakeWx.ID_OK


def test_sticky_note_editor_cancel_from_json_string_closes_dialog() -> None:
    dialog = StickyNoteEditorDialog.__new__(StickyNoteEditorDialog)
    dialog._wx = _FakeWx()
    dialog.dialog = _FakeDialog()
    dialog._result = None

    dialog._on_message('{"type":"cancel"}')

    assert dialog.dialog.result == _FakeWx.ID_CANCEL
