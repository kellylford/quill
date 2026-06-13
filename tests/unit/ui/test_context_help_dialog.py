"""Tests for the ContextHelpMixin show_control_help dialog contract."""

from __future__ import annotations


def test_show_control_help_uses_show_modal_dialog(monkeypatch) -> None:
    import types

    from quill.ui.context_help import ContextHelpMixin

    # Minimal stand-in for wx.
    fake_wx = types.ModuleType("wx")
    fake_wx.ID_OK = 5100  # type: ignore[attr-defined]
    fake_wx.ID_HELP = 5199  # type: ignore[attr-defined]
    fake_wx.DEFAULT_DIALOG_STYLE = 0  # type: ignore[attr-defined]
    fake_wx.RESIZE_BORDER = 0  # type: ignore[attr-defined]

    modal_calls: list[tuple[object, str]] = []

    class _FakeDialog:
        def __init__(self, *_args, **_kwargs):
            pass

        def ShowModal(self):
            raise AssertionError("ShowModal must not be called directly")

        def Destroy(self):
            pass

    class _FakeMixin(ContextHelpMixin):
        _last_focused_ctrl = None

        def __init__(self):
            self._modal_calls = modal_calls

        def _show_modal_dialog(self, dlg, label, **_kw):
            modal_calls.append((dlg, label))
            return fake_wx.ID_OK

    # Patch ContextHelpDialog so no wx is needed.
    import quill.ui.context_help as ch_mod

    monkeypatch.setattr(ch_mod, "ContextHelpDialog", _FakeDialog)
    # Patch describe_focused to return minimal topics.
    from quill.core.help import HelpTopic

    monkeypatch.setattr(
        ch_mod,
        "describe_focused",
        lambda _ctrl: (None, HelpTopic(id="test", title="Test Control", body="body")),
    )

    import wx as real_wx

    monkeypatch.setattr(real_wx.Window, "FindFocus", staticmethod(lambda: None))

    mixin = _FakeMixin()
    mixin.show_control_help()

    assert len(modal_calls) == 1
    assert modal_calls[0][1] == "Context Help"
