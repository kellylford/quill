from __future__ import annotations

from quill.core.ai.agent import AgentDecision
from quill.core.ai.assistant import Assistant


class _RecordingBackend:
    """Backend that records prompts and echoes a fixed structured reply."""

    name = "recording"

    def __init__(self, reply: str = "# Heading\n\nBody.") -> None:
        self.reply = reply
        self.prompts: list[str] = []

    def is_available(self) -> tuple[bool, None]:
        return (True, None)

    def respond(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.reply

    def decide(self, message, document, tool_ids, style_preamble=""):  # pragma: no cover
        return AgentDecision(action="answer", text="ok")


def test_structure_is_a_registered_operation() -> None:
    assert "structure" in Assistant(backend=_RecordingBackend()).available_operations()


def test_structure_transform_sends_ocr_text_and_returns_markdown() -> None:
    backend = _RecordingBackend(reply="# Title\n\nReflowed paragraph.")
    raw = "Some text broken\nacross OCR lines."

    result = Assistant(backend=backend).transform("structure", raw)

    assert result == "# Title\n\nReflowed paragraph."
    # The raw OCR text is handed to the model inside a structuring instruction.
    assert raw in backend.prompts[0]
    assert "Markdown" in backend.prompts[0]


def test_structure_preserves_wording_instruction_forbids_summarizing() -> None:
    backend = _RecordingBackend()
    Assistant(backend=backend).transform("structure", "hello world")

    prompt = backend.prompts[0].lower()
    assert "do not summarize" in prompt
