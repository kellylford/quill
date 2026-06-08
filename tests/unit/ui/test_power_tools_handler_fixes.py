"""Behavior tests for power-tool handlers that had wiring bugs.

Covers the Infer Indent setting name (EDS-18) and the clipboard collector
rebind-on-toggle correctness (EDS-11), exercising the mixin against lightweight
stand-ins (no live wx needed).
"""

from __future__ import annotations

from quill.ui.main_frame_power_tools import PowerToolsActionsMixin


class _Settings:
    def __init__(self) -> None:
        self.indent_with_tabs = False
        self.indent_size = 4


class _Editor:
    def __init__(self, text: str) -> None:
        self._text = text

    def GetValue(self) -> str:
        return self._text


class _IndentHarness(PowerToolsActionsMixin):
    def __init__(self, text: str, answer: int) -> None:
        self.editor = _Editor(text)
        self.settings = _Settings()
        self._answer = answer
        self.announced: list[str] = []
        self.status: str | None = None

    class _Wx:
        YES_NO = 1
        ICON_QUESTION = 2
        ID_YES = 100

    _wx = _Wx()

    def _show_message_box(self, message: str, title: str, style: int) -> int:
        return self._answer

    def _announce(self, message: str) -> None:
        self.announced.append(message)

    def _set_status(self, message: str) -> None:
        self.status = message


def test_infer_indent_adopts_indent_size_not_indent_width() -> None:
    harness = _IndentHarness("    one\n    two\n", answer=_IndentHarness._Wx.ID_YES)
    harness.infer_indent()
    assert harness.settings.indent_with_tabs is False
    assert harness.settings.indent_size == 4
    # The old bug set a non-existent `indent_width` attribute and left indent_size stale.
    assert not hasattr(harness.settings, "indent_width")


def test_infer_indent_adopts_tabs() -> None:
    harness = _IndentHarness("\tone\n\ttwo\n", answer=_IndentHarness._Wx.ID_YES)
    harness.infer_indent()
    assert harness.settings.indent_with_tabs is True


def test_infer_indent_decline_leaves_settings_unchanged() -> None:
    harness = _IndentHarness("  one\n  two\n", answer=999)
    harness.infer_indent()
    assert harness.settings.indent_size == 4
    assert harness.settings.indent_with_tabs is False


class _CopyEditor:
    def __init__(self, name: str) -> None:
        self.name = name
        self.bound: list[str] = []

    def Bind(self, event: object, handler: object) -> None:
        self.bound.append("bind")

    def Unbind(self, event: object) -> None:
        self.bound.append("unbind")


class _CollectorHarness(PowerToolsActionsMixin):
    class _Wx:
        EVT_TEXT_COPY = object()

    _wx = _Wx()

    def __init__(self) -> None:
        self.editor = _CopyEditor("tab1")
        self.announced: list[str] = []

    def _announce(self, message: str) -> None:
        self.announced.append(message)


def test_collector_toggle_unbinds_the_editor_it_bound() -> None:
    harness = _CollectorHarness()
    first = harness.editor

    harness.toggle_clipboard_collector()  # on -> binds first
    assert first.bound == ["bind"]
    assert harness._power_tools_collector_editor is first

    # Switch tabs, then toggle off: the ORIGINAL editor must be unbound.
    harness.editor = _CopyEditor("tab2")
    harness.toggle_clipboard_collector()  # off -> unbinds first, not the new editor
    assert "unbind" in first.bound
    assert harness.editor.bound == []
    assert harness._power_tools_collector_editor is None
