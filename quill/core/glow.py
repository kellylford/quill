from __future__ import annotations

import re
from dataclasses import dataclass

from quill.core.plain_language import lint_plain_language


@dataclass(frozen=True, slots=True)
class GlowFinding:
    rule_id: str
    severity: str
    message: str
    suggestion: str
    line: int | None = None
    column: int | None = None
    fixable: bool = False


@dataclass(frozen=True, slots=True)
class GlowFix:
    description: str


@dataclass(frozen=True, slots=True)
class GlowFixResult:
    text: str
    fixes: tuple[GlowFix, ...]


_GENERIC_LINK_TEXT = {
    "click here",
    "here",
    "read more",
    "more",
    "link",
    "this",
}


def audit_text(text: str, markup: str) -> list[GlowFinding]:
    if markup == "markdown":
        findings = _audit_markdown(text)
    elif markup == "html":
        findings = _audit_html(text)
    else:
        findings = _audit_plain(text)
    findings.extend(_audit_common(text))
    findings.sort(key=lambda item: (item.line or 0, item.column or 0, item.rule_id))
    return findings


def build_audit_report(document_name: str, text: str, markup: str, scope_label: str) -> str:
    findings = audit_text(text, markup)
    fixable = sum(1 for item in findings if item.fixable)
    lines = [
        f"GLOW audit for {document_name}",
        "",
        f"Scope: {scope_label}",
        f"Format: {markup}",
        f"Findings: {len(findings)}",
        f"Automatically fixable: {fixable}",
    ]
    if not findings:
        lines.extend(
            [
                "",
                "No deterministic GLOW findings detected in this scope.",
                "The document is ready for deeper human review and export checks.",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(["", "Findings:"])
    for index, finding in enumerate(findings, start=1):
        location = ""
        if finding.line is not None:
            location = f" (line {finding.line}"
            if finding.column is not None:
                location += f", column {finding.column}"
            location += ")"
        fixable_suffix = " [auto-fix]" if finding.fixable else ""
        lines.append(
            f"{index}. [{finding.severity.upper()}] {finding.rule_id}{location}{fixable_suffix}"
        )
        lines.append(f"   {finding.message}")
        lines.append(f"   Suggestion: {finding.suggestion}")
    return "\n".join(lines).rstrip() + "\n"


def fix_text(text: str, markup: str) -> GlowFixResult:
    updated = text
    fixes: list[GlowFix] = []
    updated, trimmed = _trim_trailing_whitespace(updated)
    if trimmed:
        fixes.append(GlowFix("Trimmed trailing whitespace"))
    if markup == "markdown":
        updated, markdown_fixes = _fix_markdown(updated)
        fixes.extend(markdown_fixes)
    elif markup == "html":
        updated, html_fixes = _fix_html(updated)
        fixes.extend(html_fixes)
    return GlowFixResult(text=updated, fixes=tuple(fixes))


def build_fix_report(
    document_name: str,
    result: GlowFixResult,
    markup: str,
    scope_label: str,
) -> str:
    lines = [
        f"GLOW fixes for {document_name}",
        "",
        f"Scope: {scope_label}",
        f"Format: {markup}",
        f"Applied fixes: {len(result.fixes)}",
    ]
    if not result.fixes:
        lines.extend(["", "No deterministic GLOW fixes were available for this scope."])
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(["", "Applied fixes:"])
    for index, fix in enumerate(result.fixes, start=1):
        lines.append(f"{index}. {fix.description}")
    return "\n".join(lines).rstrip() + "\n"


def _audit_common(text: str) -> list[GlowFinding]:
    findings: list[GlowFinding] = []
    for issue in lint_plain_language(text):
        findings.append(
            GlowFinding(
                rule_id="GLOW-PLAIN-LANGUAGE",
                severity="info",
                message=f'Consider replacing "{issue.phrase}" with plainer language.',
                suggestion=f'Use "{issue.suggestion}" instead.',
                line=issue.line,
                column=issue.column,
            )
        )
    for line_number, paragraph in enumerate(text.split("\n\n"), start=1):
        compact = paragraph.strip()
        if not compact:
            continue
        if len(compact) > 600:
            findings.append(
                GlowFinding(
                    rule_id="GLOW-DENSE-PARAGRAPH",
                    severity="warning",
                    message="This paragraph is long and may be difficult to review or read aloud.",
                    suggestion="Split the paragraph into shorter units or add headings.",
                    line=line_number,
                    column=1,
                )
            )
    return findings


def _audit_plain(text: str) -> list[GlowFinding]:
    findings: list[GlowFinding] = []
    if "\t" in text:
        line, column = _line_column_for_offset(text, text.index("\t"))
        findings.append(
            GlowFinding(
                rule_id="GLOW-TAB-INDENT",
                severity="warning",
                message="Tab characters can create inconsistent reading and export behavior.",
                suggestion="Replace tabs with spaces before sharing or exporting.",
                line=line,
                column=column,
            )
        )
    return findings


def _audit_markdown(text: str) -> list[GlowFinding]:
    findings: list[GlowFinding] = []
    previous_heading_level = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        heading_match = re.match(r"^(#{1,6})([^\s#].*)$", line)
        if heading_match:
            findings.append(
                GlowFinding(
                    rule_id="GLOW-MD-HEADING-SPACING",
                    severity="warning",
                    message="Markdown headings should include a space after the # markers.",
                    suggestion="Insert a space between the heading markers and the heading text.",
                    line=line_number,
                    column=len(heading_match.group(1)) + 1,
                    fixable=True,
                )
            )
        spaced_heading = re.match(r"^(#{1,6})\s+", line)
        if spaced_heading:
            level = len(spaced_heading.group(1))
            if previous_heading_level and level > previous_heading_level + 1:
                findings.append(
                    GlowFinding(
                        rule_id="GLOW-MD-HEADING-JUMP",
                        severity="warning",
                        message="Heading levels jump by more than one level.",
                        suggestion="Use intermediate heading levels for a smoother outline.",
                        line=line_number,
                        column=1,
                    )
                )
            previous_heading_level = level
        for match in re.finditer(r"!?\[([^\]]*)\]\(([^)]+)\)", line):
            label = match.group(1).strip().lower()
            if line[match.start()] == "!" and not label:
                findings.append(
                    GlowFinding(
                        rule_id="GLOW-MD-IMAGE-ALT",
                        severity="error",
                        message="Markdown image is missing alternative text.",
                        suggestion="Add concise alt text inside the image brackets.",
                        line=line_number,
                        column=match.start() + 1,
                    )
                )
            if line[match.start()] != "!" and label in _GENERIC_LINK_TEXT:
                findings.append(
                    GlowFinding(
                        rule_id="GLOW-MD-LINK-TEXT",
                        severity="warning",
                        message="Markdown link text is too generic.",
                        suggestion="Use link text that describes the destination or purpose.",
                        line=line_number,
                        column=match.start() + 1,
                    )
                )
    return findings


def _audit_html(text: str) -> list[GlowFinding]:
    findings: list[GlowFinding] = []
    html_tag = re.search(r"<html\b([^>]*)>", text, re.IGNORECASE)
    if html_tag is not None and re.search(r"\blang\s*=", html_tag.group(1), re.IGNORECASE) is None:
        line, column = _line_column_for_offset(text, html_tag.start())
        findings.append(
            GlowFinding(
                rule_id="GLOW-HTML-LANG",
                severity="error",
                message="The html element is missing a language attribute.",
                suggestion='Add lang="en" (or the correct language code) to the html element.',
                line=line,
                column=column,
                fixable=True,
            )
        )
    heading_matches = list(re.finditer(r"<h([1-6])\b", text, re.IGNORECASE))
    previous_level = 0
    for match in heading_matches:
        level = int(match.group(1))
        if previous_level and level > previous_level + 1:
            line, column = _line_column_for_offset(text, match.start())
            findings.append(
                GlowFinding(
                    rule_id="GLOW-HTML-HEADING-JUMP",
                    severity="warning",
                    message="HTML heading levels jump by more than one level.",
                    suggestion="Use intermediate heading levels for a predictable outline.",
                    line=line,
                    column=column,
                )
            )
        previous_level = level
    for match in re.finditer(r"<img\b([^>]*)>", text, re.IGNORECASE):
        attributes = match.group(1)
        if re.search(r"\balt\s*=", attributes, re.IGNORECASE) is None:
            line, column = _line_column_for_offset(text, match.start())
            findings.append(
                GlowFinding(
                    rule_id="GLOW-HTML-IMG-ALT",
                    severity="error",
                    message="Image element is missing an alt attribute.",
                    suggestion='Add alt text or alt="" for decorative images.',
                    line=line,
                    column=column,
                    fixable=True,
                )
            )
    for match in re.finditer(r"<a\b[^>]*>(.*?)</a>", text, re.IGNORECASE | re.DOTALL):
        link_text = re.sub(r"<[^>]+>", "", match.group(1)).strip().lower()
        if link_text in _GENERIC_LINK_TEXT:
            line, column = _line_column_for_offset(text, match.start())
            findings.append(
                GlowFinding(
                    rule_id="GLOW-HTML-LINK-TEXT",
                    severity="warning",
                    message="Link text is too generic.",
                    suggestion="Use text that describes the destination or action.",
                    line=line,
                    column=column,
                )
            )
    for match in re.finditer(r"<table\b.*?</table>", text, re.IGNORECASE | re.DOTALL):
        if re.search(r"<th\b", match.group(0), re.IGNORECASE) is None:
            line, column = _line_column_for_offset(text, match.start())
            findings.append(
                GlowFinding(
                    rule_id="GLOW-HTML-TABLE-HEADERS",
                    severity="warning",
                    message="Table does not contain header cells.",
                    suggestion="Add th elements for header rows or columns before export.",
                    line=line,
                    column=column,
                )
            )
    return findings


def _fix_markdown(text: str) -> tuple[str, list[GlowFix]]:
    fixes: list[GlowFix] = []
    updated = re.sub(r"(?m)^(#{1,6})([^\s#])", r"\1 \2", text)
    if updated != text:
        fixes.append(GlowFix("Inserted missing spaces after Markdown heading markers"))
    return updated, fixes


def _fix_html(text: str) -> tuple[str, list[GlowFix]]:
    fixes: list[GlowFix] = []
    updated = text
    updated = re.sub(
        r"<html\b(?![^>]*\blang\s*=)([^>]*)>",
        r'<html lang="en"\1>',
        updated,
        count=1,
        flags=re.IGNORECASE,
    )
    if updated != text:
        fixes.append(GlowFix('Added lang="en" to the html element'))
        text = updated
    def add_alt(match: re.Match[str]) -> str:
        attributes = match.group(1).rstrip()
        space = " " if attributes else ""
        return f'<img{space}{attributes} alt="">'
    updated = re.sub(
        r"<img\b((?:(?!\balt\s*=)[^>])*)>",
        add_alt,
        updated,
        flags=re.IGNORECASE,
    )
    if updated != text:
        fixes.append(GlowFix('Added empty alt attributes to img elements missing alt text'))
    return updated, fixes


def _trim_trailing_whitespace(text: str) -> tuple[str, bool]:
    updated = re.sub(r"[ \t]+(?=\r?$)", "", text, flags=re.MULTILINE)
    return updated, updated != text


def _line_column_for_offset(text: str, offset: int) -> tuple[int, int]:
    prefix = text[:offset]
    line = prefix.count("\n") + 1
    line_start = prefix.rfind("\n")
    if line_start < 0:
        return line, offset + 1
    return line, offset - line_start