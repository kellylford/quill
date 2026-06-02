"""AIBackend that routes generation to the user's configured provider (AI-13).

When the user has configured an AI connection (OpenAI, Claude, Gemini, Azure
OpenAI, OpenRouter, a custom OpenAI-compatible endpoint, or local/cloud Ollama),
this backend makes that provider actually produce the response, instead of
generation silently falling back to the bundled local model. It is a thin
adapter over ``quill.core.assistant_ai.generate_assistant_response`` so the
provider request building, endpoint-security check, verified TLS, retry, and
error taxonomy all live in one place.
"""

from __future__ import annotations

from quill.core.ai.backend import AIBackend
from quill.core.assistant_ai import (
    AssistantConnectionSettings,
    generate_assistant_response,
    load_assistant_api_key,
    load_assistant_connection_settings,
    provider_requires_api_key,
)


class ProviderChatBackend(AIBackend):
    """Generate via the configured cloud or Ollama provider."""

    name = "provider"

    def __init__(
        self,
        settings: AssistantConnectionSettings | None = None,
        api_key: str | None = None,
    ) -> None:
        self._settings = settings or load_assistant_connection_settings()
        self._api_key = api_key if api_key is not None else load_assistant_api_key()

    @property
    def settings(self) -> AssistantConnectionSettings:
        return self._settings

    def is_available(self) -> tuple[bool, str | None]:
        provider = self._settings.provider.strip().lower()
        if provider == "off":
            return False, "The AI provider is set to Off."
        if provider_requires_api_key(provider) and not self._api_key.strip():
            return False, "No API key is configured for this provider. Add one in AI settings."
        return True, None

    def respond(self, prompt: str) -> str:
        available, reason = self.is_available()
        if not available:
            raise RuntimeError(reason or "The AI provider is not available.")
        text, error = generate_assistant_response(self._settings, self._api_key, prompt)
        if error is not None:
            raise RuntimeError(error)
        return text or ""
