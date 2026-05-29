from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContrastCheck:
    label: str
    ratio: float
    passes_normal_text: bool


def validate_theme_contrast(theme: str) -> list[ContrastCheck]:
    palettes = {
        "system": ("#1E1E1E", "#FFFFFF", "#005A9E", "#FFFFFF"),
        "light": ("#111111", "#FFFFFF", "#0F6CBD", "#FFFFFF"),
        "dark": ("#E5E5E5", "#1E1E1E", "#7FB4FF", "#1E1E1E"),
        "low-vision": ("#000000", "#FFFFFF", "#FFD400", "#000000"),
    }
    text_fg, text_bg, accent_fg, accent_bg = palettes.get(theme, palettes["system"])
    checks = [
        _check_pair("Body text", text_fg, text_bg),
        _check_pair("Accent text", accent_fg, accent_bg),
    ]
    return checks


def render_contrast_report(theme: str, checks: list[ContrastCheck]) -> str:
    lines = [f"Contrast validation for theme: {theme}", ""]
    for check in checks:
        result = "PASS" if check.passes_normal_text else "FAIL"
        lines.append(f"- {check.label}: {check.ratio:.2f}:1 ({result})")
    return "\n".join(lines)


def _check_pair(label: str, foreground: str, background: str) -> ContrastCheck:
    ratio = contrast_ratio(foreground, background)
    return ContrastCheck(label=label, ratio=ratio, passes_normal_text=ratio >= 4.5)


def contrast_ratio(foreground: str, background: str) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(color: str) -> float:
    red, green, blue = _hex_to_rgb(color)
    channels = [_srgb_to_linear(component / 255.0) for component in (red, green, blue)]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    cleaned = value.lstrip("#")
    if len(cleaned) != 6:
        raise ValueError(f"Invalid hex color: {value}")
    return int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16)


def _srgb_to_linear(component: float) -> float:
    if component <= 0.04045:
        return component / 12.92
    return float(((component + 0.055) / 1.055) ** 2.4)
