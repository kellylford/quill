from __future__ import annotations

import re
from dataclasses import dataclass

CONTROLLED_VOCABULARY: dict[str, str] = {
    "utilize": "use",
    "leverage": "use",
    "aforementioned": "earlier",
    "commence": "start",
    "terminate": "end",
    "in order to": "to",
}


@dataclass(frozen=True, slots=True)
class PlainLanguageIssue:
    phrase: str
    suggestion: str
    line: int
    column: int


def lint_plain_language(
    text: str,
    vocabulary: dict[str, str] | None = None,
) -> list[PlainLanguageIssue]:
    phrase_map = vocabulary or CONTROLLED_VOCABULARY
    issues: list[PlainLanguageIssue] = []
    for phrase, suggestion in phrase_map.items():
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            line, column = _line_column_for_offset(text, match.start())
            issues.append(
                PlainLanguageIssue(
                    phrase=match.group(0),
                    suggestion=suggestion,
                    line=line,
                    column=column,
                )
            )
    issues.sort(key=lambda issue: (issue.line, issue.column, issue.phrase.lower()))
    return issues


def _line_column_for_offset(text: str, offset: int) -> tuple[int, int]:
    prefix = text[:offset]
    line = prefix.count("\n") + 1
    line_start = prefix.rfind("\n")
    if line_start < 0:
        return line, offset + 1
    return line, offset - line_start
