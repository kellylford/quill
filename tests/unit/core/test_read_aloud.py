from __future__ import annotations

from types import SimpleNamespace

from quill.core import read_aloud as read_aloud_module
from quill.core.read_aloud import ReadAloudController, list_voices, sentence_spans


def test_sentence_spans() -> None:
    spans = sentence_spans("One. Two! Three?")
    assert [(span.start, span.end) for span in spans] == [(0, 5), (5, 10), (10, 16)]


def test_list_voices_uses_backend(monkeypatch) -> None:
    class FakeVoice:
        id = "voice-1"
        name = "Voice 1"

    class FakeEngine:
        def __init__(self) -> None:
            self.spoken: list[str] = []
            self.properties: dict[str, object] = {}

        def getProperty(self, name: str):  # noqa: N802
            if name == "voices":
                return [FakeVoice()]
            return None

        def setProperty(self, name: str, value: object) -> None:  # noqa: N802
            self.properties[name] = value

        def say(self, text: str) -> None:
            self.spoken.append(text)

        def runAndWait(self) -> None:  # noqa: N802
            return None

        def stop(self) -> None:
            return None

    engine = FakeEngine()
    monkeypatch.setattr(read_aloud_module, "pyttsx3", SimpleNamespace(init=lambda: engine))

    voices = list_voices()
    assert [(voice.id, voice.name) for voice in voices] == [("voice-1", "Voice 1")]


def test_read_aloud_controller_speaks_sentences(monkeypatch) -> None:
    class FakeEngine:
        def __init__(self) -> None:
            self.spoken: list[str] = []
            self.properties: dict[str, object] = {}

        def getProperty(self, name: str):  # noqa: N802
            return []

        def setProperty(self, name: str, value: object) -> None:  # noqa: N802
            self.properties[name] = value

        def say(self, text: str) -> None:
            self.spoken.append(text)

        def runAndWait(self) -> None:  # noqa: N802
            return None

        def stop(self) -> None:
            return None

    engine = FakeEngine()
    monkeypatch.setattr(read_aloud_module, "pyttsx3", SimpleNamespace(init=lambda: engine))

    controller = ReadAloudController()
    controller.start("One. Two!", 0, "voice-1")
    assert controller._thread is not None
    controller._thread.join(timeout=1)

    assert engine.properties["voice"] == "voice-1"
    assert engine.spoken == ["One.", "Two!"]
