# zfix2 — Exact path to "golden" (Done) on every Tier 2 feature

Status as of 2026-06-03. After this session's work, **Tier 2 stands at 57 of 60
Done**. Three items remain open, all genuinely blocked on something that cannot be
produced or verified from this environment (no live AI provider endpoint, no
Windows 11 packaged-install cycle). Each is honestly "In progress" or "Todo" in
`golden.md` — none is faked Done.

This document is the precise, file-by-file checklist of what **you** (on a real
Windows 11 machine with live provider credentials) must do to drive each remaining
item to verified Done. Nothing here is hand-waving: every step names the file,
function, and acceptance test.

---

## Summary table

| ID | Title | State now | What's already built & tested | What only you can finish | Effort |
| --- | --- | --- | --- | --- | --- |
| AI-19 | Accessible subscription sign-in (OAuth device flow) | In progress | The full RFC 8628 device-flow state machine (`device_login.py`), fully unit-tested with an injected poster | Real HTTPS poster, consent dialog, DPAPI token storage, AIBackend wiring, live end-to-end run | M |
| SHELL-2 | Structured-Markdown OCR verb (AI pass) | In progress | The assistant `structure` operation + `_apply_ocr_structuring` worker wiring, unit + contract tested | One live-key run to verify quality/threading on real OCR output; quality tuning | S |
| SHELL-3 | Windows 11 modern context menu (IExplorerCommand) | Todo | The classic Explorer verb path (SHELL-1) ships and is verifiable | A compiled `IExplorerCommand` COM handler + sparse MSIX package + installer registration + real install/uninstall verification | M–L |

When all three reach Done, **Tier 2 is golden (60/60)** and the QUILL 1.0 subtotal
drops by three remaining.

---

## AI-19 — Accessible subscription sign-in (no pasted API key)

### What already exists (do not rebuild)

- `quill/core/ai/device_login.py` — a complete, wx-free, strict-typed OAuth 2.0
  Device Authorization Grant (RFC 8628) state machine. Public API:
  - `DeviceFlowConfig`, `DeviceCodeGrant`, `PollResult` (frozen dataclasses).
  - `request_device_code(config, *, poster)` — starts the flow.
  - `poll_once(config, grant, *, poster)` — classifies one poll into
    pending / slow_down / authorized / denied / expired / error.
  - `run_device_login(...)` — drives the full polling loop honoring `interval`,
    backing off on `slow_down`, stopping at `expires_in`.
  - `announce_device_code(grant)` — the screen-reader instruction string.
  - `describe_login_result(result)` — the spoken outcome.
  - Every network exchange is an **injected** `poster`, so the engine is already
    tested without a live endpoint (7 tests) and adds no new egress site.
- `quill/platform/windows/credential_manager.py` — DPAPI-backed Windows Credential
  Manager storage already exists:
  - `credential_manager_available()`, `load_generic_credential(target_name)`,
    `save_generic_credential(...)`, `delete_generic_credential(target_name)`,
    `StoredCredential`.
- `quill/core/assistant_ai.py` — `AssistantConnectionSettings` (the saved provider
  connection, including `api_key`), `load_assistant_connection_settings()`, and
  `_build_auth_headers(provider, host, api_key)` is where the credential is
  consumed for outbound requests.

### Exact remaining work (Windows + live provider only)

1. **Real HTTPS poster.** Add a `urlopen`-based poster (TLS-verified) that satisfies
   the `Poster` protocol in `device_login.py`. Put it in a new
   `quill/platform/windows/` or `quill/core/ai/` module (keep `device_login.py`
   itself poster-free so the GATE-9 egress inventory stays explicit — register the
   new `urlopen` site in the egress audit).
   - Acceptance: a unit test that the poster issues a POST with the correct
     `application/x-www-form-urlencoded` body and parses a JSON reply; TLS
     verification is on (no `ssl._create_unverified_context`).

2. **Consent / progress dialog `DeviceLoginDialog`** in `quill/ui/`.
   - Shows: the device code, the verification URL, and the expiry; an
     "Open in browser" button; an "I've authorized — continue" button; a Cancel
     path. Must follow the A11Y-4 dialog contract (outer sizer, default button,
     `Destroy` on close, focus return to editor).
   - Speaks `announce_device_code(grant)` on open and `describe_login_result(...)`
     on completion.
   - Acceptance: a source-contract test (the cloud-safe bar) asserting the dialog
     uses `show_modal_dialog`, shows code/URL/expiry, and wires the three buttons;
     add a row to `dialogs.md` with the menu path that opens it.

3. **DPAPI token storage.** On `authorized`, persist the returned token via
   `save_generic_credential(target_name="Quill/<provider>/oauth", ...)`. Never log
   the token; never write it to the JSON connection file in plaintext.
   - Acceptance: round-trip test through the credential manager (save → load →
     delete) under a `target_name` namespaced per provider.

4. **AIBackend wiring.** Teach `assistant_ai.py` / the provider backend to resolve
   credentials as: device-login token (if present in DPAPI) → else pasted
   `api_key`. The provider must then send the device-login token in
   `_build_auth_headers`.
   - Acceptance: a unit test that, given a stored device-login token and an empty
     pasted key, the auth header carries the token; given both, the device-login
     token wins (or whatever precedence you choose — document it).

5. **Surface the entry point.** Add a "Sign in with your <provider> account" button
   to the AI provider configuration surface (the assistant setup) that launches the
   flow. Gate behind `FeatureManager` like every other AI surface.

6. **Live end-to-end verification** (the actual blocker). On a real Windows machine
   with a provider that genuinely offers an OAuth **device authorization grant** for
   API access:
   - Start the flow → QUILL shows the code + URL → you authorize in the browser →
     QUILL polls and retrieves the token → the token is used for subsequent AI
     requests → **no pasted key required**.
   - Confirm the whole flow is keyboard- and screen-reader-accessible at every step
     (NVDA/JAWS/Narrator parity).
   - **Reality check:** confirm your target provider actually exposes a public
     device-authorization endpoint for API tokens. Several major API providers do
     **not** (they issue API keys from a dashboard instead). If yours doesn't, AI-19
     cannot be honestly closed against that provider — pick one that does (or keep
     the engine ready and mark AI-19 Done only once one real provider validates it).

### Done definition for AI-19

A blind user signs in with an existing subscription via the device flow, with no
visible 51-character secret, the token is stored in DPAPI, and at least one real
provider serves AI responses using that token — all keyboard/screen-reader
accessible and registered in the GATE-9 egress audit.

---

## SHELL-2 — Structured-Markdown OCR verb (AI structuring pass)

### What already exists (built and tested this session)

- `quill/core/ai/assistant.py` — new `structure` operation in `_OPERATION_PROMPTS`:
  reflows raw OCR text into clean Markdown (joins scan-broken lines, groups
  paragraphs, infers headings/lists/tables) and **forbids** summarizing, adding, or
  inventing content. Reuses the existing chunking, `_wrap`, and backend, so large
  scans are handled. Unit-tested in `tests/unit/core/ai/test_structure_operation.py`
  (registration, OCR text reaches the model, the no-summarize instruction).
- `quill/ui/main_frame_image.py` — `_run_ocr_on_path(..., structured: bool = False)`
  and a new `_apply_ocr_structuring(...)` helper that, **inside the existing OCR
  worker thread** (off the UI thread, sharing the progress dialog), structures the
  recognized text via the assistant when one is available and reports available, and
  otherwise degrades safely to plain OCR with a status note saying why. The review
  dialog title and the insert status line reflect whether the structured pass ran.
- `quill/ui/main_frame.py` — `_handle_shell_request` passes
  `structured=action == "ocr-structured"`.
- Source-contract tests in `tests/unit/ui/test_ocr_review_dialog.py` assert the
  worker wiring and the structured-verb dispatch.

### Exact remaining work (needs a live AI key)

1. **One live run.** On Windows with a configured, available assistant backend:
   right-click an image/PDF → "OCR with Quill (structured Markdown)". Confirm the
   recognized text comes back as structured Markdown (headings/lists/paragraphs),
   inserted into the editor, with the "Structured OCR text inserted" status.
2. **Quality tuning.** Inspect the output on harder inputs — multi-column PDFs,
   tables, headers/footers, page numbers. If the model summarizes or drops content,
   tighten the `structure` prompt in `_OPERATION_PROMPTS` (it is the single source
   of truth) and re-run. No code path changes needed — only the prompt string.
3. **Threading/latency check.** Confirm the off-thread `assistant.transform(...)`
   call is thread-safe with your backend and that the progress dialog stays
   responsive (the worker already runs off the UI thread; verify no backend
   requires UI-thread affinity). If a backend needs main-thread marshaling, route
   the structuring call through `wx.CallAfter`-bounded handoff instead.

### Done definition for SHELL-2

The structured verb produces faithful structured Markdown from real OCR output on a
live backend, with no content loss, responsive UI, and accessible status
announcements. Then flip SHELL-2 to Done in `golden.md` (tracker + both living
lists + a dated activity-log entry) and regenerate `golden.html`.

---

## SHELL-3 — Windows 11 modern context menu (IExplorerCommand) + installer

### What already exists

- `quill/platform/windows/shell_integration.py` — the **classic** (pre-Win11)
  `HKCU\Software\Classes\SystemFileAssociations\<ext>\shell\Quill.<verb>` verb path
  ships in SHELL-1 and is buildable and verifiable locally. On Windows 11 these
  verbs appear under "Show more options" (the legacy menu).

### Why this can't be finished from here

The Windows 11 **primary** context menu (the non-"Show more options" menu) only
shows verbs provided by a registered `IExplorerCommand` COM handler packaged in a
sparse/MSIX package. That requires a compiled in-proc COM component and a real
package install — none of which a pure-Python repo can produce or verify in this
environment.

### Exact remaining work (real Windows 11 + packaging toolchain)

1. **Build the `IExplorerCommand` handler.** A compiled in-proc COM server (C++/WinRT
   or Rust, or a packaged .NET COM component) that implements `IExplorerCommand`
   (and `IExplorerCommandState` / `IEnumExplorerCommand` for the submenu). It must
   surface the **same** verbs as the core registry — drive its labels/actions from
   `quill/core/shell_verbs.py` (`default_shell_verbs()`, `verb_for_action`,
   `verbs_for_extension`) so there is exactly one source of truth. Each invoked verb
   launches `quill --action <verb> "<path>"` (reuse `verb_launcher_command(action)`
   from `shell_integration.py`).
   - Submenu shape: a top "Send to Quill" flyout enumerating Open / OCR / OCR
     structured Markdown / Read aloud, filtered by file extension via
     `verbs_for_extension`.

2. **Sparse package + registration.** Author a sparse MSIX package manifest that
   declares the `IExplorerCommand` handler under the relevant
   `windows.fileTypeAssociation` / `desktop4:FileExplorerContextMenus` extension, and
   register/unregister it on install/uninstall.

3. **Installer wiring.** Wire the package register/unregister into the QUILL
   installer (`installer/quill.iss` and/or `scripts/build_windows_distribution.py`)
   so a normal install adds the modern menu and uninstall removes it cleanly. Keep
   the classic-menu fallback for non-packaged/portable installs.

4. **Live install/uninstall verification.** On Windows 11: install → confirm the
   verbs appear in the **primary** right-click menu (not just "Show more options")
   for the correct file types → run each verb → confirm uninstall removes them with
   no orphaned registry/package state. Confirm keyboard and Narrator accessibility of
   the menu entries.

### Done definition for SHELL-3

QUILL's "Send to Quill" verbs appear in the Windows 11 primary context menu via a
registered `IExplorerCommand`, driven by the same `shell_verbs.py` registry,
installed and removed cleanly by the installer, and verified on a real Win11 box.
Then flip SHELL-3 to Done in `golden.md` and regenerate `golden.html`.

---

## Per-change discipline reminder (applies to all three)

- Format then lint only the **specific** changed files: `ruff format <files>`,
  `ruff check <files>`. Do not run whole-tree format (it reflows unrelated drift).
- Strict `mypy` on any changed `quill/core` / `quill/io` file — must report
  "Success: no issues found"; those layers stay wx-free.
- Add at least one behavior test (or source-contract test where wx can't load) per
  change; keep the targeted `pytest` green.
- After editing `golden.md`: update the **tracker totals**, **both living lists**,
  and add a **dated activity-log entry**, then regenerate `golden.html` with
  `pandoc -s golden.md -o golden.html` and commit both together.
- New user-facing dialog (e.g. `DeviceLoginDialog`) → add a row to `dialogs.md`.
- New public `MainFrame` method → regenerate the surface fixture with
  `python -m quill.tools.ui_surface --write`.
- Stage **specific files only**. Never `git add -A`.
