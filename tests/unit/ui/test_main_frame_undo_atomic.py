"""Live-wx regression for issue #131: a whole-document case transform must be a
single, cleanly reversible undo step.

This test instantiates real wx controls, so it runs on Windows (where wxPython is
installed) and is skipped automatically in the Linux cloud CI environment.
"""

from __future__ import annotations

import pytest

wx = pytest.importorskip("wx")

from quill.ui.main_frame import MainFrame  # noqa: E402


@pytest.fixture(scope="module")
def wx_app():
    app = wx.App()
    yield app
    app.Destroy()


class _Holder:
    """Minimal host exposing just the atomic-replace helper bound to a control."""

    def __init__(self, editor) -> None:
        self.editor = editor

    _atomic_replace = MainFrame._atomic_replace


def test_atomic_replace_whole_document_undoes_in_one_step(wx_app) -> None:
    frame = wx.Frame(None)
    try:
        ctrl = wx.TextCtrl(frame, style=wx.TE_MULTILINE)
        ctrl.SetValue("hello world this is a test")
        holder = _Holder(ctrl)

        text = ctrl.GetValue()
        holder._atomic_replace(0, len(text), text.upper())
        assert ctrl.GetValue() == "HELLO WORLD THIS IS A TEST"

        # A single undo restores exactly the original text — not an empty or
        # corrupted intermediate state (the #131 bug with native Replace).
        ctrl.Undo()
        assert ctrl.GetValue() == "hello world this is a test"
    finally:
        frame.Destroy()


def test_atomic_replace_preserves_earlier_history(wx_app) -> None:
    frame = wx.Frame(None)
    try:
        ctrl = wx.TextCtrl(frame, style=wx.TE_MULTILINE)
        ctrl.SetValue("hello world")
        # An earlier edit that must survive undoing the transform.
        ctrl.SetInsertionPointEnd()
        ctrl.WriteText("!")
        holder = _Holder(ctrl)

        text = ctrl.GetValue()
        holder._atomic_replace(0, len(text), text.upper())
        assert ctrl.GetValue() == "HELLO WORLD!"

        ctrl.Undo()
        # Back to the pre-transform text, with the earlier "!" edit intact.
        assert ctrl.GetValue() == "hello world!"
    finally:
        frame.Destroy()


def test_native_replace_would_corrupt_undo(wx_app) -> None:
    """Document the native behavior the fix avoids: Replace splits into two
    undo entries, so one undo lands on an empty intermediate state."""
    frame = wx.Frame(None)
    try:
        ctrl = wx.TextCtrl(frame, style=wx.TE_MULTILINE)
        ctrl.SetValue("hello world this is a test")
        text = ctrl.GetValue()
        ctrl.Replace(0, len(text), text.upper())
        ctrl.Undo()
        assert ctrl.GetValue() == ""  # the bug; _atomic_replace avoids this
    finally:
        frame.Destroy()
