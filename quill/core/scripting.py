"""Official QUILL scripting API — the ``q`` object exposed in the developer console.

The ``QuillScriptAPI`` class is the only stable, supported way to automate the
running editor from console code.  All mutations route through the command
registry so undo/redo, dirty-state tracking, status-bar updates, and
screen-reader announcements remain consistent.

The ``ConsoleHost`` protocol is implemented by the UI mixin
``main_frame_devtools.DevToolsMixin``; it keeps this module wx-free and
independently testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Host protocol (implemented in the UI layer — no wx import here)
# ---------------------------------------------------------------------------


class ConsoleHost(Protocol):
    """Minimal surface the scripting API needs from the live editor."""

    def console_get_editor_text(self) -> str: ...
    def console_set_editor_text(self, text: str) -> None: ...
    def console_get_selected_text(self) -> str: ...
    def console_replace_selection(self, text: str) -> None: ...
    def console_goto_line(self, line: int) -> None: ...
    def console_goto_offset(self, offset: int) -> None: ...
    def console_get_document_name(self) -> str: ...
    def console_run_command(self, command_id: str) -> None: ...
    def console_command_exists(self, command_id: str) -> bool: ...
    def console_list_commands(self, query: str | None) -> list[tuple[str, str]]: ...
    def console_announce(self, text: str) -> None: ...
    def console_get_last_announcements(self) -> list[str]: ...
    def console_document_stats(self) -> dict[str, int]: ...
    # Subsystem surfaces for the q.* facades (settings, profile, bookmarks,
    # quillins, macros, spell). All implemented defensively in the UI layer so a
    # console call never crashes the editor.
    def console_get_setting(self, name: str) -> object: ...
    def console_all_settings(self) -> dict[str, object]: ...
    def console_active_profile(self) -> tuple[str, str]: ...
    def console_available_profiles(self) -> list[tuple[str, str]]: ...
    def console_switch_profile(self, profile_id: str) -> None: ...
    def console_feature_enabled(self, feature_id: str) -> bool: ...
    def console_list_bookmarks(self) -> list[tuple[str, int]]: ...
    def console_list_quillins(self) -> list[str]: ...
    def console_start_macro(self, name: str) -> None: ...
    def console_stop_macro(self) -> str | None: ...
    def console_play_last_macro(self) -> None: ...
    def console_recording_macro(self) -> str | None: ...
    def console_spell_suggest(self, word: str) -> list[str]: ...


# ---------------------------------------------------------------------------
# Snapshot types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DocumentSnapshot:
    name: str
    path: str
    modified: bool
    line_count: int
    char_count: int


@dataclass(frozen=True, slots=True)
class DocumentStats:
    words: int
    lines: int
    chars: int
    paragraphs: int


@dataclass(frozen=True, slots=True)
class CommandInfo:
    id: str
    title: str


# ---------------------------------------------------------------------------
# Sub-facades
# ---------------------------------------------------------------------------


class _A11yFacade:
    """Announcement and accessibility testing facade (q.a11y)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def announce(self, text: str) -> None:
        """Send a screen-reader announcement through QUILL's normal path."""
        self._host.console_announce(text)

    def last_announcements(self) -> list[str]:
        """Return recent announcements (most recent last)."""
        return self._host.console_get_last_announcements()


class _CommandsFacade:
    """Command registry facade (q.commands / standalone ``commands`` name)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def search(self, query: str) -> list[str]:
        """Return command IDs whose title or ID contains *query* (case-insensitive)."""
        q = query.lower()
        return [
            cmd_id
            for cmd_id, title in self._host.console_list_commands(None)
            if q in cmd_id.lower() or q in title.lower()
        ]

    def exists(self, command_id: str) -> bool:
        return self._host.console_command_exists(command_id)

    def run(self, command_id: str) -> None:
        self._host.console_run_command(command_id)

    def list(self, query: str | None = None) -> list[CommandInfo]:
        return [
            CommandInfo(id=cid, title=title)
            for cid, title in self._host.console_list_commands(query)
        ]


class _FocusFacade:
    """Focus inspection facade (q.focus)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def describe(self) -> str:
        """Describe the current editor focus state."""
        name = self._host.console_get_document_name()
        stats = self._host.console_document_stats()
        lines = stats.get("lines", 0)
        chars = stats.get("chars", 0)
        selected = self._host.console_get_selected_text()
        sel_info = f", {len(selected)} chars selected" if selected else ", no selection"
        return f"Editor: {name or '(no document)'}, {lines} lines, {chars} chars{sel_info}"


class _SupportFacade:
    """Support and diagnostics facade (q.support)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def diagnostic_summary(self) -> str:
        """Return a plain-text diagnostic summary suitable for support tickets."""
        import sys

        from quill.core.paths import app_data_dir

        name = self._host.console_get_document_name() or "(none)"
        stats = self._host.console_document_stats()
        lines = [
            "QUILL diagnostic summary",
            f"Python: {sys.version.split()[0]}",
            f"Active document: {name}",
            f"Document lines: {stats.get('lines', 0)}",
            f"Document words: {stats.get('words', 0)}",
            f"Data directory: {app_data_dir()}",
            "Document content included: no",
        ]
        return "\n".join(lines)


class _SelectionFacade:
    """Selection access (q.selection)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def text(self) -> str:
        """Return the currently selected text (empty string if none)."""
        return self._host.console_get_selected_text()

    def replace(self, text: str) -> None:
        """Replace the current selection with *text* (or insert if none)."""
        if not isinstance(text, str):
            raise TypeError(f"replace expects a str, got {type(text).__name__}")
        self._host.console_replace_selection(text)


class _DocFacade:
    """Active-document access (q.doc)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def name(self) -> str:
        """Return the active document's file name (empty if unsaved)."""
        return self._host.console_get_document_name()

    def text(self) -> str:
        """Return the full text of the active document."""
        return self._host.console_get_editor_text()

    def set_text(self, text: str) -> None:
        """Replace the entire document text with *text*."""
        if not isinstance(text, str):
            raise TypeError(f"set_text expects a str, got {type(text).__name__}")
        self._host.console_set_editor_text(text)

    def stats(self) -> DocumentStats:
        """Return word / line / char / paragraph counts."""
        s = self._host.console_document_stats()
        return DocumentStats(
            words=s.get("words", 0),
            lines=s.get("lines", 0),
            chars=s.get("chars", 0),
            paragraphs=s.get("paragraphs", 0),
        )


class _EditorFacade:
    """Editor mutations and caret movement (q.editor)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def insert(self, text: str) -> None:
        """Insert *text* at the caret."""
        if not isinstance(text, str):
            raise TypeError(f"insert expects a str, got {type(text).__name__}")
        self._host.console_replace_selection(text)

    def goto_line(self, line: int) -> None:
        """Move the caret to 1-based *line*."""
        if not isinstance(line, int) or line < 1:
            raise ValueError(f"goto_line expects a positive int, got {line!r}")
        self._host.console_goto_line(line)

    def goto_offset(self, offset: int) -> None:
        """Move the caret to absolute character *offset* (0-based)."""
        if not isinstance(offset, int) or offset < 0:
            raise ValueError(f"goto_offset expects a non-negative int, got {offset!r}")
        self._host.console_goto_offset(offset)


class _SettingsFacade:
    """Read-only settings access (q.settings)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def get(self, name: str) -> object:
        """Return the value of setting *name* (None if unknown)."""
        return self._host.console_get_setting(name)

    def all(self) -> dict[str, object]:
        """Return a snapshot of all settings as a plain dict."""
        return self._host.console_all_settings()


class _ProfileFacade:
    """Feature-profile inspection and switching (q.profile)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def current(self) -> tuple[str, str]:
        """Return the active profile as (id, name)."""
        return self._host.console_active_profile()

    def names(self) -> list[tuple[str, str]]:
        """Return all available profiles as (id, name) pairs."""
        return self._host.console_available_profiles()

    def switch(self, profile_id: str) -> None:
        """Switch to the profile with id *profile_id*."""
        self._host.console_switch_profile(profile_id)

    def feature_enabled(self, feature_id: str) -> bool:
        """Return True if *feature_id* is enabled under the active profile."""
        return self._host.console_feature_enabled(feature_id)


class _BookmarksFacade:
    """Bookmark inspection (q.bookmarks)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def list(self) -> list[tuple[str, int]]:
        """Return bookmarks as (name, caret-offset) pairs."""
        return self._host.console_list_bookmarks()


class _QuillinsFacade:
    """Installed-extension inspection (q.quillins)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def list(self) -> list[str]:
        """Return the ids/names of discovered Quillins."""
        return self._host.console_list_quillins()


class _MacrosFacade:
    """Macro recording and playback (q.macros)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def start(self, name: str) -> None:
        """Begin recording a macro named *name*."""
        self._host.console_start_macro(name)

    def stop(self) -> str | None:
        """Stop recording; return the recorded macro name (or None)."""
        return self._host.console_stop_macro()

    def play(self) -> None:
        """Replay the last recorded macro."""
        self._host.console_play_last_macro()

    def recording(self) -> str | None:
        """Return the name of the macro currently recording, or None."""
        return self._host.console_recording_macro()


class _SpellFacade:
    """Spell-check helpers (q.spell)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def suggest(self, word: str) -> list[str]:
        """Return spelling suggestions for *word* (empty if none/unavailable)."""
        return self._host.console_spell_suggest(word)


class _DiagnosticsFacade:
    """Diagnostics summaries (q.diagnostics)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host
        self._support = _SupportFacade(host)

    def summary(self) -> str:
        """Return a plain-text diagnostic summary (no document content)."""
        return self._support.diagnostic_summary()

    def document_summary(self) -> str:
        """Alias for :meth:`summary` (documented as q.diagnostics.document_summary)."""
        return self._support.diagnostic_summary()


# ---------------------------------------------------------------------------
# Primary scripting API
# ---------------------------------------------------------------------------


class QuillScriptAPI:
    """The ``q`` object available in the QUILL developer console."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host
        self.a11y = _A11yFacade(host)
        self.commands = _CommandsFacade(host)
        self.focus = _FocusFacade(host)
        self.support = _SupportFacade(host)
        self.selection = _SelectionFacade(host)
        self.doc = _DocFacade(host)
        self.editor = _EditorFacade(host)
        self.settings = _SettingsFacade(host)
        self.profile = _ProfileFacade(host)
        self.bookmarks = _BookmarksFacade(host)
        self.quillins = _QuillinsFacade(host)
        self.macros = _MacrosFacade(host)
        self.spell = _SpellFacade(host)
        self.diagnostics = _DiagnosticsFacade(host)

    # -- Text mutations (route through host which routes through command registry) --

    def insert_text(self, text: str) -> None:
        """Insert *text* at the current caret position."""
        if not isinstance(text, str):
            raise TypeError(f"insert_text expects a str, got {type(text).__name__}")
        self._host.console_replace_selection(text)

    def replace_selection(self, text: str) -> None:
        """Replace the current selection with *text* (or insert if no selection)."""
        if not isinstance(text, str):
            raise TypeError(f"replace_selection expects a str, got {type(text).__name__}")
        self._host.console_replace_selection(text)

    def selected_text(self) -> str:
        """Return the currently selected text (empty string if no selection)."""
        return self._host.console_get_selected_text()

    def document_text(self) -> str:
        """Return the full text of the active document."""
        return self._host.console_get_editor_text()

    def set_document_text(self, text: str) -> None:
        """Replace the entire document text with *text*."""
        if not isinstance(text, str):
            raise TypeError(f"set_document_text expects a str, got {type(text).__name__}")
        self._host.console_set_editor_text(text)

    # -- Navigation --

    def goto_line(self, line: int) -> None:
        """Move the caret to 1-based *line*."""
        if not isinstance(line, int) or line < 1:
            raise ValueError(f"goto_line expects a positive int, got {line!r}")
        self._host.console_goto_line(line)

    def goto_offset(self, offset: int) -> None:
        """Move the caret to absolute character *offset* (0-based)."""
        if not isinstance(offset, int) or offset < 0:
            raise ValueError(f"goto_offset expects a non-negative int, got {offset!r}")
        self._host.console_goto_offset(offset)

    # -- Commands --

    def run_command(self, command_id: str, **kwargs: object) -> None:
        """Run a registered command by ID."""
        if not self._host.console_command_exists(command_id):
            suggestions = self.commands.search(command_id.split(".")[-1])
            hint = ""
            if suggestions:
                hint = f"  Suggestion: try one of {suggestions[:3]}"
            raise KeyError(f"Unknown command: {command_id!r}.{hint}")
        self._host.console_run_command(command_id)

    def command_exists(self, command_id: str) -> bool:
        return self._host.console_command_exists(command_id)

    def describe_command(self, command_id: str) -> str:
        """Return a one-line description of *command_id* (id, title, availability)."""
        for cid, title in self._host.console_list_commands(None):
            if cid == command_id:
                return f"{cid}: {title} (available)"
        if self._host.console_command_exists(command_id):
            return f"{command_id}: (available)"
        suggestions = self.commands.search(command_id.split(".")[-1])
        hint = f"  Did you mean: {suggestions[:3]}" if suggestions else ""
        return f"{command_id}: unknown command.{hint}"

    def begin_macro(self, name: str) -> None:
        """Begin recording a macro named *name* (alias for q.macros.start)."""
        self.macros.start(name)

    def end_macro(self) -> str | None:
        """Stop recording the current macro (alias for q.macros.stop)."""
        return self.macros.stop()

    def list_commands(self, query: str | None = None) -> list[CommandInfo]:
        return [
            CommandInfo(id=cid, title=title)
            for cid, title in self._host.console_list_commands(query)
        ]

    # -- State inspection --

    def active_document(self) -> DocumentSnapshot:
        name = self._host.console_get_document_name()
        stats = self._host.console_document_stats()
        return DocumentSnapshot(
            name=name or "",
            path="",
            modified=False,
            line_count=stats.get("lines", 0),
            char_count=stats.get("chars", 0),
        )

    def document_stats(self) -> DocumentStats:
        s = self._host.console_document_stats()
        return DocumentStats(
            words=s.get("words", 0),
            lines=s.get("lines", 0),
            chars=s.get("chars", 0),
            paragraphs=s.get("paragraphs", 0),
        )

    def refresh_context(self) -> None:
        """Signal that snapshot variables should be updated."""

    # -- Help --

    def help(self, topic: str | None = None) -> str:
        if topic is None:
            return (
                "QUILL scripting API (q):\n"
                "  q.insert_text(text)         Insert text at caret\n"
                "  q.replace_selection(text)   Replace selection\n"
                "  q.selected_text()           Read selection\n"
                "  q.document_text()           Read full document\n"
                "  q.goto_line(n)              Move to line n (1-based)\n"
                "  q.run_command(id)           Run a command by ID\n"
                "  q.list_commands(query)      List/search commands\n"
                "  q.describe_command(id)      One-line command description\n"
                "  q.selection.text() / .replace(text)\n"
                "  q.doc.name() / .text() / .set_text(t) / .stats()\n"
                "  q.editor.insert(t) / .goto_line(n) / .goto_offset(n)\n"
                "  q.settings.get(name) / .all()\n"
                "  q.profile.current() / .names() / .switch(id) / .feature_enabled(id)\n"
                "  q.bookmarks.list()          q.quillins.list()\n"
                "  q.macros.start(name) / .stop() / .play() / .recording()\n"
                "  q.begin_macro(name) / q.end_macro()\n"
                "  q.spell.suggest(word)       q.diagnostics.summary()\n"
                "  q.a11y.announce(text)       Send SR announcement\n"
                "  q.help('method_name')       Help on a specific method"
            )
        doc = getattr(self.__class__, topic, None)
        if doc and doc.__doc__:
            return cast(str, doc.__doc__).strip()
        return f"No help found for {topic!r}. Try q.list_commands() or q.help()."

    def __repr__(self) -> str:
        return "<QuillScriptAPI — type q.help() for usage>"
