from __future__ import annotations

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
        command.extend(["-l", language])
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
