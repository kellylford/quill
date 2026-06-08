"""Line Tools - a bundled Layer 2 Quillin (Tier C).

Six cursor-aware line operations converted out of QUILL's core into a genuine
sandboxed Quillin: duplicate line, delete line, move line up, move line down,
join paragraph lines, and join with next line.

Each operation uses the new ``get_cursor_offset()`` and ``set_cursor()`` API
methods to read and reposition the caret as an integer character offset, so
the algorithm can work with the same coordinate system as the pure text
functions it calls. Changes are applied as a single ``set_text`` undoable edit
followed by a ``set_cursor`` reposition.

Capabilities used: ``editor.read`` (read buffer text and cursor offset),
``editor.write`` (replace document text and set cursor position),
``ui.announce`` (optional no-op), ``ui.command`` (handler commands). No
filesystem, network, clipboard, or storage access.
"""

from __future__ import annotations

from line_ops import (
    delete_line,
    duplicate_line,
    join_paragraph,
    join_with_next_line,
    move_line_down,
    move_line_up,
)


def register(api):
    """Register every line-tool handler."""

    def _make_simple_command(transform):
        """Build a command that applies a (text, cursor) -> (text, cursor) transform."""

        def command(ctx):
            text = ctx.get_text()
            cursor = ctx.get_cursor_offset()
            new_text, new_cursor = transform(text, cursor)
            if new_text != text:
                ctx.set_text(new_text)
            ctx.set_cursor(new_cursor)

        return command

    api.register_command("duplicate_line", _make_simple_command(duplicate_line))
    api.register_command("delete_line", _make_simple_command(delete_line))
    api.register_command("move_line_up", _make_simple_command(move_line_up))
    api.register_command("move_line_down", _make_simple_command(move_line_down))
    api.register_command("join_paragraph", _make_simple_command(join_paragraph))
    api.register_command("join_with_next_line", _make_simple_command(join_with_next_line))
