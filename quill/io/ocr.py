from __future__ import annotations

import re
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


class OcrUnavailableError(RuntimeError):
    pass


class OcrFailedError(RuntimeError):
    pass


class OcrCancelledError(RuntimeError):
    pass


class OcrLanguageError(ValueError):
    """Raised when a requested OCR language code is not a valid Tesseract code."""


# Tesseract language codes are lowercase ISO 639-2/3 codes, optionally with a
# script suffix (chi_sim, aze_cyrl), and may be combined with '+' (eng+fra).
# Validating against this grammar rejects option injection like '-psm' or
# '--config' and any other unexpected input before it reaches the CLI.
_LANGUAGE_SEGMENT = re.compile(r"^[a-z]{2,4}(_[a-z]+)*$")
_MAX_LANGUAGE_SEGMENTS = 8


def validate_ocr_language(language: str) -> str:
    """Return a normalized, validated Tesseract language string.

    Raises OcrLanguageError if any segment is not a well-formed language code.
    """
    cleaned = language.strip()
    if not cleaned:
        raise OcrLanguageError("OCR language cannot be empty.")
    segments = cleaned.split("+")
    if len(segments) > _MAX_LANGUAGE_SEGMENTS:
        raise OcrLanguageError("Too many OCR language codes requested.")
    for segment in segments:
        if not _LANGUAGE_SEGMENT.match(segment):
            raise OcrLanguageError(
                f"Unknown OCR language code: {segment!r}. "
                "Use Tesseract codes such as 'eng', 'fra', or 'eng+fra'."
            )
    return "+".join(segments)


@dataclass(slots=True)
class OcrResult:
    text: str
    engine: str
    executable: str


def ocr_image(
    path: Path,
    language: str | None = None,
    on_progress: Callable[[str], None] | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> OcrResult:
    executable = shutil.which("tesseract")
    if executable is None:
        raise OcrUnavailableError("Tesseract OCR is not installed or not on PATH.")
    command = [executable, str(path), "stdout"]
    if language:
        command.extend(["-l", validate_ocr_language(language)])
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if on_progress is not None:
        on_progress("Running OCR...")
    while True:
        if cancel_requested is not None and cancel_requested():
            process.terminate()
            process.wait()
            raise OcrCancelledError("OCR cancelled.")
        return_code = process.poll()
        if return_code is not None:
            stdout, stderr = process.communicate()
            if return_code != 0:
                message = stderr.strip() or stdout.strip() or "OCR failed."
                raise OcrFailedError(message)
            return OcrResult(
                text=stdout.rstrip() + "\n",
                engine="tesseract",
                executable=executable,
            )
        time.sleep(0.1)
