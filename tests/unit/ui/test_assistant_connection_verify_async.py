"""Issue #127: the AI connection verify must not block the UI thread (and the
screen reader) while a slow endpoint is contacted."""

from __future__ import annotations

import threading

import quill.ui.assistant_tools as assistant_tools
from quill.ui.assistant_tools import AssistantConnectionDialog


class _Button:
    def __init__(self) -> None:
        self.enabled = True

    def Enable(self, value: bool) -> None:  # noqa: N802
        self.enabled = value


class _Label:
    def __init__(self) -> None:
        self.text = ""

    def SetLabel(self, value: str) -> None:  # noqa: N802
        self.text = value


class _Field:
    def GetValue(self) -> str:  # noqa: N802
        return "secret-key"


class _Wx:
    ICON_INFORMATION = 1
    ICON_WARNING = 2
    OK = 4

    def __init__(self) -> None:
        self.message_calls: list[tuple[str, str, int]] = []

    def CallAfter(self, func, *args) -> None:  # noqa: N802
        func(*args)

    def MessageBox(self, message: str, caption: str, flags: int) -> None:  # noqa: N802
        self.message_calls.append((message, caption, flags))


def _dialog(wx: _Wx) -> AssistantConnectionDialog:
    dialog = AssistantConnectionDialog.__new__(AssistantConnectionDialog)
    dialog._wx = wx
    dialog.verify_button = _Button()
    dialog.connection_status = _Label()
    dialog.api_key = _Field()
    dialog._current_settings = lambda: object()
    return dialog


def test_verify_runs_off_the_ui_thread(monkeypatch) -> None:
    wx = _Wx()
    dialog = _dialog(wx)

    worker_threads: list[str] = []

    def fake_verify(_settings, _key):
        worker_threads.append(threading.current_thread().name)
        return True, "Connection verified. Found 3 models."

    monkeypatch.setattr(assistant_tools, "verify_assistant_connection", fake_verify)

    main_thread = threading.current_thread().name
    dialog._on_verify_connection(object())

    # Give the worker thread a moment to finish (CallAfter runs inline here).
    for _ in range(100):
        if wx.message_calls:
            break
        threading.Event().wait(0.01)

    assert worker_threads and worker_threads[0] != main_thread
    assert wx.message_calls
    assert dialog.verify_button.enabled is True
    assert "verified" in dialog.connection_status.text.lower()


def test_verify_disables_button_and_shows_progress(monkeypatch) -> None:
    wx = _Wx()
    dialog = _dialog(wx)

    started = threading.Event()
    release = threading.Event()

    def fake_verify(_settings, _key):
        started.set()
        release.wait(1.0)
        return False, "Could not reach the AI endpoint."

    monkeypatch.setattr(assistant_tools, "verify_assistant_connection", fake_verify)

    dialog._on_verify_connection(object())
    started.wait(1.0)

    # While the worker is still running, the button is disabled and progress shown.
    assert dialog.verify_button.enabled is False
    assert dialog.connection_status.text == "Verifying connection..."

    release.set()
    for _ in range(100):
        if wx.message_calls:
            break
        threading.Event().wait(0.01)
    assert dialog.verify_button.enabled is True
