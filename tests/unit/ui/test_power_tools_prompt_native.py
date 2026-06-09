"""Regression: single-field power-tool/Quillin prompts must be native.

A WebView form forces the screen reader into virtual-cursor mode for a trivial
prompt (e.g. Number Lines "Start numbering at:"). The shared
``_power_tools_prompt_single`` helper must use a native wx.TextEntryDialog.
"""

from __future__ import annotations

from pathlib import Path


def _power_tools_source() -> str:
    return Path("quill/ui/main_frame_power_tools.py").read_text(encoding="utf-8")


def _prompt_single_body() -> str:
    source = _power_tools_source()
    start = source.index("def _power_tools_prompt_single")
    end = source.index("def _power_tools_clipboard_text")
    return source[start:end]


def test_single_prompt_uses_native_text_entry_dialog() -> None:
    body = _prompt_single_body()
    assert "wx.TextEntryDialog(" in body
    assert "show_web_form" not in body
