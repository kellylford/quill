# Blocked-items completion guide — the exact path to Done on the environment-gated 1.0 features

Status as of 2026-06-03. A small set of QUILL 1.0 items are honestly "In progress"
or "Todo" in `golden.md` because they are genuinely blocked on something that cannot
be produced or verified from a non-live development environment: there is no live AI
provider endpoint and no Windows 11 packaged-install cycle available here. None is
faked Done.

This document is the precise, file-by-file runbook for what a maintainer (on a real
Windows 11 machine with live provider credentials) must do to drive each remaining
item to verified Done. Nothing here is hand-waving: every step names the file,
function, and acceptance test. It is the operational companion to the `golden.md`
tracker — the tracker records *what* remains; this guide records *exactly how* to
finish it.

> This guide was previously the working file `zfix2.md`. It is preserved here under
> a descriptive name so the completion steps survive scratch-file cleanup.

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

---

## Appendix A (merged from former zfix4) — SHELL-3 live verification & issue status

This appendix preserves the full SHELL-3 live-verification checklist and intake issue
status that previously lived in `zfix4.md`.

### Part 1 — SHELL-3 verification steps

#### What already shipped (commit `1d3bfc4`, on `main`)

- `build_shell_verb_registry_lines()` in
  `scripts/build_windows_distribution.py` generates the Inno `[Registry]`
  verb keys directly from `quill.core.shell_verbs.default_shell_verbs()`.
- A new opt-in `[Tasks]` checkbox, `shellverbs`, gates every verb key; all
  keys carry `uninsdeletekey` for clean uninstall.
- The committed `installer/quill.iss` is regenerated to include the verbs.
- Six contract tests in
  `tests/unit/scripts/test_build_windows_distribution.py` assert per-verb /
  per-extension coverage, opt-in + uninstall-clean flags, the launch command
  shape, and end-to-end presence in the generated `.iss`.

These are all green (ruff + strict mypy + pytest). **What remains is purely a
live Windows install/uninstall pass — it cannot be done in a non-live
environment and is the only thing standing between SHELL-3 and Done.**

#### Prerequisite: install the Inno Setup 6 compiler (ISCC)

The build box does **not** currently have ISCC. Install it once:

```powershell
winget install --id JRSoftware.InnoSetup --source winget
```

Confirm it resolves (either of these should print a path):

```powershell
Get-Command ISCC.exe -ErrorAction SilentlyContinue
@("C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
  "C:\Program Files\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ }
```

#### Step 1 — Build the portable bundle + installer

From the repo root, with the venv active:

```powershell
# Build the portable tree, regenerate installer/quill.iss, and compile the
# installer in one pass. --bundle-python makes the result self-contained.
python -m scripts.build_windows_distribution --bundle-python --compile-installer
```

Expected: `windows-distribution\installer\Quill-Setup-<version>.exe` (and/or
`...\Output\Quill-Setup-<version>.exe`) is produced. If `--compile-installer`
is not wired as a flag in your build, compile manually:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" `
  windows-distribution\installer\quill.iss
```

#### Step 2 — Install with the "Send to Quill" verbs enabled

1. Run `Quill-Setup-<version>.exe`.
2. On the **Select Additional Tasks** page, **check**
   *"Add 'Send to Quill' actions (OCR, Open, Read aloud) to the file
   right-click menu"* (it is unchecked by default, by design).
3. Finish the install.

Accessibility check while you are here: the task checkbox label must be read
clearly by your screen reader, and the wizard must not auto-close before the
final status is announced (it is configured `CloseApplications=force`,
`RestartApplications=no`).

#### Step 3 — Verify the verbs appear and run (the core test)

The classic registry verbs surface under **"Show more options"** on
Windows 11, and directly in the **Shift+F10** keyboard context menu.

1. In **File Explorer**, navigate to a test **`.png`** (or `.jpg`, `.tif`).
2. Give it focus and press **Shift+F10** (keyboard context menu).
   - On Win11 you may need to arrow to **"Show more options"** first.
3. Confirm these items are present and screen-reader friendly:
   - **OCR with Quill**
   - **OCR with Quill (structured Markdown)** — only meaningful when AI is on
   - **Read aloud in Quill**
   (For a `.txt`/`.md`/`.html` file you should instead see **Open in Quill**
   and **Read aloud in Quill**.)
4. Activate **OCR with Quill**.
5. Confirm: a running QUILL instance is reused (or one launches), focus lands
   on the **OCR review dialog**, and an announcement states what happened.
6. Repeat once for a **`.pdf`** to confirm document handling.

> If a verb does **not** appear, the most likely causes are: the `shellverbs`
> task was left unchecked at install, or another app owns an overriding
> per-extension association. Re-run the installer and confirm the task is
> ticked. The keys are written to **HKCU** (never HKLM), so no elevation is
> needed and no other user is affected.

#### Step 4 — Confirm the registry keys exist (optional, precise)

```powershell
# Should list a "Quill.ocr" subkey with a (default) value of "OCR with Quill"
reg query "HKCU\Software\Classes\SystemFileAssociations\.png\shell\Quill.ocr" /ve
reg query "HKCU\Software\Classes\SystemFileAssociations\.png\shell\Quill.ocr\command" /ve
```

The `\command` default value should be:
`"<install>\run-quill.cmd" --action ocr "%1"`.

#### Step 5 — Uninstall and confirm clean removal

1. Uninstall QUILL (Settings → Apps, or the Start-menu uninstaller).
2. When prompted about removing personal data, either choice is fine for this
   test (that prompt covers `%APPDATA%\Quill`, not the shell verbs).
3. Re-run the `reg query` commands from Step 4 — both must now return
   **"ERROR: The system was unable to find the specified registry key"**,
   proving `uninsdeletekey` cleaned up the verbs.
4. Re-check **Shift+F10** on the test `.png`: the Quill verbs must be gone.

#### Step 6 — Flip SHELL-3 to Done

Once Steps 1–5 pass on real hardware:

- In `golden.md`: change the **SHELL-3** row Status from `In progress` to
  `Done`, move `SHELL-3` out of the two living *Work-in-progress* lists into
  the *Completed* Tier 2 list, and update the tracker totals
  (Tier 2 becomes `60 | 58 | 2 | AI-19, SHELL-2`; bump the 1.0 subtotal and
  grand total Done counts by 1).
- Add a dated activity-log entry recording the live verification pass.
- Regenerate the HTML: `pandoc -s golden.md -o golden.html`.
- Stage `golden.md` + `golden.html` only and commit.

### Part 2 — What's left, issue by issue

#### Umbrella #113 — Open & OCR from the file manager

**Status: substantially delivered on Windows; keep open as the umbrella.**
The shared groundwork it asked for is done: the action-bearing entry point
(`quill --action <verb> "<path>"`), routing through the existing
single-instance IPC, the qualifying file-type sets, and the initial action
set (Open, OCR, Read aloud) all ship via SHELL-1. Close this only when its
three sub-issues are resolved.

#### #114 — Windows Explorer context menu

**Status: classic/Show-more-options path is code-complete and tested; needs
the Part 1 live pass to call done. One sub-item is intentionally deferred.**

| Sub-item from #114 | Status |
| --- | --- |
| Classic registry verbs (`SystemFileAssociations\<ext>\shell\…`) per image ext + `.pdf` | **Done in code** (SHELL-1 runtime writer + SHELL-3 installer registration) |
| Verb invokes shared `--action` entry point over single-instance IPC | **Done** (SHELL-1) |
| Installer registration + clean uninstall | **Done in code** (SHELL-3); **needs live verify** (Part 1) |
| Reachable via Shift+F10; clear labels; focus + announcement after invoke | **Done in code**; confirmed by the Part 1 manual pass |
| **Modern Win11 menu via `IExplorerCommand` (packaged COM)** | **Deferred to QUILL 2.0** — the OS gates the primary menu behind compiled COM + package identity (sparse/MSIX). Out of scope for 1.0. |

**To finish #114 for 1.0:** run Part 1, then post a status comment noting the
modern-menu `IExplorerCommand` piece is tracked as a 2.0 follow-up, and close.

#### #115 — macOS Finder integration

**Status: Blocked, correctly. Not a 1.0 item.**
Depends on the macOS port (#42), which is not done. The OCR engine work it
describes (Apple Vision backend) also lands with the macOS port. No action now.

#### #116 — Structured OCR (AI-gated)

**Status: functionally delivered (SHELL-2), pending one live-AI verification;
the geometry/bounding-box enhancement is an optional follow-up.**

| Sub-item from #116 | Status |
| --- | --- |
| Gate behind AI + explicit `ocr_structured` opt-in setting | **Done** (SHELL-1/SHELL-2) |
| Dedicated `transform`-style op returning structured Markdown | **Done** — assistant `structure` operation |
| Feed structured result into the OCR review dialog | **Done** — `_apply_ocr_structuring` in the OCR worker |
| Plain-text behavior unchanged when AI off | **Done** — degrades safely with a status note |
| **Capture layout geometry (bounding boxes) for tables/columns** | **Not started** — optional quality enhancement; `OcrLine` has no boxes yet. Nice-to-have, can be a 2.0 follow-up. |

**To finish #116 for 1.0:** one live-key end-to-end run + structuring-quality
tuning on real multi-column / table OCR output (this is the SHELL-2 remainder),
then close noting the geometry enhancement is a future improvement.

---

## Open Tier 2 roadmap items (the honest blockers)

After SHELL-1 (Done) and this SHELL-3 work, Tier 2 stands at **57 of 60**.
The three open items and what each genuinely needs:

| ID | What's left | Blocker class |
| --- | --- | --- |
| **SHELL-3** | The Part 1 live install → right-click → run → uninstall pass | Windows runtime + Inno Setup install cycle |
| **SHELL-2** | One live-AI run + prompt-quality tuning on real OCR; then flip to Done | Configured/available AI backend |
| **AI-19** | Real HTTPS device-login poster, `DeviceLoginDialog`, DPAPI token storage, AIBackend wiring, live sign-in (RFC 8628 state machine already built + tested) | Live provider OAuth device endpoint + Windows runtime |

**Closest to Done:** SHELL-3 and SHELL-2 — each needs a single live pass with
no further code. AI-19 still needs real code plus a live provider.

### Explicitly out of scope for 1.0 (do not work on)

- Win11 modern primary-menu `IExplorerCommand` sparse package (the deferred
  half of #114) — 2.0.
- OCR bounding-box geometry capture (the deferred half of #116) — 2.0.
- macOS Finder (#115) — blocked on the macOS port (#42).
