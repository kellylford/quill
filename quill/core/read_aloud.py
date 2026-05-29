from __future__ import annotations

import re
import threading
from collections.abc import Callable
from dataclasses import dataclass

try:
    import pyttsx3  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional runtime dependency
    pyttsx3 = None


@dataclass(frozen=True, slots=True)
class VoiceOption:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class SentenceSpan:
    start: int
    end: int


def list_voices() -> list[VoiceOption]:
    if pyttsx3 is None:
        return []
    engine = pyttsx3.init()
    try:
        voices = []
        for voice in engine.getProperty("voices") or []:
            voice_id = str(getattr(voice, "id", "")).strip()
            if not voice_id:
                continue
            name = str(getattr(voice, "name", voice_id)).strip() or voice_id
            voices.append(VoiceOption(id=voice_id, name=name))
        return voices
    finally:
        engine.stop()


def sentence_spans(text: str) -> list[SentenceSpan]:
    spans: list[SentenceSpan] = []
    for match in re.finditer(r".+?(?:[.!?]+(?:\s+|$)|\n+|$)", text, re.DOTALL):
        start, end = match.span()
        if text[start:end].strip():
            spans.append(SentenceSpan(start=start, end=end))
    if not spans and text.strip():
        spans.append(SentenceSpan(0, len(text)))
    return spans


class ReadAloudUnavailableError(RuntimeError):
    pass


class ReadAloudController:
    def __init__(self) -> None:
        self._state = "idle"
        self._cursor = 0
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def cursor(self) -> int:
        with self._lock:
            return self._cursor

    def start(
        self,
        text: str,
        cursor: int,
        voice_id: str,
        end: int | None = None,
        on_progress: Callable[[int, int], None] | None = None,
        on_state_change: Callable[[str], None] | None = None,
    ) -> None:
        if pyttsx3 is None:
            raise ReadAloudUnavailableError("pyttsx3 is not available")
        self.stop()
        spans = [span for span in sentence_spans(text) if span.end > cursor]
        if end is not None:
            spans = [span for span in spans if span.start < end]
        if not spans:
            stop_at = len(text) if end is None else min(len(text), max(cursor, end))
            spans = [SentenceSpan(cursor, stop_at)]
        with self._lock:
            self._state = "playing"
            self._cursor = cursor
        self._stop_event.clear()
        self._pause_event.clear()

        def worker() -> None:
            engine = pyttsx3.init()
            try:
                if voice_id:
                    engine.setProperty("voice", voice_id)
                for span in spans:
                    if self._stop_event.is_set():
                        break
                    if self._pause_event.is_set():
                        break
                    sentence = text[span.start : span.end].strip()
                    if not sentence:
                        continue
                    if on_progress is not None:
                        on_progress(span.start, span.end)
                    engine.say(sentence)
                    engine.runAndWait()
                    with self._lock:
                        self._cursor = span.end
                with self._lock:
                    if self._pause_event.is_set():
                        self._state = "paused"
                    else:
                        self._state = "idle"
                if on_state_change is not None:
                    on_state_change(self.state)
            finally:
                engine.stop()

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def pause(self) -> None:
        with self._lock:
            if self._state != "playing":
                return
            self._state = "paused"
        self._pause_event.set()

    def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.clear()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.2)
        with self._lock:
            self._state = "idle"
        self._thread = None
