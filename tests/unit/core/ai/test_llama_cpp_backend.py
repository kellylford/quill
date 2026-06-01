from __future__ import annotations

import builtins

from quill.core.ai.llama_cpp_backend import LlamaCppBackend


def _patched_import(
    monkeypatch,
    side_effect: Exception,
) -> None:
    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals=None,  # noqa: A002
        locals=None,  # noqa: A002
        fromlist=(),
        level: int = 0,
    ):
        if name == "llama_cpp":
            raise side_effect
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_is_available_reports_missing_dependency(monkeypatch) -> None:
    _patched_import(monkeypatch, ImportError("missing llama_cpp"))
    available, reason = LlamaCppBackend().is_available()
    assert available is False
    assert reason is not None
    assert "not installed" in reason


def test_is_available_reports_native_loader_failure(monkeypatch) -> None:
    _patched_import(monkeypatch, OSError(-1073741795, "Windows Error 0xc000001d"))
    available, reason = LlamaCppBackend().is_available()
    assert available is False
    assert reason is not None
    assert "0xc000001d" in reason


def test_load_raises_runtime_error_for_native_loader_failure(monkeypatch) -> None:
    _patched_import(monkeypatch, OSError(-1073741795, "Windows Error 0xc000001d"))
    backend = LlamaCppBackend(model_path="dummy.gguf")
    try:
        backend._load()
    except RuntimeError as exc:
        assert "0xc000001d" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for native loader failure")


class _StubLlm:
    def __init__(self, response: object) -> None:
        self._response = response

    def create_chat_completion(self, **_kwargs):
        return self._response


def _backend_with_response(response: object) -> LlamaCppBackend:
    backend = LlamaCppBackend(model_path="dummy.gguf")
    backend._llm = _StubLlm(response)
    return backend


def test_complete_extracts_well_formed_content() -> None:
    backend = _backend_with_response(
        {"choices": [{"message": {"content": "  hello world  "}}]}
    )
    assert backend.respond("hi") == "hello world"


def test_complete_handles_missing_choices(monkeypatch) -> None:
    # Regression for BUG-5: a malformed/version-mismatched response must not
    # raise KeyError/IndexError; surface a friendly RuntimeError instead.
    for bad in ({}, {"choices": []}, {"choices": [{}]}, {"choices": [{"message": {}}]}, None):
        backend = _backend_with_response(bad)
        try:
            backend.respond("hi")
        except RuntimeError as exc:
            assert "unexpected response shape" in str(exc)
        else:
            raise AssertionError(f"Expected RuntimeError for malformed response: {bad!r}")


def test_complete_treats_null_content_as_empty() -> None:
    backend = _backend_with_response({"choices": [{"message": {"content": None}}]})
    assert backend.respond("hi") == ""

