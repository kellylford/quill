from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ACRMetadata:
    product_name: str
    product_version: str
    report_date: str
    contact: str


def render_acr_markdown(metadata: ACRMetadata) -> str:
    conformance = "Supports / Partially Supports / Does Not Support"
    evidence = "_Fill in evidence_"
    return (
        "# Accessibility Conformance Report (ACR)\n\n"
        "## Report details\n\n"
        f"- Product: **{metadata.product_name}**\n"
        f"- Version: **{metadata.product_version}**\n"
        f"- Report date: **{metadata.report_date}**\n"
        f"- Contact: **{metadata.contact}**\n\n"
        "## Standards and guidelines\n\n"
        "- WCAG 2.1 Level A: _To be assessed_\n"
        "- WCAG 2.1 Level AA: _To be assessed_\n"
        "- Section 508: _To be assessed_\n\n"
        "## VPAT summary table\n\n"
        "| Criteria | Conformance Level | Remarks |\n"
        "| --- | --- | --- |\n"
        f"| 1.1.1 Non-text Content | {conformance} | {evidence} |\n"
        f"| 1.3.1 Info and Relationships | {conformance} | {evidence} |\n"
        f"| 2.1.1 Keyboard | {conformance} | {evidence} |\n"
        f"| 2.4.3 Focus Order | {conformance} | {evidence} |\n"
        f"| 4.1.2 Name, Role, Value | {conformance} | {evidence} |\n\n"
        "## Assessment notes\n\n"
        "- Add screen-reader coverage notes (NVDA, Narrator, JAWS).\n"
        "- Add keyboard-only walkthrough findings.\n"
        "- Add known limitations and remediation targets.\n"
    )
