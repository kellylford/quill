from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

try:  # pragma: no cover - Windows-only runtime hook
    # `launch_windows_dictation` is set to the real Windows shell
    # launcher when running on Windows. On macOS/Linux the import
    # raises ImportError and we fall back to ``None`` so the public
    # methods return a clean ``DictationUnavailableError`` instead of
    # crashing at import time. Do not assume the symbol exists outside
    # Windows; gate every call on ``launch_windows_dictation is not None``.
    from quill.platform.windows.dictation import (
        launch_windows_dictation as _launch_windows_dictation,
    )

    launch_windows_dictation: Callable[[], None] | None = _launch_windows_dictation
except ImportError:  # pragma: no cover - non-Windows fallback
    launch_windows_dictation = None


@dataclass(frozen=True, slots=True)
class DictationSettings:
    engine: str = "windows"
    language: str = "en-US"
    model: str = "default"
    device_index: int | None = None


class DictationUnavailableError(RuntimeError):
    pass


class DictationController:
    def __init__(self) -> None:
        self._state = "idle"
        self._stopper: Callable[..., None] | None = None
        self._segments: list[str] = []

    @property
    def state(self) -> str:
        return self._state

    def start(
        self,
        settings: DictationSettings,
        *,
        on_state_change: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        if launch_windows_dictation is None:
            raise DictationUnavailableError("Windows dictation is only available on Windows")
        try:
            launch_windows_dictation()
        except OSError as error:
            if on_error is not None:
                on_error(str(error))
            raise DictationUnavailableError(str(error)) from error
        self._state = "listening"

    def stop(self, *, on_state_change: Callable[[str], None] | None = None) -> str:
        if self._state == "listening" and launch_windows_dictation is not None:
            try:
                launch_windows_dictation()
            except OSError:
                pass
        self._state = "idle"
        transcript = "".join(self._segments).strip()
        self._segments.clear()
        if on_state_change is not None:
            on_state_change(self._state)
        return transcript


def _transcribe_audio(recognizer: Any, audio: object, settings: DictationSettings) -> str:
    """Transcribe one audio chunk using the configured local recognizer engine."""
    engine = (settings.engine or "").strip().lower()
    if engine == "whisper":
        return str(
            recognizer.recognize_whisper(
                audio,
                model=settings.model,
                language=settings.language,
            )
        )
    if engine == "vosk":
        payload = recognizer.recognize_vosk(audio)
        if isinstance(payload, str):
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                return payload.strip()
            return str(data.get("text", "")).strip()
        if isinstance(payload, dict):
            return str(payload.get("text", "")).strip()
        return ""
    raise DictationUnavailableError(f"Unsupported dictation engine: {settings.engine}")


def list_dictation_devices() -> list[str]:
    return []
