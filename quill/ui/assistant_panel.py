"""The "Ask Quill" AI chat dialog.

A conversation with Quill's on-device assistant (Apple Foundation Models on
macOS, llama.cpp on Windows/Linux). Each turn the assistant decides whether to
answer in chat, insert or replace text in the document, or run a Quill command —
and acts on the editor live via callbacks, but only after the user approves.

The whole conversation — transcript, suggestions, and the message edit field —
renders inside an accessible WebView (Edge WebView2 on Windows): Markdown is
formatted, new messages land in an ARIA live region, and the edit field is part
of the page so the user stays in the web view to type. A plain wx ListBox +
text field is the fallback when no WebView backend is available. Generation runs
off the UI thread.
"""

from __future__ import annotations

import threading
import time

from quill.ui.dialog_contract import apply_modal_ids, show_modal_dialog

SUGGESTED_PROMPTS: tuple[str, ...] = (
    "Summarize this document",
    "Fix spelling and grammar",
    "Write an introduction for this",
    "List the key action items",
    "Save the document",
    "Read this aloud",
)


def classify_assistant_error(error: str) -> tuple[str, bool]:
    """Return a user-facing error message and whether chat input should be disabled."""
    text = (error or "").strip()
    lowered = text.lower()
    if "failed to load native code" in lowered or "0xc000001d" in lowered:
        return (
            "On-device AI couldn't start on this computer. This processor may not "
            "support the built-in AI engine. You can turn AI off from the AI menu, "
            "or connect a cloud AI provider in AI settings.",
            True,
        )
    return (f"Error: {text}", False)


class AskQuillChatDialog:
    def __init__(
        self,
        parent: object,
        assistant: object,
        *,
        get_document,
        get_selection,
        insert_text,
        replace_selection,
        run_command,
        tool_catalog: list[tuple[str, str]],
        announce=None,
        review_changes=None,
    ) -> None:
        import wx

        self._wx = wx
        self._assistant = assistant
        self._get_document = get_document
        self._get_selection = get_selection
        self._insert_text = insert_text
        self._replace_selection = replace_selection
        self._run_command = run_command
        # AI-7: optional callback to present a navigable diff before applying a
        # replacement. Signature: review_changes(original, revised, on_apply).
        self._review_changes = review_changes
        self._tool_titles = dict(tool_catalog)
        self._tool_ids = tuple(tid for tid, _ in tool_catalog)
        self._announce = announce or (lambda _m: None)
        self._last_response = ""
        self._first_done = False
        # Branch-tree session log (#130): conversational exchanges are recorded
        # as user/assistant turns and saved so the Session Branches browser is
        # populated. Created lazily on the first completed exchange.
        self._session = None
        self._pending_user_message = ""
        # Streaming state (AI-1): accumulate streamed fragments on the UI thread
        # and announce them in throttled, sentence-sized chunks.
        self._stream_active = False
        self._stream_buffer = ""
        self._stream_announced = 0
        self._stream_last = 0.0

        self.dialog = wx.Dialog(
            parent, title="Ask Quill", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.dialog.SetSize((760, 760))
        outer = wx.BoxSizer(wx.VERTICAL)

        self._full_messages: list[str] = []
        # Render the whole chat (transcript + suggestions + edit field) as
        # markdown in a WebView. Fall back to a list box + wx text field if the
        # WebView backend (Edge WebView2 / WebKit) isn't available.
        self._webview = None
        self.messages = None
        self.input = None
        self.send_button = None
        self._suggestion_buttons: list = []
        try:
            from quill.ui.accessible_webview import AccessibleWebView

            self._webview = AccessibleWebView(
                self.dialog,
                title="Conversation",
                intro=("Quill", "Hi! Ask me to write, edit, or run something in your document."),
                suggestions=SUGGESTED_PROMPTS,
                on_send=self._submit,
                on_close=self._close,
            )
            outer.Add(self._webview.control, 1, wx.EXPAND | wx.ALL, 0)
        except Exception:  # noqa: BLE001
            self._webview = None
            self._build_fallback_input(outer)

        # Approval bar — nothing is applied to the document until you approve.
        self._pending = None
        self.approval_label = wx.StaticText(self.dialog, label="")
        self.approve_button = wx.Button(self.dialog, label="Approve")
        self.discard_button = wx.Button(self.dialog, label="Discard")
        approval = wx.BoxSizer(wx.HORIZONTAL)
        approval.Add(self.approval_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        approval.Add(self.approve_button, 0, wx.RIGHT, 8)
        approval.Add(self.discard_button, 0)
        outer.Add(approval, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 14)
        self._show_approval(False)

        footer = wx.BoxSizer(wx.HORIZONTAL)
        self.copy_button = wx.Button(self.dialog, label="Copy Last Response")
        self.copy_button.Enable(False)
        footer.Add(self.copy_button, 0, wx.RIGHT, 8)
        footer.AddStretchSpacer()
        footer.Add(wx.Button(self.dialog, wx.ID_CANCEL, label="Close"), 0)
        outer.Add(footer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)
        self.dialog.SetSizer(outer)

        self.approve_button.Bind(wx.EVT_BUTTON, self._on_approve)
        self.discard_button.Bind(wx.EVT_BUTTON, self._on_discard)
        self.copy_button.Bind(wx.EVT_BUTTON, self._on_copy)
        self.dialog.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

        available, reason = assistant.is_available()
        if not available:
            self._append("Quill", f"On-device AI is unavailable: {reason}")
            self._set_busy(True)
        elif self._webview is None:
            # WebView bakes the greeting into the page (no flash); list box needs it added.
            self._append("Quill", "Hi! Ask me to write, edit, or run something in your document.")

    def _build_fallback_input(self, outer) -> None:
        """List box transcript + wx text field, for when no WebView backend exists."""
        wx = self._wx
        outer.Add(
            wx.StaticText(self.dialog, label="Conversation"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 14
        )
        self.messages = wx.ListBox(self.dialog, style=wx.LB_SINGLE | wx.LB_NEEDED_SB)
        self.messages.SetName("Conversation")
        outer.Add(self.messages, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 14)

        outer.Add(
            wx.StaticText(self.dialog, label="Suggestions"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 14
        )
        suggestions = wx.WrapSizer(wx.HORIZONTAL)
        for text in SUGGESTED_PROMPTS:
            button = wx.Button(self.dialog, label=text)
            button.Bind(wx.EVT_BUTTON, lambda _e, t=text: self._submit(t))
            suggestions.Add(button, 0, wx.RIGHT | wx.BOTTOM, 6)
            self._suggestion_buttons.append(button)
        outer.Add(suggestions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 14)

        outer.Add(
            wx.StaticText(self.dialog, label="Your message"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 14
        )
        input_row = wx.BoxSizer(wx.HORIZONTAL)
        self.input = wx.TextCtrl(self.dialog, style=wx.TE_PROCESS_ENTER)
        self.input.SetName("Your message to Quill")
        self.input.SetHint("Ask Quill to write, edit, or run something…")
        input_row.Add(self.input, 1, wx.EXPAND | wx.RIGHT, 8)
        self.send_button = wx.Button(self.dialog, label="Send")
        self.send_button.SetDefault()
        input_row.Add(self.send_button, 0)
        outer.Add(input_row, 0, wx.EXPAND | wx.ALL, 14)

        self.input.Bind(wx.EVT_TEXT_ENTER, lambda _e: self._submit(self.input.GetValue()))
        self.send_button.Bind(wx.EVT_BUTTON, lambda _e: self._submit(self.input.GetValue()))

    def _close(self) -> None:
        self.dialog.EndModal(self._wx.ID_CANCEL)

    def _on_char_hook(self, event: object) -> None:
        wx = self._wx
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self._close()
            return
        event.Skip()

    def _append(self, speaker: str, text: str) -> None:
        self._full_messages.append(text)
        if self._webview is not None:
            # Rendered markdown in the WebView's ARIA live-region log.
            self._webview.append_message(speaker, text)
            return
        # List-box fallback: one item per message (newlines flattened).
        display = f"{speaker}: {' '.join(text.splitlines())}"
        index = self.messages.GetCount()
        self.messages.Append(display)
        self.messages.SetSelection(index)
        if hasattr(self.messages, "EnsureVisible"):
            self.messages.EnsureVisible(index)

    def _announce_incoming(self, text: str, *, prefix: str = "Quill says") -> None:
        compact = " ".join((text or "").split())
        if not compact:
            return
        if len(compact) > 140:
            compact = compact[:137].rstrip() + "..."
        self._announce(f"{prefix}: {compact}")

    def _set_busy(self, busy: bool) -> None:
        if self._webview is not None:
            self._webview.set_input_enabled(not busy)
            return
        self.send_button.Enable(not busy)
        self.input.Enable(not busy)
        for button in self._suggestion_buttons:
            button.Enable(not busy)

    def _focus_composer(self) -> None:
        if self._webview is not None:
            self._webview.focus()
        elif self.input is not None:
            self.input.SetFocus()

    def _submit(self, message: str) -> None:
        message = (message or "").strip()
        if not message:
            self._focus_composer()
            return
        self._append("You", message)
        self._pending_user_message = message
        if self.input is not None:
            self.input.SetValue("")
        # Suggestions fall away once the conversation starts (like Apple Intelligence).
        if not self._first_done:
            self._first_done = True
            if self._webview is not None:
                self._webview.hide_suggestions()
        self._set_busy(True)
        if self._webview is not None:
            self._webview.set_status("Quill is responding")
        self._announce("Working")
        document = self._get_document()
        selection = self._get_selection()
        self._stream_active = False
        self._stream_buffer = ""
        self._stream_announced = 0
        self._stream_last = 0.0

        def worker() -> None:
            try:
                decision = self._assistant.decide(message, document, self._tool_ids)
                action = decision.action
                if action == "run" and decision.tool:
                    result = ("run", "", decision.tool, "")
                elif action == "insert":
                    text = self._assistant.write_for_document(message, document)
                    result = ("insert", text, "", "")
                elif action == "replace":
                    if selection:
                        text = self._assistant.rewrite_selection(message, selection)
                    else:
                        text = self._assistant.write_for_document(message, document)
                    result = ("replace", text, "", "")
                else:
                    self._stream_active = True

                    def on_delta(fragment: str) -> None:
                        self._wx.CallAfter(self._on_stream_delta, fragment)

                    text = self._assistant.answer_stream(message, document, on_delta)
                    result = ("answer", text, "", "")
            except Exception as exc:  # noqa: BLE001
                result = ("error", "", "", str(exc))
            self._wx.CallAfter(self._apply, *result)

        threading.Thread(target=worker, daemon=True).start()

    def _on_stream_delta(self, fragment: str) -> None:
        """UI thread: collect a streamed fragment and announce on a throttle (AI-1)."""
        if not fragment:
            return
        self._stream_buffer += fragment
        now = time.monotonic()
        # Hold announcements to roughly one per 0.8s so speech stays intelligible
        # instead of being interrupted token by token.
        if now - self._stream_last < 0.8:
            return
        self._announce_stream_progress()

    def _announce_stream_progress(self) -> None:
        """Announce the next sentence-sized chunk of streamed text."""
        pending = self._stream_buffer[self._stream_announced :]
        if not pending.strip():
            return
        boundary = max(
            pending.rfind(". "),
            pending.rfind("! "),
            pending.rfind("? "),
            pending.rfind("\n"),
        )
        if boundary < 0:
            # No sentence end yet; wait unless a long run has built up.
            if len(pending) < 80:
                return
            consumed = len(pending)
            chunk = pending
        else:
            consumed = boundary + 1
            chunk = pending[:consumed]
        spoken = " ".join(chunk.split())
        self._stream_announced += consumed
        if not spoken:
            return
        self._stream_last = time.monotonic()
        if self._webview is not None:
            self._webview.set_status(spoken)
        else:
            self._announce(spoken)

    def _show_approval(self, show: bool, label: str = "") -> None:
        self.approval_label.SetLabel(label)
        self.approve_button.Show(show)
        self.discard_button.Show(show)
        self.approve_button.Enable(show)
        self.discard_button.Enable(show)
        self.dialog.Layout()

    def _apply(self, action: str, text: str, tool: str, error: str) -> None:
        # Nothing touches the document automatically — propose, then await approval.
        if action == "error":
            message, disable_chat = classify_assistant_error(error)
            self._append("Quill", message)
            self._announce_incoming(message, prefix="Quill error")
            if disable_chat:
                self._set_busy(True)
                if self._webview is not None:
                    self._webview.set_status("Quill is unavailable")
                self._announce("On-device AI unavailable")
                return
        elif action == "run" and tool:
            title = self._tool_titles.get(tool, tool)
            self._pending = ("run", "", tool)
            proposal = f"I'd like to run: {title}. Approve to run it."
            self._append("Quill", proposal)
            self._announce_incoming(proposal, prefix="Quill proposal")
            self._show_approval(True, f"Run “{title}”?")
        elif action in ("insert", "replace") and text:
            self._last_response = text
            self._pending = (action, text, "")
            verb = (
                "insert this at the cursor"
                if action == "insert"
                else "replace the selection with this"
            )
            proposal = f"I'd like to {verb} (approve to apply):\n{text}"
            self._append("Quill", proposal)
            self._announce_incoming(text, prefix="Quill proposal")
            self._show_approval(True, "Apply this to the document?")
            self._record_session_exchange(text)
        else:
            self._last_response = text
            self._append("Quill", text or "(no response)")
            if self._stream_active:
                # The reply was already announced incrementally as it streamed
                # in, and the full text is now in the transcript. Skip repeating
                # the whole thing; the "Response ready" cue below closes it out.
                self._stream_active = False
            else:
                self._announce_incoming(text or "No response")
            self._record_session_exchange(text)
        self.copy_button.Enable(bool(self._last_response))
        self._set_busy(False)
        if self._webview is not None:
            self._webview.set_status("Quill responded")
        if self._pending:
            self._announce("Quill is proposing a change. Approve or discard.")
            self.approve_button.SetFocus()
        else:
            # The live region already announced the reply; don't steal focus
            # from the in-page edit field the user is sitting in.
            self._announce("Response ready")

    def _record_session_exchange(self, assistant_text: str) -> None:
        """Persist the user/assistant turn pair to the branch-tree log (#130).

        Created lazily on the first completed exchange and titled from the first
        user message. Persistence failures must never disrupt the conversation,
        so any error here is swallowed.
        """
        user_message = self._pending_user_message
        self._pending_user_message = ""
        if not user_message or not assistant_text:
            return
        try:
            from quill.core.ai.sessions import (
                ROLE_ASSISTANT,
                ROLE_USER,
                append_turn,
                new_session,
                save_session,
            )

            if self._session is None:
                title = " ".join(user_message.split())[:60] or "Writing session"
                self._session = new_session(title)
            self._session = append_turn(self._session, ROLE_USER, user_message)
            self._session = append_turn(self._session, ROLE_ASSISTANT, assistant_text)
            save_session(self._session)
        except Exception:  # noqa: BLE001 - session logging is best-effort
            pass

    def _on_approve(self, _event: object) -> None:
        if not self._pending:
            return
        action, text, tool = self._pending
        self._pending = None
        self._show_approval(False)
        try:
            if action == "run":
                title = self._tool_titles.get(tool, tool)
                self._run_command(tool)
                self._append("Quill", f"Ran: {title}")
            elif action == "insert":
                self._insert_text(text)
                self._append("Quill", "Inserted into the document.")
            elif action == "replace":
                if self._get_selection():
                    selection = self._get_selection()
                    if self._review_changes is not None and selection != text:
                        # AI-7: let the reader review the change as a navigable,
                        # line-by-line diff before it touches the document.
                        self._review_changes(selection, text, self._apply_reviewed_replace)
                        self._append("Quill", "Opened the change review.")
                    else:
                        self._replace_selection(text)
                        self._append("Quill", "Replaced the selection.")
                else:
                    self._insert_text(text)
                    self._append("Quill", "No selection — inserted at the cursor.")
        except Exception as exc:  # noqa: BLE001
            self._append("Quill", f"Couldn't apply that: {exc}")
        self._announce("Applied")
        self._focus_composer()

    def _apply_reviewed_replace(self, reviewed_text: str) -> None:
        # Callback from the AI-7 diff review dialog: apply the reviewed text as a
        # single replacement of the selection.
        self._replace_selection(reviewed_text)
        self._append("Quill", "Applied the reviewed changes.")
        self._announce("Applied reviewed changes")

    def _on_discard(self, _event: object) -> None:
        self._pending = None
        self._show_approval(False)
        self._append("Quill", "Discarded — nothing was changed.")
        self._announce("Discarded")
        self._focus_composer()

    def _on_copy(self, _event: object) -> None:
        wx = self._wx
        if not self._last_response:
            return
        if wx.TheClipboard.Open():
            try:
                wx.TheClipboard.SetData(wx.TextDataObject(self._last_response))
            finally:
                wx.TheClipboard.Close()
            self._announce("Copied last response to clipboard")

    def show(self) -> None:
        self.dialog.CentreOnParent()
        apply_modal_ids(
            self.dialog,
            affirmative_id=self._wx.ID_CANCEL,
            escape_id=self._wx.ID_CANCEL,
        )
        try:
            # Land in the web view's edit field (or the wx field in fallback).
            self._wx.CallAfter(self._focus_composer)
            show_modal_dialog(self.dialog, "Ask Quill")
        finally:
            self.dialog.Destroy()
