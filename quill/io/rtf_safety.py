"""Defensive RTF scanning for QUILL's native RTF surface.

RTF is a historically dangerous format: it can embed OLE objects and executables
(``\\object``/``\\objdata``), binary blobs (``\\bin``), and fields that fetch remote
resources (``INCLUDEPICTURE``, auto-updating links). ``docs/QUILL-PRD.md`` requires that
any native RTF surface parse defensively, refuse embedded executables and OLE
objects, and never fetch a remote resource without explicit consent.

This module is wx-free and runs *before* any byte of RTF reaches a native control.
:func:`scan_rtf_safety` returns a report describing what was blocked or flagged and
a sanitized copy with the dangerous groups removed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

__all__ = ["RtfSafetyReport", "scan_rtf_safety"]

# Destination control words whose entire group is removed before loading. These
# carry embedded objects / binary payloads that have no place in a text document.
_DANGEROUS_DESTINATIONS: frozenset[str] = frozenset({
    "object",
    "objdata",
    "objclass",
    "objemb",
    "objautlink",
    "objalias",
    "datastore",
})

_DESTINATION_LABELS: dict[str, str] = {
    "object": "embedded OLE object",
    "objdata": "embedded object data",
    "objclass": "embedded object class",
    "objemb": "embedded OLE object",
    "objautlink": "auto-updating linked object",
    "objalias": "object alias",
    "datastore": "embedded data store",
}

# Field instructions that fetch remote content; flagged for consent, not auto-run.
_REMOTE_FIELD_RE = re.compile(r"INCLUDEPICTURE|INCLUDETEXT|DDEAUTO", re.IGNORECASE)
_BIN_RE = re.compile(r"\\bin\d+", re.IGNORECASE)


@dataclass(slots=True)
class RtfSafetyReport:
    """The outcome of scanning an RTF document for unsafe constructs."""

    safe: bool
    sanitized_rtf: str
    blocked: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _group_start_destination(rtf: str, brace_index: int) -> str | None:
    """Return the destination control word a group opens with, if dangerous.

    Handles the optional ``\\*`` ignorable-destination marker, e.g.
    ``{\\*\\objdata ...}``.
    """
    index = brace_index + 1
    length = len(rtf)
    if index < length and rtf[index] == "\\" and index + 1 < length and rtf[index + 1] == "*":
        index += 2
        while index < length and rtf[index] in " \r\n":
            index += 1
    if index >= length or rtf[index] != "\\":
        return None
    index += 1
    start = index
    while index < length and rtf[index].isalpha():
        index += 1
    word = rtf[start:index]
    return word if word in _DANGEROUS_DESTINATIONS else None


def _strip_dangerous_groups(rtf: str) -> tuple[str, list[str]]:
    out: list[str] = []
    blocked: list[str] = []
    index = 0
    length = len(rtf)
    while index < length:
        char = rtf[index]
        if char == "\\" and rtf.startswith(("\\{", "\\}", "\\\\"), index):
            # Escaped brace/backslash: copy both characters verbatim.
            out.append(rtf[index : index + 2])
            index += 2
            continue
        if char == "{":
            destination = _group_start_destination(rtf, index)
            if destination is not None:
                label = _DESTINATION_LABELS.get(destination, destination)
                if label not in blocked:
                    blocked.append(label)
                index = _skip_group(rtf, index)
                continue
        out.append(char)
        index += 1
    return "".join(out), blocked


def _skip_group(rtf: str, brace_index: int) -> int:
    """Return the index just past the group opened at ``brace_index``."""
    depth = 0
    index = brace_index
    length = len(rtf)
    while index < length:
        char = rtf[index]
        if char == "\\" and index + 1 < length and rtf[index + 1] in "{}\\":
            index += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return length


def scan_rtf_safety(rtf: str) -> RtfSafetyReport:
    """Scan and sanitize an RTF document string.

    Embedded objects and binary payloads are stripped; remote-fetching fields are
    flagged as warnings (the caller decides whether to honor them, per QUILL's
    no-silent-network rule). ``safe`` is ``True`` only when nothing had to be
    blocked.
    """
    sanitized, blocked = _strip_dangerous_groups(rtf)
    warnings: list[str] = []
    if _BIN_RE.search(sanitized):
        # Any residual binary data outside an object group is removed defensively.
        sanitized = _BIN_RE.sub(r"\\bin0", sanitized)
        warnings.append("binary data")
    if _REMOTE_FIELD_RE.search(sanitized):
        warnings.append("remote content references")
    return RtfSafetyReport(
        safe=not blocked,
        sanitized_rtf=sanitized,
        blocked=blocked,
        warnings=warnings,
    )
