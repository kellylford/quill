"""Tests for windows_ocr.py importability without winsdk (H-3-platform).

The winsdk package is a Windows-runtime-only optional dependency.  On CI and
non-Windows dev boxes it is not installed.  The module must be importable
regardless and must raise OcrUnavailableError at call time, not at import time.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


def test_module_imports_without_winsdk() -> None:
    """H-3-platform: windows_ocr imports cleanly when winsdk is absent."""
    # Remove the module from the cache so the import runs fresh.
    mod_name = "quill.platform.windows.windows_ocr"
    cached = sys.modules.pop(mod_name, None)
    # Patch all winsdk sub-modules to simulate absence.
    winsdk_mods = [
        "winsdk",
        "winsdk.windows",
        "winsdk.windows.globalization",
        "winsdk.windows.graphics",
        "winsdk.windows.graphics.imaging",
        "winsdk.windows.media",
        "winsdk.windows.media.ocr",
        "winsdk.windows.storage",
    ]
    with patch.dict(sys.modules, {m: None for m in winsdk_mods}):  # type: ignore[arg-type]
        try:
            import importlib

            mod = importlib.import_module(mod_name)
        finally:
            # Restore original state whether the test passes or fails.
            sys.modules.pop(mod_name, None)
            if cached is not None:
                sys.modules[mod_name] = cached
    # If we got here without ImportError the module is importable.
    assert hasattr(mod, "recognize_with_windows_ocr")
    assert mod._WINSDK_AVAILABLE is False  # type: ignore[attr-defined]


def test_recognize_raises_ocr_unavailable_when_winsdk_missing() -> None:
    """H-3-platform: recognize_with_windows_ocr raises OcrUnavailableError when winsdk absent."""
    from quill.io.ocr import OcrUnavailableError

    mod_name = "quill.platform.windows.windows_ocr"
    cached = sys.modules.pop(mod_name, None)
    winsdk_mods = [
        "winsdk",
        "winsdk.windows",
        "winsdk.windows.globalization",
        "winsdk.windows.graphics",
        "winsdk.windows.graphics.imaging",
        "winsdk.windows.media",
        "winsdk.windows.media.ocr",
        "winsdk.windows.storage",
    ]
    import pytest

    with patch.dict(sys.modules, {m: None for m in winsdk_mods}):  # type: ignore[arg-type]
        try:
            import importlib

            mod = importlib.import_module(mod_name)
            with pytest.raises(OcrUnavailableError, match="winsdk"):
                mod.recognize_with_windows_ocr(Path("dummy.png"), None)
        finally:
            sys.modules.pop(mod_name, None)
            if cached is not None:
                sys.modules[mod_name] = cached
