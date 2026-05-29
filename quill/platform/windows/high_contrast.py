from __future__ import annotations

try:  # pragma: no cover - Windows-only runtime hook
    import ctypes
    from ctypes import wintypes
except ImportError:  # pragma: no cover - non-Windows fallback
    ctypes = None
    wintypes = None

SPI_GETHIGHCONTRAST = 0x0042
HCF_HIGHCONTRASTON = 0x00000001


def is_high_contrast_enabled() -> bool:
    if ctypes is None or wintypes is None or not hasattr(ctypes, "windll"):
        return False

    class HIGHCONTRASTW(ctypes.Structure):  # type: ignore[attr-defined]
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("dwFlags", wintypes.DWORD),
            ("lpszDefaultScheme", wintypes.LPWSTR),
        ]

    high_contrast = HIGHCONTRASTW()
    high_contrast.cbSize = ctypes.sizeof(HIGHCONTRASTW)
    ok = ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
        SPI_GETHIGHCONTRAST,
        high_contrast.cbSize,
        ctypes.byref(high_contrast),
        0,
    )
    if not ok:
        return False
    return bool(high_contrast.dwFlags & HCF_HIGHCONTRASTON)
