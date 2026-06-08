"""Unicode code point parser vendored into the Insert Character Quillin.

Accepts hexadecimal (``"1F600"``), decimal with a ``d`` prefix (``"d128512"``),
and ``U+`` notation (``"U+1F600"``). Surrogates and out-of-range values are
rejected with a descriptive :class:`CodepointError`.
"""

from __future__ import annotations

__all__ = ["CodepointError", "parse_codepoint"]

_MAX_CODEPOINT = 0x10FFFF


class CodepointError(ValueError):
    """Raised when a code point string cannot be turned into a character."""


def parse_codepoint(value: str) -> str:
    """Return the Unicode character for ``value``.

    ``value`` is interpreted as hexadecimal by default, as decimal when prefixed
    with a lowercase ``d``, or as a ``U+`` escape. Surrogate and out-of-range
    values are rejected. A leading uppercase ``D`` is a hex digit, not a prefix.
    """
    raw = value.strip()
    if not raw:
        raise CodepointError("Enter a Unicode code point")
    try:
        if raw[0] == "d" and len(raw) > 1 and raw[1:].isdigit():
            number = int(raw[1:], 10)
        elif raw[:2].lower() == "u+":
            number = int(raw[2:], 16)
        else:
            number = int(raw, 16)
    except ValueError as exc:
        raise CodepointError(f"Invalid code point: {value!r}") from exc
    if number < 0 or number > _MAX_CODEPOINT:
        raise CodepointError(f"Code point out of range: {value!r}")
    if 0xD800 <= number <= 0xDFFF:
        raise CodepointError(f"Code point is an unpaired surrogate: {value!r}")
    return chr(number)
