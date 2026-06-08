"""Line-transform commands (``power.number_lines``, ``power.hard_wrap_lines``).

The first feature group migrated off ``main_frame.py`` onto the contribution
grammar (Quillin migration plan §9, Wave 2). These handlers are the worked
example: pure functions that read the editor, prompt for a parameter, and apply a
:mod:`quill.core.line_ops` / :mod:`quill.core.wrap_ops` transform — all through
the wx-free :class:`quill.core.contributions.Host` facade. They import no ``wx``
and reach no ``MainFrame`` internal, so they are unit-testable with a fake host.

``HANDLERS`` maps each command id to its handler; the Power Tools menu/registration
table resolves these ids to ``lambda: handler(host)`` instead of a mixin method,
which is what lets the inline bodies leave the god object.
"""

from __future__ import annotations

from collections.abc import Callable

from quill.core.contributions import Host
from quill.core.line_ops import number_lines as _number_lines_op
from quill.core.wrap_ops import hard_wrap, widest_line_width


def number_lines(host: Host) -> None:
    """Prefix each line of the selection (or document) with a running number."""

    raw = host.prompt("Number Lines", "Start numbering at:", "1")
    if raw is None:
        return
    try:
        start = int(raw.strip() or "1")
    except ValueError:
        host.set_status("Start value must be a whole number")
        return
    host.transform_block(
        lambda block: _number_lines_op(block, start=start),
        "Numbered lines",
    )


def hard_wrap_lines(host: Host) -> None:
    """Hard-wrap the selection (or document) at a user-supplied column width."""

    text = host.get_text()
    start, end = host.get_selection()
    block = text if start == end else text[start:end]
    default_width = widest_line_width(block) or 72
    raw = host.prompt("Hard-Wrap Lines", "Wrap width:", str(default_width))
    if raw is None:
        return
    try:
        width = int(raw.strip())
    except ValueError:
        host.set_status("Wrap width must be a whole number")
        return
    if width <= 0:
        host.set_status("Wrap width must be greater than zero")
        return
    host.transform_block(
        lambda value: hard_wrap(value, width),
        f"Hard-wrapped at {width} characters",
    )


# Command-id -> handler. Consumed by the Power Tools registration/menu wiring so the
# manifest stays the single declaration of placement while the behavior lives
# here (migration plan §9).
HANDLERS: dict[str, Callable[[Host], None]] = {
    "power.number_lines": number_lines,
    "power.hard_wrap_lines": hard_wrap_lines,
}
