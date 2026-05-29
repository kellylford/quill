from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.document import Document
from quill.core.sessions import (
    active_index_from_session,
    add_recent_session,
    build_session_payload,
    clear_recent_sessions,
    documents_from_session,
    load_recent_sessions,
    load_session,
    save_session,
    session_title,
)


def test_session_save_and_restore_roundtrip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    docs = [
        Document(text="alpha", path=tmp_path / "alpha.txt", modified=False),
        Document(
            text="beta",
            path=None,
            modified=True,
            encoding="utf-16",
            line_ending="\r\n",
            source_metadata={"source_kind": "text"},
        ),
    ]

    target = tmp_path / "sessions" / "demo.quill-session.json"
    payload = build_session_payload("Demo Session", 1, docs)
    save_session(target, payload, limit=5)

    loaded = load_session(target)
    restored = documents_from_session(loaded)

    assert session_title(loaded, "fallback") == "Demo Session"
    assert active_index_from_session(loaded, len(restored)) == 1
    assert restored[0].text == "alpha"
    assert restored[0].path == (tmp_path / "alpha.txt")
    assert restored[1].text == "beta"
    assert restored[1].encoding == "utf-16"
    assert restored[1].line_ending == "\r\n"
    assert restored[1].source_metadata == {"source_kind": "text"}
    assert load_recent_sessions() == [target.resolve()]


def test_recent_sessions_can_be_cleared(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    target = tmp_path / "sessions" / "one.quill-session.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")

    add_recent_session(target, limit=5)
    clear_recent_sessions()

    assert load_recent_sessions() == []
