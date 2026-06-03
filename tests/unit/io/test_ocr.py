from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from quill.io.ocr import (
    ENGINE_WINDOWS,
    CancelFn,
    OcrCancelledError,
    OcrLine,
    OcrResult,
    OcrUnavailableError,
    ProgressFn,
    WindowsOcrBackend,
    available_engines,
    default_backends,
    ocr_image,
    render_ocr_review,
)

# --- backend-pluggable selection (OCR-1) -----------------------------------


@dataclass
class _FakeBackend:
    """A test backend with controllable availability and recognized text."""

    backend_id: str
    available: bool = True
    text: str = "hello world"

    def is_available(self) -> bool:
        return self.available

    def run(
        self,
        path: Path,
        language: str | None,
        on_progress: ProgressFn | None,
        cancel_requested: CancelFn | None,
    ) -> OcrResult:
        if on_progress is not None:
            on_progress("Running OCR...")
        if cancel_requested is not None and cancel_requested():
            raise OcrCancelledError("OCR cancelled.")
        return OcrResult(
            text=self.text + "\n",
            engine=self.backend_id,
            language=language or "",
            lines=[OcrLine(text=self.text, confidence=95.0)],
        )


def _backends(windows: bool) -> dict[str, _FakeBackend]:
    return {
        ENGINE_WINDOWS: _FakeBackend(ENGINE_WINDOWS, available=windows, text="windows text"),
    }


def test_default_backends_exposes_windows_engine() -> None:
    registry = default_backends()
    assert set(registry) == {ENGINE_WINDOWS}
    assert isinstance(registry[ENGINE_WINDOWS], WindowsOcrBackend)


def test_available_engines_filters_by_availability() -> None:
    assert available_engines(_backends(windows=True)) == [ENGINE_WINDOWS]
    assert available_engines(_backends(windows=False)) == []


def test_ocr_image_runs_windows_backend() -> None:
    result = ocr_image(Path("x.png"), backends=_backends(windows=True))
    assert result.engine == ENGINE_WINDOWS
    assert result.text.strip() == "windows text"


def test_ocr_image_raises_when_engine_unavailable() -> None:
    with pytest.raises(OcrUnavailableError):
        ocr_image(Path("x.png"), backends=_backends(windows=False))


def test_ocr_image_reports_progress() -> None:
    messages: list[str] = []
    ocr_image(
        Path("x.png"),
        on_progress=messages.append,
        backends=_backends(windows=True),
    )
    assert "Running OCR..." in messages


def test_ocr_image_can_be_cancelled() -> None:
    with pytest.raises(OcrCancelledError):
        ocr_image(
            Path("x.png"),
            cancel_requested=lambda: True,
            backends=_backends(windows=True),
        )


def test_windows_backend_availability_is_boolean() -> None:
    backend = WindowsOcrBackend()
    # On a machine without the WinRT OCR projection this is False; the call must
    # not raise regardless of platform.
    assert isinstance(backend.is_available(), bool)


# --- low-confidence flagging (OCR-4) ---------------------------------------


def test_ocr_line_low_confidence_threshold() -> None:
    assert OcrLine("clear", 92.0).is_low_confidence is False
    assert OcrLine("fuzzy", 30.0).is_low_confidence is True
    # A missing confidence (-1) is never treated as low.
    assert OcrLine("unknown").is_low_confidence is False


def test_result_low_confidence_lines() -> None:
    result = OcrResult(
        text="",
        engine=ENGINE_WINDOWS,
        lines=[OcrLine("Good", 92.0), OcrLine("Bad", 30.0)],
    )
    assert [line.text for line in result.low_confidence_lines] == ["Bad"]


# --- review surface formatting (OCR-4) -------------------------------------


def test_render_review_flags_low_confidence_lines() -> None:
    result = OcrResult(
        text="",
        engine=ENGINE_WINDOWS,
        language="en-US",
        lines=[OcrLine("Good line", 92.0), OcrLine("Bad line", 30.0)],
    )
    rendered = render_ocr_review(result)
    assert "Engine: windows" in rendered
    assert "Language: en-US" in rendered
    assert "1 of 2 lines need review" in rendered
    assert "[review 30%] Bad line" in rendered
    assert "Good line" in rendered


def test_render_review_without_lines_uses_text() -> None:
    result = OcrResult(text="line one\nline two\n", engine=ENGINE_WINDOWS)
    rendered = render_ocr_review(result)
    assert "Engine: windows" in rendered
    assert "line one" in rendered
    assert "line two" in rendered


def test_render_review_notes_all_good_lines() -> None:
    result = OcrResult(
        text="",
        engine=ENGINE_WINDOWS,
        lines=[OcrLine("Clean", 95.0)],
    )
    rendered = render_ocr_review(result)
    assert "All lines recognized with good confidence" in rendered
