"""Native Windows OCR recognition via ``Windows.Media.Ocr`` (OCR-1).

This is a Windows-only, fully offline helper. It is imported lazily and behind
a guard by :func:`quill.io.ocr._import_windows_ocr`, so importing this module
fails cleanly (and the Windows backend reports itself unavailable) on machines
without the WinRT projection (``winsdk``) installed. No ``wx`` imports.
"""

from __future__ import annotations

from pathlib import Path

# Importing the WinRT projection at module load means this whole module fails to
# import when ``winsdk`` is absent, which is exactly how the Windows OCR backend
# detects unavailability. Keep these imports at module scope on purpose.
from winsdk.windows.globalization import Language  # type: ignore[import-not-found]
from winsdk.windows.graphics.imaging import (  # type: ignore[import-not-found]
    BitmapDecoder,
)
from winsdk.windows.media.ocr import OcrEngine  # type: ignore[import-not-found]
from winsdk.windows.storage import (  # type: ignore[import-not-found]
    FileAccessMode,
    StorageFile,
)

from quill.io.ocr import OcrLine


def recognize_with_windows_ocr(
    path: Path, language: str | None
) -> tuple[str, list[OcrLine]]:  # pragma: no cover - requires Windows + winsdk
    """Recognize text in ``path`` with the native Windows OCR engine.

    Returns the joined text and per-line :class:`OcrLine` records. Confidence is
    not exposed by ``Windows.Media.Ocr`` per line, so each line is reported with
    an unknown (-1) confidence, which the review surface treats as good.
    """
    import asyncio

    async def _run() -> tuple[str, list[OcrLine]]:
        storage_file = await StorageFile.get_file_from_path_async(str(path))
        stream = await storage_file.open_async(FileAccessMode.READ)
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        if language:
            engine = OcrEngine.try_create_from_language(Language(language))
        else:
            engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            from quill.io.ocr import OcrUnavailableError

            raise OcrUnavailableError(
                "No Windows OCR language pack is installed for the requested language."
            )
        ocr_result = await engine.recognize_async(bitmap)
        lines = [OcrLine(text=line.text, confidence=-1.0) for line in ocr_result.lines]
        joined = "\n".join(line.text for line in lines)
        return joined, lines

    return asyncio.run(_run())


__all__ = ["recognize_with_windows_ocr"]
