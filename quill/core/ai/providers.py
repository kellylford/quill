"""Provider catalog metadata for the AI assistant.

Pure, wx-free helpers describing each supported assistant provider: default
hosts and models, whether an API key is required, human-facing key labels and
help text, and recommended model lists/guidance. Extracted from
``assistant_ai`` to keep that module under the GATE-11 size budget (CQ-1) and to
give the provider catalog a single cohesive home.
"""

from __future__ import annotations

from dataclasses import dataclass

from quill.core.ai.model_manager import total_ram_gb


@dataclass(slots=True)
class ModelRecommendation:
    model: str
    framing: str
    reason: str


def default_host_for_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return "https://api.openai.com"
    if normalized == "claude":
        return "https://api.anthropic.com"
    if normalized == "openrouter":
        return "https://openrouter.ai/api"
    if normalized == "gemini":
        return "https://generativelanguage.googleapis.com"
    if normalized == "azure_openai":
        return "https://YOUR-RESOURCE-NAME.openai.azure.com"
    if normalized == "ollama_cloud":
        return "https://ollama.com"
    if normalized == "custom":
        return "https://api.openai.com"
    if normalized == "off":
        return ""
    return "http://localhost:11434"


def default_model_for_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return "gpt-4o-mini"
    if normalized == "claude":
        return "claude-3-5-sonnet-latest"
    if normalized == "openrouter":
        return "openrouter/auto"
    if normalized == "gemini":
        return "gemini-2.0-flash"
    if normalized == "azure_openai":
        return "gpt-4o-mini"
    if normalized == "ollama_cloud":
        return "qwen3"
    if normalized == "custom":
        return "gpt-4o-mini"
    if normalized == "off":
        return ""
    return "llama3.2:1b-instruct-q4_K_M"


def provider_requires_api_key(provider: str) -> bool:
    normalized = provider.strip().lower()
    return normalized in {
        "ollama_cloud",
        "openai",
        "claude",
        "openrouter",
        "gemini",
        "azure_openai",
        "custom",
    }


def provider_api_key_label(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return "OpenAI API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "claude":
        return "Claude API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "openrouter":
        return "OpenRouter API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "gemini":
        return "Google Gemini API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "azure_openai":
        return "Azure OpenAI API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "ollama_cloud":
        return "Ollama Cloud API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "custom":
        return "API key (OpenAI-compatible endpoint; Credential Manager or DPAPI fallback)"
    return "API key (optional; Credential Manager or DPAPI-encrypted fallback)"


def provider_help_text(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "ollama":
        return "Local Ollama: no key required. Best for private on-device workflows."
    if normalized == "openai":
        return "OpenAI: default host is prefilled. Add key and list models."
    if normalized == "claude":
        return "Claude: default host is prefilled and model discovery is supported."
    if normalized == "openrouter":
        return "OpenRouter: broad model routing with a single key."
    if normalized == "gemini":
        return "Gemini: default Google API endpoint is prefilled."
    if normalized == "azure_openai":
        return "Azure OpenAI: replace YOUR-RESOURCE-NAME with your Azure resource name."
    if normalized == "ollama_cloud":
        return "Ollama Cloud: add your cloud key to discover hosted models."
    if normalized == "custom":
        return "Advanced OpenAI-compatible endpoint: override host/model as needed."
    return "AI provider is off."


def recommended_models_for_provider(provider: str) -> list[str]:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"]
    if normalized == "claude":
        return ["claude-3-5-haiku-latest", "claude-3-5-sonnet-latest"]
    if normalized == "openrouter":
        return ["openrouter/auto", "anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]
    if normalized == "gemini":
        return ["gemini-2.0-flash", "gemini-1.5-pro"]
    if normalized == "azure_openai":
        return ["gpt-4o-mini", "gpt-4o", "o3-mini"]
    if normalized == "ollama_cloud":
        return ["qwen3", "gpt-oss:20b", "gemma3"]
    if normalized == "ollama":
        if total_ram_gb() < 8.0:
            return [
                "llama3.2:1b-instruct-q4_K_M",
                "qwen2.5:1.5b-instruct-q4_K_M",
                "qwen2.5:3b-instruct-q4_K_M",
            ]
        return [
            "qwen2.5:7b-instruct-q4_K_M",
            "llama3.1:8b-instruct-q4_K_M",
            "qwen2.5:3b-instruct-q4_K_M",
        ]
    return ["gpt-4o-mini", "claude-3-5-sonnet-latest", "gemini-2.0-flash"]


def recommended_model_guidance(provider: str) -> list[ModelRecommendation]:
    normalized = provider.strip().lower()
    if normalized == "ollama":
        if total_ram_gb() < 8.0:
            return [
                ModelRecommendation(
                    model="llama3.2:1b-instruct-q4_K_M",
                    framing="Fast local drafting",
                    reason="Best fit for lower-memory devices.",
                ),
                ModelRecommendation(
                    model="qwen2.5:1.5b-instruct-q4_K_M",
                    framing="Balanced local writing",
                    reason="Slightly stronger output with modest resource use.",
                ),
            ]
        return [
            ModelRecommendation(
                model="qwen2.5:7b-instruct-q4_K_M",
                framing="Quality-focused local editing",
                reason="Higher quality while staying practical for local runs.",
            ),
            ModelRecommendation(
                model="llama3.1:8b-instruct-q4_K_M",
                framing="General local assistant",
                reason="Reliable for rewriting, summarizing, and grammar tasks.",
            ),
        ]
    if normalized == "openai":
        return [
            ModelRecommendation(
                model="gpt-4o-mini",
                framing="Cost-aware daily use",
                reason="Fast and efficient for most writing tasks.",
            ),
            ModelRecommendation(
                model="gpt-4.1",
                framing="High-quality reasoning",
                reason="Best for complex transformations and nuanced editing.",
            ),
        ]
    if normalized == "claude":
        return [
            ModelRecommendation(
                model="claude-3-5-haiku-latest",
                framing="Speed-first drafting",
                reason="Responsive for rapid prompt iteration.",
            ),
            ModelRecommendation(
                model="claude-3-5-sonnet-latest",
                framing="Deep writing review",
                reason="Stronger reasoning for long-form revision.",
            ),
        ]
    if normalized == "openrouter":
        return [
            ModelRecommendation(
                model="openrouter/auto",
                framing="Automatic routing",
                reason="Lets the endpoint select a good model for each request.",
            ),
            ModelRecommendation(
                model="openai/gpt-4o-mini",
                framing="Predictable speed and cost",
                reason="Good explicit fallback when you want stable behavior.",
            ),
        ]
    if normalized == "gemini":
        return [
            ModelRecommendation(
                model="gemini-2.0-flash",
                framing="Fast cloud drafting",
                reason="Strong default for low-latency writing help.",
            ),
            ModelRecommendation(
                model="gemini-1.5-pro",
                framing="Long-context analysis",
                reason="Better for larger prompts and deeper synthesis.",
            ),
        ]
    if normalized == "azure_openai":
        return [
            ModelRecommendation(
                model="gpt-4o-mini",
                framing="Enterprise default",
                reason="Balanced quality/cost for managed Azure deployments.",
            ),
            ModelRecommendation(
                model="o3-mini",
                framing="Reasoning-heavy tasks",
                reason="Useful for multi-step editing and refactoring prompts.",
            ),
        ]
    return [
        ModelRecommendation(
            model=name,
            framing="General recommendation",
            reason="Suggested model for this provider.",
        )
        for name in recommended_models_for_provider(provider)
    ]
