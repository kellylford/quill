from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from quill.io.ocr import (
    ENGINE_AUTO,
    ENGINE_TESSERACT,
    ENGINE_WINDOWS,
    CancelFn,
    OcrCancelledError,
    OcrFailedError,
    OcrLanguageError,
    OcrLine,
    OcrResult,
    OcrUnavailableError,
    ProgressFn,
    available_engines,
    ocr_image,
    parse_tesseract_tsv,
    render_ocr_review,
    select_engine,
    validate_ocr_language,
)


def test_ocr_image_raises_when_tesseract_is_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("quill.io.ocr.shutil.which", lambda _name: None)

    with pytest.raises(OcrUnavailableError):
        ocr_image(tmp_path / "sample.png")


def test_ocr_image_returns_text(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("quill.io.ocr.shutil.which", lambda _name: "tesseract")

    class CompletedProcess:
        def __init__(self) -> None:
            self.calls = 0

        def poll(self):
            self.calls += 1
            if self.calls == 1:
                return None
            return 0

        def communicate(self):
            return ("Recognized text", "")

        def terminate(self):
            return None

        def wait(self):
            return 0

    monkeypatch.setattr("quill.io.ocr.subprocess.Popen", lambda *args, **kwargs: CompletedProcess())

    result = ocr_image(tmp_path / "sample.png")

    assert result.engine == "tesseract"
    assert result.text == "Recognized text\n"


def test_ocr_image_raises_on_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("quill.io.ocr.shutil.which", lambda _name: "tesseract")

    class CompletedProcess:
        def __init__(self) -> None:
            self.calls = 0

        def poll(self):
            self.calls += 1
            if self.calls == 1:
                return None
            return 1

        def communicate(self):
            return ("", "bad image")

        def terminate(self):
            return None

        def wait(self):
            return 0

    monkeypatch.setattr("quill.io.ocr.subprocess.Popen", lambda *args, **kwargs: CompletedProcess())

    with pytest.raises(OcrFailedError, match="bad image"):
        ocr_image(tmp_path / "sample.png")


def test_ocr_image_can_be_cancelled(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("quill.io.ocr.shutil.which", lambda _name: "tesseract")

    class CompletedProcess:
        def __init__(self) -> None:
            self.calls = 0

        def poll(self):
            self.calls += 1
            if self.calls == 1:
                return None
            return 0

        def communicate(self):
            return ("", "")

        def terminate(self):
            return None

        def wait(self):
            return 0

    monkeypatch.setattr("quill.io.ocr.subprocess.Popen", lambda *args, **kwargs: CompletedProcess())

    calls = {"count": 0}

    def cancel_requested() -> bool:
        calls["count"] += 1
        return calls["count"] > 1

    with pytest.raises(OcrCancelledError):
        ocr_image(tmp_path / "sample.png", cancel_requested=cancel_requested)


@pytest.mark.parametrize("code", ["eng", "fra", "eng+fra", "chi_sim", "aze_cyrl", "deu+eng+spa"])
def test_validate_ocr_language_accepts_known_shapes(code: str) -> None:
    assert validate_ocr_language(code) == code


@pytest.mark.parametrize(
    "code",
    [
        "",
        "  ",
        "-psm",
        "--config",
        "eng;rm -rf",
        "eng/Latin",
        "ENG",
        "e n g",
        "eng+",
        "1234",
    ],
)
def test_validate_ocr_language_rejects_bad_input(code: str) -> None:
    with pytest.raises(OcrLanguageError):
        validate_ocr_language(code)


def test_validate_ocr_language_strips_surrounding_whitespace() -> None:
    assert validate_ocr_language("  eng+fra  ") == "eng+fra"


def test_ocr_image_rejects_malicious_language(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("quill.io.ocr.shutil.which", lambda _name: "tesseract")
    # Should never reach Popen because validation fails first.
    monkeypatch.setattr(
        "quill.io.ocr.subprocess.Popen",
        lambda *args, **kwargs: pytest.fail("Popen must not run with an invalid language"),
    )
    with pytest.raises(OcrLanguageError):
        ocr_image(tmp_path / "sample.png", language="--config")


# --- backend-pluggable selection (OCR-1, OCR-2) ----------------------------


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
        return OcrResult(
            text=self.text + "\n",
            engine=self.backend_id,
            language=language or "",
            lines=[OcrLine(text=self.text, confidence=95.0)],
        )


def _backends(windows: bool, tesseract: bool) -> dict[str, _FakeBackend]:
    return {
        ENGINE_WINDOWS: _FakeBackend(ENGINE_WINDOWS, available=windows, text="windows text"),
        ENGINE_TESSERACT: _FakeBackend(ENGINE_TESSERACT, available=tesseract, text="tess text"),
    }


def test_auto_prefers_windows_when_available() -> None:
    assert select_engine(ENGINE_AUTO, _backends(windows=True, tesseract=True)) == ENGINE_WINDOWS


def test_auto_falls_back_to_tesseract() -> None:
    assert select_engine(ENGINE_AUTO, _backends(windows=False, tesseract=True)) == ENGINE_TESSERACT


def test_auto_raises_when_no_backend_available() -> None:
    with pytest.raises(OcrUnavailableError):
        select_engine(ENGINE_AUTO, _backends(windows=False, tesseract=False))


def test_explicit_engine_honored() -> None:
    assert select_engine(ENGINE_TESSERACT, _backends(windows=True, tesseract=True)) == (
        ENGINE_TESSERACT
    )


def test_explicit_unavailable_engine_points_to_setup() -> None:
    with pytest.raises(OcrUnavailableError) as excinfo:
        select_engine(ENGINE_WINDOWS, _backends(windows=False, tesseract=True))
    assert "setup" in str(excinfo.value).lower()


def test_unknown_engine_rejected() -> None:
    with pytest.raises(OcrUnavailableError):
        select_engine("banana", _backends(windows=True, tesseract=True))


def test_available_engines_filters_by_availability() -> None:
    assert available_engines(_backends(windows=False, tesseract=True)) == [ENGINE_TESSERACT]


def test_ocr_image_runs_selected_backend() -> None:
    result = ocr_image(
        Path("x.png"), engine=ENGINE_AUTO, backends=_backends(windows=True, tesseract=True)
    )
    assert result.engine == ENGINE_WINDOWS
    assert result.text.strip() == "windows text"


def test_ocr_image_unavailable_path_with_backends() -> None:
    with pytest.raises(OcrUnavailableError):
        ocr_image(Path("x.png"), backends=_backends(windows=False, tesseract=False))


# --- tesseract tsv parsing (per-line confidence, OCR-1) ---------------------


def test_parse_tesseract_tsv_builds_lines_with_confidence() -> None:
    tsv = (
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\t"
        "left\ttop\twidth\theight\tconf\ttext\n"
        "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t90\tHello\n"
        "5\t1\t1\t1\t1\t2\t0\t0\t10\t10\t80\tworld\n"
        "5\t1\t1\t1\t2\t1\t0\t0\t10\t10\t40\tfuzzy\n"
    )
    text, lines = parse_tesseract_tsv(tsv)
    assert text == "Hello world\nfuzzy"
    assert lines[0].text == "Hello world"
    assert lines[0].confidence == pytest.approx(85.0)
    assert lines[1].is_low_confidence is True  # 40 < threshold


def test_parse_tesseract_tsv_handles_plain_text() -> None:
    text, lines = parse_tesseract_tsv("just some text\n")
    assert text == "just some text"
    assert lines == []


# --- review surface formatting (OCR-4) -------------------------------------


def test_render_review_flags_low_confidence_lines() -> None:
    result = OcrResult(
        text="",
        engine="tesseract",
        language="eng",
        lines=[OcrLine("Good line", 92.0), OcrLine("Bad line", 30.0)],
    )
    rendered = render_ocr_review(result)
    assert "Engine: tesseract" in rendered
    assert "Language: eng" in rendered
    assert "1 of 2 lines need review" in rendered
    assert "[review 30%] Bad line" in rendered
    assert "Good line" in rendered


def test_render_review_without_lines_uses_text() -> None:
    result = OcrResult(text="line one\nline two\n", engine="windows")
    rendered = render_ocr_review(result)
    assert "Engine: windows" in rendered
    assert "line one" in rendered
    assert "line two" in rendered
