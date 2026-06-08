"""Live ``Host`` adapter binding the first-party facade to ``MainFrame``.

This is the ``quill/ui`` implementation of the wx-free
:class:`quill.core.contributions.Host` protocol (migration plan §4). It is a thin
adapter: every method delegates to an already-tested ``MainFrame`` helper, so a
feature module that drives the editor through the host behaves byte-for-byte like
the inline handler it replaced. The adapter holds only a back-reference to the
frame and reads ``frame.editor`` dynamically, so it stays correct across tab
switches without being rebuilt.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class MainFrameHost:
    """Adapt a live :class:`~quill.ui.main_frame.MainFrame` to ``Host``."""

    def __init__(self, frame: Any) -> None:
        self._frame = frame

    def get_text(self) -> str:
        return str(self._frame.editor.GetValue())

    def get_selection(self) -> tuple[int, int]:
        start, end = self._frame.editor.GetSelection()
        return int(start), int(end)

    def is_read_only(self) -> bool:
        return bool(self._frame._document_is_read_only())

    def set_status(self, message: str) -> None:
        self._frame._set_status(message)

    def announce(self, message: str) -> None:
        self._frame._announce(message)

    def prompt(self, title: str, label: str, value: str = "") -> str | None:
        result = self._frame._power_tools_prompt_single(title, label, value)
        return None if result is None else str(result)

    def transform_block(self, transform: Callable[[str], str], status: str) -> None:
        self._frame._power_tools_transform_selection_or_document(transform, status)
