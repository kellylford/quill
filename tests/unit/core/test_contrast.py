from __future__ import annotations

from quill.core.contrast import contrast_ratio, render_contrast_report, validate_theme_contrast


def test_contrast_ratio_computes_expected_ordering() -> None:
    assert contrast_ratio("#000000", "#FFFFFF") > contrast_ratio("#777777", "#FFFFFF")


def test_validate_theme_contrast_returns_checks() -> None:
    checks = validate_theme_contrast("dark")
    assert len(checks) == 2
    assert checks[0].label == "Body text"


def test_render_contrast_report_contains_results() -> None:
    report = render_contrast_report("system", validate_theme_contrast("system"))
    assert "Contrast validation for theme: system" in report
    assert "PASS" in report
