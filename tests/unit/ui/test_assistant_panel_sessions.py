"""Issue #130: AI chat exchanges are recorded to the branch-tree session log so
the Session Branches browser is populated instead of always empty."""

from __future__ import annotations

import quill.core.ai.sessions as sessions
from quill.ui.assistant_panel import AskQuillChatDialog


def _dialog() -> AskQuillChatDialog:
    dialog = AskQuillChatDialog.__new__(AskQuillChatDialog)
    dialog._session = None
    dialog._pending_user_message = ""
    return dialog


def test_exchange_is_recorded_and_listed(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sessions, "app_data_dir", lambda: tmp_path)

    dialog = _dialog()
    dialog._pending_user_message = "Write a short poem about rain"
    dialog._record_session_exchange("Rain taps the glass like a quiet friend.")

    saved = sessions.list_sessions()
    assert len(saved) == 1
    assert saved[0].turn_count == 2
    assert saved[0].title.startswith("Write a short poem")


def test_second_exchange_appends_to_same_session(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sessions, "app_data_dir", lambda: tmp_path)

    dialog = _dialog()
    dialog._pending_user_message = "First question"
    dialog._record_session_exchange("First answer")
    dialog._pending_user_message = "Second question"
    dialog._record_session_exchange("Second answer")

    saved = sessions.list_sessions()
    assert len(saved) == 1
    assert saved[0].turn_count == 4


def test_blank_message_or_answer_records_nothing(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sessions, "app_data_dir", lambda: tmp_path)

    dialog = _dialog()
    dialog._pending_user_message = ""
    dialog._record_session_exchange("An answer with no question")
    dialog._pending_user_message = "A question with no answer"
    dialog._record_session_exchange("")

    assert sessions.list_sessions() == ()
