from __future__ import annotations

from pathlib import Path

import pytest

from quill.io.ocr import OcrCancelledError, OcrFailedError, OcrUnavailableError, ocr_image


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
