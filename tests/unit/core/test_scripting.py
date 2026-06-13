"""Tests for quill.core.scripting (QuillScriptAPI and sub-facades)."""

from __future__ import annotations

import pytest

from quill.core.scripting import (
    CommandInfo,
    DocumentSnapshot,
    DocumentStats,
    QuillScriptAPI,
)


class _FakeHost:
    """Minimal ConsoleHost stub for testing the scripting API in isolation."""

    def __init__(self):
        self.text = "Hello world\nSecond line"
        self.selection = ""
        self.cursor_line = 1
        self.cursor_offset = 0
        self.doc_name = "test.txt"
        self.commands_db = {
            "file.save": "Save",
            "edit.copy": "Copy",
        }
        self.announcements: list[str] = []
        self.settings_data: dict[str, object] = {
            "theme": "dark",
            "ai_chat_default_provider": "ollama",
        }
        self.profiles = [("essential", "Essential"), ("writer", "Writer")]
        self.active_profile_pair = ("essential", "Essential")
        self.enabled_features = {"core.editor"}
        self.bookmarks_data = [("Intro", 0), ("End", 42)]
        self.quillins_data = ["word-count", "markdown-helpers"]
        self.macro_recording: str | None = None
        self.last_macro: str | None = None
        self.macro_played = False
        self.spell_db = {"happy": ["glad", "cheerful"]}

    def console_get_editor_text(self) -> str:
        return self.text

    def console_set_editor_text(self, text: str) -> None:
        self.text = text

    def console_get_selected_text(self) -> str:
        return self.selection

    def console_replace_selection(self, text: str) -> None:
        self.selection = text

    def console_goto_line(self, line: int) -> None:
        self.cursor_line = line

    def console_goto_offset(self, offset: int) -> None:
        self.cursor_offset = offset

    def console_get_document_name(self) -> str:
        return self.doc_name

    def console_run_command(self, command_id: str) -> None:
        if command_id not in self.commands_db:
            raise KeyError(command_id)

    def console_command_exists(self, command_id: str) -> bool:
        return command_id in self.commands_db

    def console_list_commands(self, query):
        items = list(self.commands_db.items())
        if query:
            q = query.lower()
            items = [(k, v) for k, v in items if q in k.lower() or q in v.lower()]
        return items

    def console_announce(self, text: str) -> None:
        self.announcements.append(text)

    def console_get_last_announcements(self) -> list[str]:
        return list(self.announcements)

    def console_document_stats(self) -> dict:
        words = len(self.text.split())
        lines = self.text.count("\n") + 1
        chars = len(self.text)
        return {"words": words, "lines": lines, "chars": chars, "paragraphs": 1}

    def console_get_setting(self, name):
        return self.settings_data.get(name)

    def console_all_settings(self):
        return dict(self.settings_data)

    def console_active_profile(self):
        return self.active_profile_pair

    def console_available_profiles(self):
        return list(self.profiles)

    def console_switch_profile(self, profile_id):
        for pid, pname in self.profiles:
            if pid == profile_id:
                self.active_profile_pair = (pid, pname)

    def console_feature_enabled(self, feature_id):
        return feature_id in self.enabled_features

    def console_list_bookmarks(self):
        return list(self.bookmarks_data)

    def console_list_quillins(self):
        return list(self.quillins_data)

    def console_start_macro(self, name):
        self.macro_recording = name

    def console_stop_macro(self):
        name = self.macro_recording
        self.macro_recording = None
        self.last_macro = name
        return name

    def console_play_last_macro(self):
        self.macro_played = True

    def console_recording_macro(self):
        return self.macro_recording

    def console_spell_suggest(self, word):
        return list(self.spell_db.get(word, []))


@pytest.fixture
def host():
    return _FakeHost()


@pytest.fixture
def api(host):
    return QuillScriptAPI(host)


def test_insert_text_delegates_to_host(api, host):
    api.insert_text("foo")
    assert host.selection == "foo"


def test_replace_selection(api, host):
    api.replace_selection("bar")
    assert host.selection == "bar"


def test_insert_text_rejects_non_str(api):
    with pytest.raises(TypeError):
        api.insert_text(123)


def test_selected_text(api, host):
    host.selection = "selected"
    assert api.selected_text() == "selected"


def test_document_text(api):
    assert api.document_text() == "Hello world\nSecond line"


def test_set_document_text(api, host):
    api.set_document_text("new content")
    assert host.text == "new content"


def test_goto_line_delegates(api, host):
    api.goto_line(2)
    assert host.cursor_line == 2


def test_goto_line_rejects_zero(api):
    with pytest.raises(ValueError):
        api.goto_line(0)


def test_goto_offset(api, host):
    api.goto_offset(5)
    assert host.cursor_offset == 5


def test_run_command_known(api):
    api.run_command("file.save")  # should not raise


def test_run_command_unknown_raises(api):
    with pytest.raises(KeyError):
        api.run_command("not.real")


def test_command_exists(api):
    assert api.command_exists("file.save") is True
    assert api.command_exists("not.real") is False


def test_list_commands_returns_command_info(api):
    cmds = api.list_commands()
    assert all(isinstance(c, CommandInfo) for c in cmds)
    ids = [c.id for c in cmds]
    assert "file.save" in ids


def test_active_document_snapshot(api):
    snap = api.active_document()
    assert isinstance(snap, DocumentSnapshot)
    assert snap.name == "test.txt"


def test_document_stats(api):
    stats = api.document_stats()
    assert isinstance(stats, DocumentStats)
    assert stats.words == 4  # "Hello world Second line"
    assert stats.lines == 2


def test_a11y_announce(api, host):
    api.a11y.announce("test announcement")
    assert "test announcement" in host.announcements


def test_a11y_last_announcements(api, host):
    api.a11y.announce("first")
    api.a11y.announce("second")
    last = api.a11y.last_announcements()
    assert last == ["first", "second"]


def test_commands_search(api):
    results = api.commands.search("save")
    assert "file.save" in results


def test_commands_search_no_results(api):
    results = api.commands.search("xyzzy_nonexistent")
    assert results == []


def test_support_diagnostic_summary_has_version(api):
    summary = api.support.diagnostic_summary()
    assert "QUILL" in summary
    assert "test.txt" in summary


def test_focus_describe_includes_doc_name(api):
    desc = api.focus.describe()
    assert "test.txt" in desc


def test_help_returns_string(api):
    result = api.help()
    assert isinstance(result, str)
    assert "insert_text" in result


def test_repr(api):
    assert "QuillScriptAPI" in repr(api)


# --- New q.* facades (QDC API completion) -------------------------------------


def test_selection_facade(api, host):
    host.selection = "sel"
    assert api.selection.text() == "sel"
    api.selection.replace("new")
    assert host.selection == "new"


def test_doc_facade(api, host):
    assert api.doc.name() == "test.txt"
    assert api.doc.text() == "Hello world\nSecond line"
    assert api.doc.stats().words == 4
    api.doc.set_text("changed")
    assert host.text == "changed"


def test_editor_facade(api, host):
    api.editor.insert("ins")
    assert host.selection == "ins"
    api.editor.goto_line(3)
    assert host.cursor_line == 3
    api.editor.goto_offset(7)
    assert host.cursor_offset == 7


def test_settings_facade(api):
    assert api.settings.get("ai_chat_default_provider") == "ollama"
    assert "theme" in api.settings.all()


def test_profile_facade(api):
    assert api.profile.current() == ("essential", "Essential")
    assert ("writer", "Writer") in api.profile.names()
    api.profile.switch("writer")
    assert api.profile.current() == ("writer", "Writer")
    assert api.profile.feature_enabled("core.editor") is True
    assert api.profile.feature_enabled("nope") is False


def test_bookmarks_facade(api):
    assert ("Intro", 0) in api.bookmarks.list()


def test_quillins_facade(api):
    assert "word-count" in api.quillins.list()


def test_macros_facade(api, host):
    api.macros.start("m1")
    assert api.macros.recording() == "m1"
    assert api.macros.stop() == "m1"
    assert api.macros.recording() is None
    api.macros.play()
    assert host.macro_played is True


def test_begin_end_macro_aliases(api):
    api.begin_macro("m2")
    assert api.macros.recording() == "m2"
    assert api.end_macro() == "m2"


def test_spell_facade(api):
    assert api.spell.suggest("happy") == ["glad", "cheerful"]
    assert api.spell.suggest("unknownword") == []


def test_diagnostics_facade(api):
    assert "QUILL" in api.diagnostics.summary()
    assert "QUILL" in api.diagnostics.document_summary()


def test_describe_command(api):
    assert "file.save" in api.describe_command("file.save")
    assert "unknown" in api.describe_command("not.real")


def test_help_lists_new_facades(api):
    result = api.help()
    assert "q.macros" in result
    assert "q.selection" in result
