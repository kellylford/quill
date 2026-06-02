"""Backend-pluggable OCR (image-to-text) engine (OCR-1, OCR-2).

This module is UI-framework-agnostic (no ``wx``). It exposes a small backend
contract so text can be pulled from images either fully offline through the
native ``Windows.Media.Ocr`` runtime (zero-install) or through an opt-in
Tesseract install, with a shared :class:`OcrResult` that carries the recognized
text plus per-line confidence. Backend selection honors an ``engine``
preference (``auto``/``windows``/``tesseract``); ``auto`` prefers the native
Windows backend and falls back to Tesseract when present. When no usable
backend exists the engine raises :class:`OcrUnavailableError` with a message
that points the user back to OCR onboarding rather than failing silently.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class OcrUnavailableError(RuntimeError):
    pass


class OcrFailedError(RuntimeError):
    pass


class OcrCancelledError(RuntimeError):
    pass


class OcrLanguageError(ValueError):
    """Raised when a requested OCR language code is not a valid Tesseract code."""


#: Engine preference values accepted by :func:`ocr_image` and the ``ocr_engine``
#: setting (OCR-2).
ENGINE_AUTO = "auto"
ENGINE_WINDOWS = "windows"
ENGINE_TESSERACT = "tesseract"
ENGINE_CHOICES = (ENGINE_AUTO, ENGINE_WINDOWS, ENGINE_TESSERACT)

#: Lines whose confidence falls below this (on a 0-100 scale) are flagged for
#: review in the OCR review surface (OCR-4). A confidence of -1 means the
#: backend did not report one and is never treated as low.
LOW_CONFIDENCE_THRESHOLD = 60.0


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
class OcrLine:
    """One recognized line of text with an optional confidence (0-100)."""

    text: str
    confidence: float = -1.0

    @property
    def is_low_confidence(self) -> bool:
        return 0.0 <= self.confidence < LOW_CONFIDENCE_THRESHOLD


@dataclass(slots=True)
class OcrResult:
    text: str
    engine: str
    executable: str = ""
    language: str = ""
    lines: list[OcrLine] = field(default_factory=list)

    @property
    def low_confidence_lines(self) -> list[OcrLine]:
        """Recognized lines flagged below the confidence threshold (OCR-4)."""
        return [line for line in self.lines if line.is_low_confidence]


# Progress/cancel callbacks shared by every backend.
ProgressFn = Callable[[str], None]
CancelFn = Callable[[], bool]


class OcrBackend(Protocol):
    """The contract every OCR backend implements.

    ``backend_id`` is the stable engine id (``windows``/``tesseract``);
    ``is_available`` reports whether the backend can run on this machine right
    now (its runtime/binary is present); ``run`` performs recognition.
    """

    backend_id: str

    def is_available(self) -> bool: ...

    def run(
        self,
        path: Path,
        language: str | None,
        on_progress: ProgressFn | None,
        cancel_requested: CancelFn | None,
    ) -> OcrResult: ...


def parse_tesseract_tsv(tsv: str) -> tuple[str, list[OcrLine]]:
    """Parse Tesseract ``tsv`` output into text plus per-line confidence.

    Tesseract emits one row per recognized token with a ``level`` column; word
    tokens (level 5) carry the text and confidence. We rebuild each line from
    its words and average their confidences. Returns the joined text and the
    list of :class:`OcrLine`. Malformed rows are skipped defensively.
    """
    rows = tsv.splitlines()
    if not rows:
        return "", []
    header = rows[0].split("\t")
    try:
        idx_level = header.index("level")
        idx_line = header.index("line_num")
        idx_block = header.index("block_num")
        idx_par = header.index("par_num")
        idx_conf = header.index("conf")
        idx_text = header.index("text")
    except ValueError:
        # Not a recognized TSV header; treat the whole blob as plain text.
        return tsv.rstrip(), []
    grouped: dict[tuple[str, str, str], list[tuple[str, float]]] = {}
    order: list[tuple[str, str, str]] = []
    for raw in rows[1:]:
        cols = raw.split("\t")
        if len(cols) <= idx_text:
            continue
        if cols[idx_level] != "5":  # only word tokens carry text + conf
            continue
        word = cols[idx_text]
        if not word.strip():
            continue
        try:
            conf = float(cols[idx_conf])
        except (TypeError, ValueError):
            conf = -1.0
        key = (cols[idx_block], cols[idx_par], cols[idx_line])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append((word, conf))
    lines: list[OcrLine] = []
    for key in order:
        words = grouped[key]
        text = " ".join(word for word, _ in words)
        confs = [conf for _, conf in words if conf >= 0]
        confidence = sum(confs) / len(confs) if confs else -1.0
        lines.append(OcrLine(text=text, confidence=confidence))
    joined = "\n".join(line.text for line in lines)
    return joined, lines


@dataclass(slots=True)
class TesseractBackend:
    """OCR backend that shells out to a user-installed Tesseract (OCR-2)."""

    backend_id: str = ENGINE_TESSERACT

    def is_available(self) -> bool:
        return shutil.which("tesseract") is not None

    def run(
        self,
        path: Path,
        language: str | None,
        on_progress: ProgressFn | None,
        cancel_requested: CancelFn | None,
    ) -> OcrResult:
        executable = shutil.which("tesseract")
        if executable is None:
            raise OcrUnavailableError(
                "Tesseract OCR is not installed or not on PATH. "
                "Turn it on in OCR setup, or choose the native Windows engine."
            )
        validated = validate_ocr_language(language) if language else ""
        command = [executable, str(path), "stdout", "tsv"]
        if validated:
            command.extend(["-l", validated])
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
                text, lines = parse_tesseract_tsv(stdout)
                return OcrResult(
                    text=text.rstrip() + "\n" if text else "",
                    engine=ENGINE_TESSERACT,
                    executable=executable,
                    language=validated,
                    lines=lines,
                )
            time.sleep(0.1)


@dataclass(slots=True)
class WindowsOcrBackend:
    """Native ``Windows.Media.Ocr`` backend, fully offline and zero-install (OCR-1).

    Recognition uses the WinRT OCR engine via ``winsdk``/``winrt`` when present.
    On a non-Windows machine or without the projection installed,
    :meth:`is_available` returns ``False`` so selection falls back cleanly.
    """

    backend_id: str = ENGINE_WINDOWS

    def is_available(self) -> bool:
        return _import_windows_ocr() is not None

    def run(
        self,
        path: Path,
        language: str | None,
        on_progress: ProgressFn | None,
        cancel_requested: CancelFn | None,
    ) -> OcrResult:
        recognize = _import_windows_ocr()
        if recognize is None:
            raise OcrUnavailableError(
                "The native Windows OCR engine is not available on this machine. "
                "Open OCR setup to choose an engine."
            )
        if on_progress is not None:
            on_progress("Running OCR...")
        if cancel_requested is not None and cancel_requested():
            raise OcrCancelledError("OCR cancelled.")
        text, lines = recognize(path, language)
        return OcrResult(
            text=text.rstrip() + "\n" if text else "",
            engine=ENGINE_WINDOWS,
            executable="",
            language=language or "",
            lines=lines,
        )


def _import_windows_ocr() -> Callable[[Path, str | None], tuple[str, list[OcrLine]]] | None:
    """Return a callable that runs WinRT OCR, or ``None`` when unavailable.

    Kept isolated so the rest of the module never imports a platform-only
    dependency at module load and remains testable on any OS.
    """
    try:  # pragma: no cover - platform/runtime dependent
        from quill.platform.windows.windows_ocr import recognize_with_windows_ocr
    except Exception:
        return None
    return recognize_with_windows_ocr  # pragma: no cover


def default_backends() -> dict[str, OcrBackend]:
    """The built-in OCR backends keyed by engine id."""
    return {
        ENGINE_WINDOWS: WindowsOcrBackend(),
        ENGINE_TESSERACT: TesseractBackend(),
    }


def available_engines(backends: Mapping[str, OcrBackend] | None = None) -> list[str]:
    """Engine ids whose backend can run on this machine right now."""
    registry = dict(backends) if backends is not None else default_backends()
    return [engine for engine, backend in registry.items() if backend.is_available()]


def select_engine(
    preference: str,
    backends: Mapping[str, OcrBackend] | None = None,
) -> str:
    """Resolve an engine ``preference`` to a concrete, available engine id.

    ``auto`` prefers the native Windows backend and falls back to Tesseract.
    An explicit ``windows``/``tesseract`` preference is honored when available.
    Raises :class:`OcrUnavailableError` (pointing back to OCR setup) when the
    requested engine, or any engine for ``auto``, is unavailable.
    """
    registry = dict(backends) if backends is not None else default_backends()
    pref = (preference or ENGINE_AUTO).strip().lower()
    if pref == ENGINE_AUTO:
        for engine in (ENGINE_WINDOWS, ENGINE_TESSERACT):
            backend = registry.get(engine)
            if backend is not None and backend.is_available():
                return engine
        raise OcrUnavailableError(
            "No OCR engine is available. Open OCR setup to install Tesseract "
            "or enable the native Windows engine."
        )
    backend = registry.get(pref)
    if backend is None:
        raise OcrUnavailableError(f"Unknown OCR engine: {preference!r}.")
    if not backend.is_available():
        raise OcrUnavailableError(
            f"The {pref} OCR engine is not available on this machine. "
            "Open OCR setup to choose another engine."
        )
    return pref


def ocr_image(
    path: Path,
    language: str | None = None,
    engine: str = ENGINE_AUTO,
    on_progress: ProgressFn | None = None,
    cancel_requested: CancelFn | None = None,
    backends: Mapping[str, OcrBackend] | None = None,
) -> OcrResult:
    """Recognize text in ``path`` using the selected/available OCR backend.

    ``engine`` is an ``ocr_engine`` preference (``auto``/``windows``/
    ``tesseract``). Selection and availability are resolved by
    :func:`select_engine`; the chosen backend performs recognition and returns
    an :class:`OcrResult` with text and per-line confidence.
    """
    registry = dict(backends) if backends is not None else default_backends()
    chosen = select_engine(engine, registry)
    backend = registry[chosen]
    return backend.run(path, language, on_progress, cancel_requested)


def render_ocr_review(result: OcrResult) -> str:
    """Render an OCR result as plain text for the accessible review surface (OCR-4).

    The header names the engine and language and notes how many lines fell
    below the confidence threshold; low-confidence lines are marked inline with
    a leading flag so a screen-reader user can find them quickly.
    """
    header_bits = [f"Engine: {result.engine or 'unknown'}"]
    if result.language:
        header_bits.append(f"Language: {result.language}")
    low = result.low_confidence_lines
    if result.lines:
        if low:
            header_bits.append(f"{len(low)} of {len(result.lines)} lines need review")
        else:
            header_bits.append("All lines recognized with good confidence")
    header = " | ".join(header_bits)
    if result.lines:
        body_lines = [
            f"[review {line.confidence:.0f}%] {line.text}" if line.is_low_confidence else line.text
            for line in result.lines
        ]
    else:
        body_lines = result.text.splitlines()
    return header + "\n\n" + "\n".join(body_lines)


__all__ = [
    "ENGINE_AUTO",
    "ENGINE_CHOICES",
    "ENGINE_TESSERACT",
    "ENGINE_WINDOWS",
    "LOW_CONFIDENCE_THRESHOLD",
    "CancelFn",
    "OcrBackend",
    "OcrCancelledError",
    "OcrFailedError",
    "OcrLanguageError",
    "OcrLine",
    "OcrResult",
    "OcrUnavailableError",
    "ProgressFn",
    "TesseractBackend",
    "WindowsOcrBackend",
    "available_engines",
    "default_backends",
    "ocr_image",
    "parse_tesseract_tsv",
    "render_ocr_review",
    "select_engine",
    "validate_ocr_language",
]
