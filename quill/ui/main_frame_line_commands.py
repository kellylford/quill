"""Line- and block-level editor commands for ``MainFrame``.

Extracted from ``main_frame.py`` to keep that module within the size budget
(GATE-11). ``LineCommandsMixin`` is mixed into ``MainFrame`` and every method
resolves identically through the MRO; the ``self._apply_*`` helpers it relies on
stay on ``MainFrame``.
"""

from __future__ import annotations

from quill.core.format_ops import (
    convert_indentation_to_spaces,
    convert_indentation_to_tabs,
    normalize_whitespace,
    remove_duplicate_lines,
    reverse_lines,
    sort_lines,
    trim_trailing_whitespace,
)
from quill.core.line_ops import (
    delete_line,
    duplicate_line,
    join_selected_lines,
    move_lines_down,
    move_lines_up,
    selected_line_bounds,
)


class LineCommandsMixin:
    def move_line_up(self) -> None:
        # Selection-aware (issue #133): a multi-line selection moves as one block,
        # the status names the line count so the result is unambiguous to a screen
        # reader, and the document edge reports an accurate no-op message.
        self._apply_selection_operation(
            move_lines_up,
            self._moved_lines_status("up"),
            no_change_status="Already at the top",
        )

    def move_line_down(self) -> None:
        self._apply_selection_operation(
            move_lines_down,
            self._moved_lines_status("down"),
            no_change_status="Already at the bottom",
        )

    def _moved_lines_status(self, direction: str) -> str:
        text = self.editor.GetValue()
        start, end = self.editor.GetSelection()
        first, last = selected_line_bounds(text, start, end)
        return self._move_lines_label(last - first + 1, direction)

    @staticmethod
    def _move_lines_label(count: int, direction: str) -> str:
        if count <= 1:
            return f"Moved line {direction}"
        return f"Moved {count} lines {direction}"

    def duplicate_line(self) -> None:
        self._apply_line_operation(duplicate_line, "Duplicated line")

    def delete_line(self) -> None:
        self._apply_line_operation(delete_line, "Deleted line")

    def join_lines(self) -> None:
        # Selection-aware (issue #135): joins the whole selection, or the
        # caret's paragraph when there is no selection, instead of only the
        # current line and the next one. The status names how many lines
        # collapsed (parity with move-line), and a single line is a quiet no-op.
        text = self.editor.GetValue()
        start, end = self.editor.GetSelection()
        updated, _new_start, _new_end = join_selected_lines(text, start, end)
        self._apply_selection_operation(
            join_selected_lines,
            self._joined_lines_label(text, updated, start, end),
            no_change_status="No lines to join",
        )

    @staticmethod
    def _joined_lines_label(before: str, after: str, start: int, end: int) -> str:
        removed = before.count("\n") - after.count("\n")
        if removed <= 0:
            return "Joined lines"
        if start == end:
            # No selection: the caret's paragraph collapses into one line.
            source = removed + 1
        else:
            first, last = selected_line_bounds(before, start, end)
            source = last - first + 1
        return f"Joined {source} lines"

    def sort_lines_ascending(self) -> None:
        self._apply_text_block_operation(
            lambda text: sort_lines(text, descending=False),
            "Sorted lines ascending",
        )

    def sort_lines_descending(self) -> None:
        self._apply_text_block_operation(
            lambda text: sort_lines(text, descending=True),
            "Sorted lines descending",
        )

    def reverse_lines(self) -> None:
        self._apply_text_block_operation(reverse_lines, "Reversed lines")

    def remove_duplicate_lines(self) -> None:
        self._apply_text_block_operation(
            remove_duplicate_lines,
            "Removed duplicate lines",
        )

    def trim_trailing_whitespace(self) -> None:
        self._apply_text_block_operation(
            trim_trailing_whitespace,
            "Trimmed trailing whitespace",
        )

    def normalize_whitespace(self) -> None:
        self._apply_text_block_operation(normalize_whitespace, "Normalized whitespace")

    def convert_indentation_to_spaces(self) -> None:
        self._apply_text_block_operation(
            lambda text: convert_indentation_to_spaces(text, self._indent_width()),
            "Converted indentation to spaces",
        )

    def convert_indentation_to_tabs(self) -> None:
        self._apply_text_block_operation(
            lambda text: convert_indentation_to_tabs(text, self._indent_width()),
            "Converted indentation to tabs",
        )
