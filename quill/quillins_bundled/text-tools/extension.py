"""Text Tools - a bundled Layer 2 Quillin (Tier C).

Six on-demand text transforms converted out of QUILL's core/UI Python into a
genuine sandboxed Quillin (``docs/quillins.md`` Wave 1):
number lines, hard-wrap lines, count/extract regex matches, and the two
cursor-split set operations. Each runs out-of-process through the same
capability-gated host path offered to third-party authors, proving the platform
can carry features users already rely on.

Capabilities used: ``editor.read`` (read the buffer/selection and cursor),
``editor.write`` (replace the selection, the whole document, or open a results
buffer), ``ui.announce`` (report the outcome for NVDA/JAWS/Narrator parity),
``ui.prompt`` (ask for the start number / wrap width / regex pattern), and
``ui.command`` because these are handler commands. No filesystem, network, or
clipboard access, so no consent prompt is ever raised.
"""

from __future__ import annotations

from algorithms import (
    RegexError,
    count_matches,
    cursor_offset_for_line,
    extract_matches,
    format_lines,
    hard_wrap,
    lines_common_to_both,
    lines_in_first_not_second,
    number_lines,
    widest_line_width,
)
from html_ops import html_to_markdown as _html_to_markdown


def register(api):
    """Register every command handler this Quillin contributes."""

    def _selection_or_document(ctx):
        """Return ``(text, is_selection)`` mirroring core transform-block scope."""

        selection = ctx.get_selection()
        if selection:
            return selection, True
        return ctx.get_text(), False

    def _apply(ctx, transformed, is_selection):
        if is_selection:
            ctx.replace_selection(transformed)
        else:
            ctx.set_text(transformed)

    def number_lines_command(ctx):
        raw = ctx.prompt("Number Lines", "Start numbering at:", "1")
        if raw is None:
            return
        try:
            start = int(raw.strip() or "1")
        except ValueError:
            ctx.announce("Start value must be a whole number")
            return
        block, is_selection = _selection_or_document(ctx)
        _apply(ctx, number_lines(block, start=start), is_selection)
        ctx.announce("Numbered lines")

    def hard_wrap_command(ctx):
        block, is_selection = _selection_or_document(ctx)
        default_width = widest_line_width(block) or 72
        raw = ctx.prompt("Hard-Wrap Lines", "Wrap width:", str(default_width))
        if raw is None:
            return
        try:
            width = int(raw.strip())
        except ValueError:
            ctx.announce("Wrap width must be a whole number")
            return
        if width <= 0:
            ctx.announce("Wrap width must be greater than zero")
            return
        _apply(ctx, hard_wrap(block, width), is_selection)
        ctx.announce(f"Hard-wrapped at {width} characters")

    def count_regex_command(ctx):
        pattern = ctx.prompt("Count Matches", "Regular expression:")
        if pattern is None:
            return
        selection = ctx.get_selection()
        scope = selection if selection else ctx.get_text()
        try:
            total = count_matches(scope, pattern)
        except RegexError as error:
            ctx.announce(str(error))
            return
        ctx.announce(f"{total} match(es)")

    def extract_regex_command(ctx):
        pattern = ctx.prompt("Extract Matches", "Regular expression:")
        if pattern is None:
            return
        selection = ctx.get_selection()
        scope = selection if selection else ctx.get_text()
        try:
            extracted = extract_matches(scope, pattern)
        except RegexError as error:
            ctx.announce(str(error))
            return
        ctx.open_buffer(extracted, "Extracted matches")

    def _split_offset(ctx):
        text = ctx.get_text()
        cursor = ctx.get_cursor()
        return text, cursor_offset_for_line(text, cursor.line)

    def lines_first_only_command(ctx):
        text, offset = _split_offset(ctx)
        lines = lines_in_first_not_second(text, offset)
        ctx.open_buffer(format_lines(lines), f"{len(lines)} line(s) in first block only")

    def lines_common_command(ctx):
        text, offset = _split_offset(ctx)
        lines = lines_common_to_both(text, offset)
        ctx.open_buffer(format_lines(lines), f"{len(lines)} line(s) common to both blocks")

    def html_to_markdown_command(ctx):
        html = ctx.get_clipboard()
        if not html.strip():
            ctx.announce("Clipboard is empty")
            return
        result = _html_to_markdown(html)
        if not result.strip():
            ctx.announce("No Markdown could be extracted from the clipboard HTML")
            return
        ctx.insert_text(result)
        ctx.announce("Pasted clipboard HTML as Markdown")

    api.register_command("number_lines", number_lines_command)
    api.register_command("hard_wrap", hard_wrap_command)
    api.register_command("count_regex", count_regex_command)
    api.register_command("extract_regex", extract_regex_command)
    api.register_command("lines_first_only", lines_first_only_command)
    api.register_command("lines_common", lines_common_command)
    api.register_command("html_to_markdown", html_to_markdown_command)
