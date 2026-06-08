"""Insert Character - a bundled Layer 2 Quillin (Tier C).

Prompt the user for a Unicode code point (hex, decimal with ``d`` prefix, or
``U+`` notation) and insert the corresponding character at the caret. Announces
the inserted character's code point and name so screen reader users know what
landed in the document.

Capabilities used: ``ui.prompt`` (ask for the code point), ``ui.announce``
(report the result), ``editor.write`` (insert the character), and ``ui.command``
because this is a handler command. No filesystem, network, or clipboard access.
"""

from __future__ import annotations

import unicodedata

from codepoints import CodepointError, parse_codepoint


def register(api):
    """Register the insert_character handler."""

    def insert_character(ctx):
        raw = ctx.prompt(
            "Insert Special Character",
            "Code point (hex, dNNN for decimal, or U+NNNN):",
            "",
        )
        if raw is None:
            return
        try:
            char = parse_codepoint(raw.strip())
        except CodepointError as error:
            ctx.announce(str(error))
            return
        ctx.insert_text(char)
        try:
            name = unicodedata.name(char)
        except ValueError:
            name = "unknown"
        ctx.announce(f"Inserted U+{ord(char):04X} {name}")

    api.register_command("insert_character", insert_character)
