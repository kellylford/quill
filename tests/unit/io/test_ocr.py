from __future__ import annotations

from pathlib import Path

import pytest

from quill.io.ocr import (
    OcrCancelledError,
    OcrFailedError,
    OcrLanguageError,
    OcrUnavailableError,
    ocr_image,
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

