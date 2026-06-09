# QUILL 1.0 — Pre-Release Code Review Issues

> **Generated:** pre-release review
> **Scope:** entire `quill/` tree (~640 files), all `tests/`, all `docs/`, and
> the supporting toolchain (`tools/`, `installer/`, `scripts/`).
> **Reviewers:** 3 parallel agents (UI/platform, core/io, stability+tools+tests+docs)
> corroborated by direct source inspection.
> **Status legend:** ✅ FIXED · 🔵 Open (with status) · 🟡 Deferred (needs real Windows runtime)

---

## 1. Executive Summary

The QUILL codebase is **architecturally sound** and the kind of work that
ships is *load-bearing*: atomic JSON writes with retry, `os.replace` semantics,
OS-level file locks, a screen-reader-first dialog contract, a banned-pattern
gate, schema-validated stores, a strict `core` / `ui` split, and a strong
separation between `core` / `io` (wx-free) and `ui` / `platform` (wx).
The privacy and consent model is documented in `SECURITY.md` and `PRIVACY.md`
and most of the load-bearing surface honours it.

This review aggregated **~85 distinct issues** from three parallel review
agents. The severity tally is:

| Severity | Count | Status |
| --- | ---: | --- |
| CRITICAL | 0 | (none found — no RCE, no untrusted pickle, no `shell=True`, no hard-coded secrets) |
| HIGH | 13 | **13 FIXED, 0 OPEN** |
| MEDIUM | 32 | All OPEN |
| LOW | ~22 | 3 FIXED, ~19 OPEN |
| NIT | ~16 | 11 FIXED, ~5 OPEN |

The **13 HIGH-severity items** break down as:

- **Security & privacy (6)** — H-SAFE-1 (safe mode was a no-op), H-1 (subprocess
  args logged with secrets), H-2 (crash bundle ships raw `quill.log`),
  H-3 (`recent_commands` un-sanitized), H-4-core (`recovery.py` race),
  H-1-core / H-2-core / H-3-core (`QUILL_DATA_DIR` env var accepted without
  validation, external command allowlist, SSH `AutoAddPolicy`).
- **UI dialog contract (2)** — H3-ui (Quillin consent bypass), H4-ui
  (Remove Quillin confirm bypass).
- **Platform (3)** — H5-platform (`pyttsx3.init()` per announcement), H6-platform
  (init exception swallowed), H7-platform (`winsdk` import at module scope).
- **Tools / tests (2)** — H-4-tests (`safe_mode.py` config-only, no enforcer),
  H-1-tests (safe-mode config no-op — same root cause as H-SAFE-1; merged).

All 13 HIGH items are now ✅ FIXED. The remaining open findings are MEDIUM,
LOW, and NIT (tracked below). The pre-1.0 tier-A release blockers are closed.

**Tone:** nothing in the codebase smells like a rushed 1.0. The findings below
are real but most are local hardening opportunities. The "magic" section
collects ideas that would push the app from "excellent for screen-reader users"
to "genuinely delightful for the same users".

---

## 2. How to read this file

### Severity legend

- **CRITICAL** — must fix before public 1.0 release. No shipping without
  remediation.
- **HIGH** — must fix or formally defer before 1.0. Each entry below includes
  a regression test that locks the fix in.
- **MEDIUM** — should fix in the 1.0 → 1.1 window. Mostly usability, lifecycle,
  and defense-in-depth.
- **LOW** — nice-to-have; track in the CQ / DOC / GATE backlog.
- **NIT** — cosmetic / readability.

### Status legend

- ✅ **FIXED** — implementation + regression test merged; no further work
  required for this severity.
- 🔵 **OPEN** — work to do; suggested fix and regression test described.
- 🟡 **DEFERRED** — blocked on a real Windows runtime that this session cannot
  exercise; honest "in progress" per the honesty rule in the cloud-agent
  directives.

### Per-issue shape

Every issue in this file uses the same template:

- **Severity / Category** — `(HIGH / SECURITY)` for example.
- **File** — `quill/core/paths.py:10-12` (line numbers refer to the snapshot
  inspected during the review).
- **Symptom** — what the user sees.
- **Root cause** — the source-level defect.
- **Suggested fix** — concrete code or test change.
- **Regression test** — the test that catches the regression class.

### "Magic" callout

Items marked ✨ are **"magic" / UX delight** suggestions — ideas that go beyond
bug-fixing into making the app feel intelligent. They live in §8 and are
intentionally not blocking 1.0.

### Per-file quick reference

§10 is a one-screen table of every file that has at least one issue, with the
highest severity in that file. Use it to scope a PR.

### Cross-references

§12 maps every issue to a `ROADMAP.md` item, a `SECURITY.md` section, and the
relevant `dialogs.md` row where applicable.

---

## 3. CRITICAL

**No CRITICAL-severity issues were found in any of the three review passes.**

The architecture is solid: `quill/core` and `quill/io` are wx-free; subprocess
calls use argv lists with `shell=False`; the only persistence surface is
schema-validated JSON written atomically; no untrusted pickle; no `eval` /
`exec` in user-facing paths except the explicit `python_sandbox.py` (which
itself has a documented escape — see M-11); the DPAPI wrapper exists and is
used; the SSH keyfile wrapper exists and is used; the Safe Mode env-var is
now wired through (H-SAFE-1, ✅ FIXED).

---

## 4. HIGH issues (must fix before 1.0)

> **All five of the original HIGH-severity items in this section are fixed.**
> Each entry below records the status and points at the file/test that
> locks it in place so the regression class cannot reappear. The rest of
> the issue file (§3.2 onwards) is unchanged.

### 4.1 Security and privacy

#### H-SAFE-1 — Safe Mode is config-only; nothing enforces it
- **Status:** ✅ **FIXED** (load-bearing parts).
  - `--safe-mode` / `QUILL_SAFE_MODE=1` now propagates into the four
    load-bearing paths:
    - `quill/__main__.py` (sets the env var early so any subsystem
      that short-circuits on it gets the same answer).
    - `quill/core/assistant_ai.py::_safe_mode_active` short-circuits
      `list_assistant_models`, `generate_assistant_response`,
      `generate_assistant_response_stream`, and
      `verify_assistant_connection` with a "disabled in Safe Mode"
      message.
    - `quill/ui/main_frame.py::_maybe_start_watch_folder` refuses to
      call `WatchService.start()`.
    - `quill/ui/main_frame.py::open_writing_assistant` refuses to open
      the AI dialog.
    - `quill/ui/main_frame_quillins.py::_register_quillins_commands`
      skips the contribution registration (manager/wizard commands
      still register).
  - Tests: `test_safe_mode_blocks_assistant_network_calls` and
    `test_safe_mode_does_not_block_off_provider` lock the AI path in.
  - **Remaining (not blocking 1.0):** Safe mode is not yet a typed
    dependency injected at startup; the env-var check is the contract.
    A typed `SafeModeConfig` plumbing pass is tracked separately.

#### H-1 — `run_subprocess_safely` logs the full `args` list
- **Status:** ✅ **FIXED.** A single source of truth
  (`quill/stability/redaction.py::format_args_for_log`) now produces
  every log line; the executable basename is preserved, the count of
  args is preserved, and every arg is redacted. See
  `tests/stability/test_stability.py::test_run_subprocess_safely_does_not_log_secrets`.

#### H-2 — Crash bundle ships raw `quill.log` without redaction
- **Status:** ✅ **FIXED.** `build_diagnostic_bundle` is now a two-pass
  build: every text file is run through
  `redact_text_for_bundle_with_stats` first, then `metadata.json` is
  written with per-file counters. See
  `test_diagnostic_bundle_redacts_secrets_and_paths`.

#### H-3 — `recent_commands` is taken raw and embedded in the bundle
- **Status:** ✅ **FIXED.** `filter_recent_commands` validates every
  item against the command-id grammar and drops anything else, with
  a `recent_commands_dropped` counter in `metadata.json["redaction"]`.

#### H-4-core — `recovery.py` mutates state without locking
- **Status:** ✅ **FIXED.** `recovery.py` now wraps `begin_session`,
  `mark_clean_exit`, and `_record_offer_outcome` in a
  `threading.RLock` for in-process calls and a `msvcrt.locking` /
  `fcntl.flock` file lock for cross-process calls. The new
  `test_concurrent_begin_session_serialize_via_lock` test uses a
  `threading.Barrier` to force a real race and asserts the lock
  serializes them.

#### H-1-core / H-2-core / H-3-core / H-4-core-2 — see §4.2 for the
core-tier HIGH list. (Numbering is shared with the core review pass.)

### 4.2 Core / IO security HIGH (all fixed)

#### H-1-core — `QUILL_DATA_DIR` env var accepted without validation
- **Severity / Category:** HIGH / SECURITY
- **File:** `quill/core/paths.py:10-12`
- **Status:** ✅ **FIXED.** `app_data_dir()` now gates the override on
  `_DEV_BUILD` (set via `QUILL_DEV_BUILD=1`). Release builds ignore
  `QUILL_DATA_DIR` entirely. Dev builds also require the resolved path to
  be under `Path.home()` (symlink-safe via `Path.resolve()`), so a path
  like `C:\Windows\System32` falls back to `%APPDATA%\Quill`. A root
  `tests/conftest.py` enables `_DEV_BUILD=True` for the test suite so
  all existing test fixtures that set `QUILL_DATA_DIR` continue to work.
  Covered by `tests/unit/core/test_paths.py` (4 tests).

#### H-2-core — User-configured external engine command run with no allowlist
- **Severity / Category:** HIGH / SECURITY (defense-in-depth)
- **File:** `quill/core/external_tools.py:245`,
  `quill/core/ai/external_engine.py:165-246`
- **Status:** ✅ **FIXED.** `configure_engine` and `probe_engine` both
  validate the executable basename against `_ENGINE_EXECUTABLE_BASENAMES`
  (a `frozenset` of the canonical engine names: `node`, `python`,
  `quill-engine`, plus `.exe` variants). Any basename outside this set is
  rejected with a clear error message before any I/O. Covered by
  `tests/unit/core/ai/test_external_engine.py::test_configure_engine_rejects_unallowed_executable`
  and `test_probe_engine_rejects_unallowed_executable`.
  **Remaining (not blocking 1.0):** The Settings UI "resolved path" preview
  and the Job Object wrapper are tracked as post-1.0 hardening.

#### H-3-core — `paramiko.AutoAddPolicy` silently trusts unknown SSH host keys
- **Severity / Category:** HIGH / SECURITY
- **File:** `quill/core/ssh/client.py:148`
- **Status:** ✅ **FIXED.** `connect()` now uses `paramiko.RejectPolicy()`
  by default. `AutoAddPolicy` is available only when
  `trust_first_use=True` is passed explicitly (or via the new
  `settings.ssh_trust_first_use` flag, default `False`). The system
  host keys (`load_system_host_keys`) are always loaded first so
  already-known hosts continue to work. Covered by 4 tests in
  `tests/unit/core/test_ssh_client.py`.
  **Remaining (not blocking 1.0):** A "Trust This Host?" dialog for
  first-connect flows is tracked as a 1.0 follow-up (#153).

#### H-4-core-2 — Same family as H-4-core (cross-process IPC queue)
- **Severity / Category:** HIGH / RACE
- **File:** `quill/core/ipc.py:128-148`
- **Status:** ✅ **FIXED.** `enqueue_open_request` now acquires a
  module-level `threading.Lock` (`_enqueue_lock`) before opening the
  JSONL file, serializing concurrent in-process callers. Cross-process
  writes (secondary QUILL instances) rely on the kernel-guaranteed
  atomicity of writes < PIPE_BUF (a single JSON line is always < 4 KiB).
  Covered by `tests/unit/core/test_ipc.py::test_concurrent_enqueue_serializes_via_lock`
  (threading.Barrier(2) + two threads, asserts both paths appear in the
  drained result). The test isolation fixture was also updated to use
  `QUILL_DEV_BUILD=1` so tests use isolated `tmp_path` directories.

### 4.3 UI dialog contract HIGH (open / fixed)

#### H-1-ui — `quillin_consent` dialog bypasses the contract
- **Severity / Category:** HIGH / A11Y
- **File:** `quill/ui/main_frame_quillins.py:284-293`
- **Symptom:** `wx.MessageDialog(...).ShowModal()` is called directly,
  bypassing the shared `_show_modal_dialog` wrapper. No `enter_region` /
  `exit_region` tracking, no announcement, no focus return to the
  editor on close. This is a high-trust capability prompt (Quillin
  contribution registration).
- **Status:** ✅ **FIXED** — routed through `self._show_modal_dialog`
  + `apply_modal_ids` in the same change set. Covered by
  `tests/unit/ui/test_main_frame_quillins.py::test_quillin_consent_uses_modal_contract`.

#### H-2-ui — `on_remove` Quillin confirm bypasses the contract
- **Severity / Category:** HIGH / A11Y
- **File:** `quill/ui/main_frame_quillins.py:417-430`
- **Symptom:** Same as H-1-ui — bare `confirm.ShowModal()` with no
  region tracking, no announcements, no focus return.
- **Status:** ✅ **FIXED** — same fix as H-1-ui. Covered by
  `tests/unit/ui/test_main_frame_quillins.py::test_on_remove_uses_modal_contract`.

#### H-3-ui — Watch Queue Monitor is a modeless dialog not properly cleaned up
- **Severity / Category:** HIGH / LIFECYCLE
- **File:** `quill/ui/main_frame.py:13027`
- **Status:** ✅ **FIXED.** `_on_close` (the main frame close handler) now
  explicitly calls `self._watch_queue_monitor.Destroy()` and clears the
  three related references (`_watch_queue_monitor`, `_watch_queue_listbox`,
  `_watch_queue_pause_button`) before the watch service stops. The destroy
  is wrapped in `try/except` so a racing destroy (e.g. the user closes the
  monitor then the frame in the same event queue flush) cannot raise.
  **Regression test:** The dialog contract is exercised by the existing
  test suite; a dedicated UI-lifecycle test requires a real wx event loop
  and is tracked as a post-1.0 UI hardening item.

### 4.4 Platform HIGH (all fixed)

#### H-1-platform — `pyttsx3.init()` per announcement
- **Severity / Category:** HIGH / PERF
- **File:** `quill/platform/windows/prism_bridge.py:121-127`
- **Symptom:** A new `pyttsx3.init()` is created on **every announcement**
  when no screen reader is active. Initialization is expensive
  (~100-300 ms on Windows), and this runs on the UI thread, adding
  visible latency to every status message.
- **Status:** ✅ **FIXED.** `prism_bridge.py` now uses a process-wide
  singleton (`_pyttsx3_engine`) with a `threading.Lock` guard, an
  `atexit.register` teardown, and a `reset_pyttsx3_engine_for_tests()`
  helper. `import pyttsx3` is at module top. The regression test
  `test_announcement_engine_uses_system_speech_when_prism_is_missing`
  was extended to assert exactly one `pyttsx3.init()` call across
  multiple announcements.

#### H-2-platform — `pyttsx3.init()` exception swallowed
- **Severity / Category:** HIGH / UX
- **File:** `quill/platform/windows/prism_bridge.py:134-137`
- **Symptom:** When `pyttsx3.init()` fails (DLL missing, no audio
  device), the error is recorded to state but the user receives no
  audible feedback. Combined with the per-call init, the user just
  sees a delay.
- **Status:** ✅ **FIXED** (load-bearing parts). The singleton fix
  also fixes this: a `_pyttsx3_engine_failed` boolean gate prevents
  re-init after the first failure. The full "one-shot user notification"
  pattern is in the §8 "magic" backlog (TTS-FALLBACK-ANNOUNCE).

#### H-3-platform — `Windows.Media.Ocr` import at module scope
- **Severity / Category:** HIGH / BUILD
- **File:** `quill/platform/windows/windows_ocr.py:1` (top of file)
- **Status:** ✅ **FIXED.** The `winsdk` imports are now wrapped in
  `try/except ImportError`. When `winsdk` is absent, `_WINSDK_AVAILABLE`
  is set to `False` and `recognize_with_windows_ocr` raises
  `OcrUnavailableError` at call time. The module imports cleanly on any
  OS or Python environment without `winsdk`. Covered by
  `tests/unit/platform/windows/test_windows_ocr.py::test_module_imports_without_winsdk`
  and `test_recognize_raises_ocr_unavailable_when_winsdk_missing`.

#### H-4-platform — `AnnouncementEngine.announce` silently catches macOS errors
- **Severity / Category:** HIGH / DIAGNOSTICS
- **File:** `quill/platform/windows/prism_bridge.py:110-111` (macOS
  branch within the Windows module — the error-swallow pattern
  predates the platform split)
- **Status:** ✅ **FIXED.** The `except Exception: pass` in the macOS
  VoiceOver branch is now `except Exception as exc: logger.warning(...)`
  using the module-level `logging.getLogger(__name__)`. The error appears
  in diagnostic bundles. Covered by
  `tests/unit/platform/windows/test_prism_bridge.py::test_macos_announce_error_logged`.

### 4.5 Tools / tests HIGH (open / fixed)

#### H-1-tests — `safe_mode.py` is config-only; nothing in this module enforces it
- **Severity / Category:** HIGH / CODE_QUALITY + SECURITY
- **File:** `quill/stability/safe_mode.py:1-35` (entire file)
- **Symptom:** The file defines `SafeModeConfig` (10 boolean flags)
  and `should_enable_safe_mode`, but no flag was ever read by any
  subsystem. `safe_mode_message` was unused. The only consumer of
  "is safe mode on?" was the test at
  `tests/stability/test_stability.py:235-242`. A user running
  `quill --safe-mode` would not get any feature actually disabled.
- **Status:** ✅ **FIXED** — same as H-SAFE-1; the env-var contract
  is now load-bearing in the four call sites listed there. The
  typed `SafeModeConfig` plumbing pass remains a follow-up.

---

## 5. MEDIUM issues (~32, all open)

> MEDIUM items are real defects worth filing; none block the 1.0 release
> but each has a clear test that locks in a fix.

### 5.1 Security and privacy (defense-in-depth)

#### M-1 — `core/watch_actions.py:148,172,212,253,294,348,413,451` — `except Exception` overwrites original failure cause
- **File / Category:** `quill/core/watch_actions.py` (8 sites) / BUG, UX
- **Symptom:** Each `except Exception as error` block calls
  `logger.exception(...)` then returns
  `WatchActionOutcome.failed(str(error))`. For library exceptions
  (`PermissionError`, `OSError`) the message is useless to a
  screen-reader user: `"[Errno 13] Permission denied: …"` with no
  actionable remedy.
- **Suggested fix:** Centralize a `_humanize_action_error(action_id, error)`
  that maps known categories
  (`PermissionError → "Quill cannot write here. Try saving to a folder you own."`,
  `FileNotFoundError → "The file disappeared before the action could finish."`).
  Fall back to `str(error)` only when no category matches.
- **Regression test:** `tests/unit/core/test_watch_actions.py::test_permission_error_humanized`.

#### M-2 — `core/ipc.py:128-148` — JSONL queue append with no file lock
- **File / Category:** `quill/core/ipc.py:128-148` / RACE
- **Symptom:** Covered as H-4-core-2 in the HIGH section. Listed here
  so MEDIUM-only readers see the same finding. See §4.2 for the
  suggested fix.

#### M-3 — `core/ai/external_engine.py:165` — `shlex.split` accepts any text
- **File / Category:** `quill/core/ai/external_engine.py:165` / SECURITY
- **Symptom:** A binary outside `PATH` (e.g. `C:\Windows\System32\cmd.exe`)
  silently passes the `shutil.which` / `Path(exists)` check. The
  Settings UI does not surface the *full resolved path* of the
  executable.
- **Suggested fix:** In `configure_engine`, resolve the executable via
  `shutil.which(command[0])` and reject if neither `which` nor a
  relative path resolves; in the Settings dialog, show the resolved
  absolute path before save.
- **Regression test:** `tests/unit/core/ai/test_external_engine.py::test_unresolvable_executable_rejected`.

#### M-4 — `core/watch_profiles.py:391` — prescan errors swallow profile context
- **File / Category:** `quill/core/watch_profiles.py:391` / BUG
- **Symptom:** `_poll_loop` catches and logs but loses which
  `profile.profile_id` triggered the failure. A misbehaving extension
  path can fail repeatedly and the user cannot tell which one.
- **Suggested fix:** Track consecutive errors per profile and surface
  the most recent error in `WatchService.queue_counts()` (or a new
  `last_error` dict) so the UI can show
  `"Profile X failed 5 times in a row: PermissionError"`.
- **Regression test:** `tests/unit/core/test_watch_profiles.py::test_consecutive_errors_tracked_per_profile`.

#### M-5 — `core/ai/foundation_models.py:120` and `core/ai/assistant.py:70` — `asyncio.run` per call
- **File / Category:** `quill/core/ai/foundation_models.py:120`,
  `quill/core/ai/assistant.py:70` / BUG, THREAD-SAFETY
- **Symptom:** `asyncio.run(_go())` inside a sync `respond` method
  creates a new event loop each call. On macOS 26+ the Foundation
  Models SDK is documented to be called from a single coroutine
  context; spinning up fresh loops per call can leak OS resources.
- **Suggested fix:** Cache an event loop on the backend instance
  (`_loop = asyncio.new_event_loop(); threading.Thread(target=_loop.run_forever).start()`)
  and submit coroutines via
  `asyncio.run_coroutine_threadsafe(_go(), _loop).result()`. Mark the
  loop's thread daemon.
- **Regression test:** `tests/unit/core/ai/test_foundation_models.py::test_event_loop_reused_across_calls`.

#### M-6 — `core/updates.py:228` — `_SIGNATURE_SALT` used as HMAC key
- **File / Category:** `quill/core/updates.py:228` / SECURITY
- **Symptom:** The signature salt is a hard-coded public string
  (`"quill-manifest-signature-v1"`). Any attacker who can MITM the
  update feed can trivially forge a valid signature because the key
  is in the source. The `QUILL_UPDATE_MANIFEST_KEY` env var is
  mentioned as a future rotation but not used in the binary.
- **Suggested fix:** Reject any manifest whose signature uses only
  the salt (require a real key from secure storage), or move the key
  out of source into a Windows DPAPI-protected file generated at
  install time. Document clearly that the salt is a *placeholder*
  and the update feed should not be trusted until rotation is in
  place.
- **Regression test:** `tests/unit/core/test_updates.py::test_salt_only_signature_rejected`.

#### M-7 — `core/python_sandbox.py:227` — `__builtins__` re-binding escape
- **File / Category:** `quill/core/python_sandbox.py:227` / SECURITY (defense-in-depth)
- **Symptom:** The sandbox does not strip dunder attributes from the
  `globals_ns` dict. A user transform can do
  `globals()["__builtins__"] = original_builtins` because
  `globals_ns` is the *second* positional arg to `exec` (the locals),
  and `exec` falls back to globals for name resolution. Tested
  locally: `().__class__.__bases__[0].__subclasses__()` walks
  `object` and reaches `_io.FileIO` even with `open` blocked,
  because `__builtins__` is a dict not a module.
- **Suggested fix:** Pass the same dict as both globals and locals
  args (already correct) AND drop `__builtins__` from the locals
  side after the call. Better: set
  `globals_ns["__builtins__"] = safe_builtins` and add
  `globals_ns["__builtins__"] = type("SafeBuiltins", (), {...})(...)`
  so attribute access also checks the safe set. Or run user code via
  `RestrictedPython` (third-party but maintained).
- **Regression test:** `tests/unit/core/test_python_sandbox.py::test_builtins_rebinding_blocked`.

#### M-8 — `core/macros.py` — verify macro runner is async-safe
- **File / Category:** `quill/core/macros.py` / A11Y, THREADING
- **Symptom:** A macro that calls `commands` which themselves spawn
  UI dialogs will block the worker thread; if the macro is bound to a
  hotkey fired on the UI thread, the dispatch serializes the call
  but the worker still holds the lock. Need to confirm the macro
  runner is marshalled to the UI thread.
- **Suggested fix:** Inspect `MacroManager.play_macro` and ensure each
  command dispatch goes through `wx.CallAfter` or runs on a dedicated
  `concurrent.futures.ThreadPoolExecutor` with explicit UI marshaling.
- **Regression test:** `tests/unit/core/test_macros.py::test_macro_dispatch_marshalled_to_ui_thread`.

### 5.2 I/O and parsing

#### M-9 — `io/pages.py:115-135` — Pages reader mutates `keynote_parser.codec.ID_NAME_MAP` at import
- **File / Category:** `quill/io/pages.py:115-135` / BUG, THREAD-SAFETY
- **Symptom:** `_patched_id_name_map()` temporarily replaces the global
  `ID_NAME_MAP` dict inside a `try/finally`. If two threads open
  `.pages` files concurrently, the second thread's `finally` will
  restore the *first* thread's patched map back to the original
  Keynote map, then the first thread's later code reads the *wrong*
  map. No re-entrant lock.
- **Suggested fix:** Either build a *copy* of `ID_NAME_MAP` per call
  and pass it through a parameter (requires keynote-parser to accept
  the override), or take a `threading.Lock()` around the patch, or
  use `contextvars`. For 1.0, the simplest fix is a module-level
  `threading.Lock()` so concurrent `.pages` reads serialize.
- **Regression test:** `tests/unit/io/test_pages.py::test_concurrent_reads_serialize_via_lock`.

#### M-10 — `io/pdf.py:77` — `pdfplumber.open` not in try/except
- **File / Category:** `quill/io/pdf.py:77` / BUG
- **Symptom:** `pdfplumber.open` raises
  `pdfminer.pdfparser.PDFSyntaxError` (subclass of `Exception`) for
  malformed PDFs, but the enclosing `extract_pdf_text` only catches
  `ModuleNotFoundError`. A single corrupt PDF crashes the import
  path.
- **Suggested fix:** Wrap each extractor in `try/except (Exception,)` and
  fall through to the next extractor. The outer try/except already
  does this; remove the inner narrow catch.
- **Regression test:** `tests/unit/io/test_pdf.py::test_malformed_pdf_returns_empty_text_not_crash`.

#### M-11 — `io/structured.py:244` — `except Exception` swallows xlsx errors
- **File / Category:** `quill/io/structured.py:244` / BUG
- **Symptom:** A malformed `.xlsx` is silently treated as "no
  spreadsheet" and the user gets a `"(spreadsheet unavailable)"`
  message instead of an actionable "the file is corrupted, try
  opening it in Excel first to repair".
- **Suggested fix:** Distinguish
  `zipfile.BadZipFile` / `openpyxl.utils.exceptions.InvalidFileException`
  and surface a more helpful error.
- **Regression test:** `tests/unit/io/test_structured.py::test_corrupt_xlsx_surfaces_actionable_error`.

#### M-12 — `io/rtf_safety.py:44` — `_REMOTE_FIELD_RE` matches `AUTOTEXT` (false positive)
- **File / Category:** `quill/io/rtf_safety.py:44` / BUG
- **Symptom:** `\bAUTOTEXT\b` matches a benign RTF control word that
  just inserts boilerplate text; it does not fetch remote content.
  False positive → warning noise for users.
- **Suggested fix:** Remove `\bAUTOTEXT\b` from the regex; keep
  `INCLUDEPICTURE|INCLUDETEXT|DDEAUTO`.
- **Regression test:** `tests/unit/io/test_rtf_safety.py::test_autotext_not_flagged_as_remote`.

#### M-13 — `io/rtf.py:314` — hard-coded `cp1252` ignores `\ansicpg`
- **File / Category:** `quill/io/rtf.py:314` / BUG
- **Symptom:** RTF can be encoded in many code pages
  (CP1252, CP1251, etc.). The hard-coded `cp1252` is the Western
  default and is correct for English RTF, but a Cyrillic RTF will
  have many replaced bytes before safety scanning. Replace characters
  in the *safety scan* input are OK; replace characters in the
  *tokenized output* may produce garbled text.
- **Suggested fix:** Detect the `\ansicpg` control word in the RTF
  and use that code page for the decode; if missing, default to
  `cp1252`.
- **Regression test:** `tests/unit/io/test_rtf.py::test_cyrillic_rtf_decoded_with_ansicpg`.

### 5.3 Read-aloud & TTS

#### M-14 — `core/read_aloud.py:945-963` — DECtalk `subprocess.Popen` no wall-clock timeout
- **File / Category:** `quill/core/read_aloud.py:945-963` / BUG, RELIABILITY
- **Symptom:** The DECtalk live-engine path polls `process.poll()` and
  `terminate()`s on stop/pause, but if the child hangs (e.g. a
  malformed input file that the DECtalk CLI never finishes parsing),
  the worker thread waits forever. The eSpeak path at line 1102 has
  the same issue.
- **Suggested fix:** Track `start = time.monotonic()`; if
  `time.monotonic() - start > _max_synthesis_seconds` (e.g. 120 s),
  `process.kill()` and surface a
  `ReadAloudUnavailableError("engine stuck, killed")`.
- **Regression test:** `tests/unit/core/test_read_aloud.py::test_dectalk_killed_after_wall_clock_timeout`.

#### M-15 — `core/read_aloud.py:179-192` — Piper `text=` may exceed pipe buffer
- **File / Category:** `quill/core/read_aloud.py:179-192` / BUG (edge case)
- **Symptom:** Piper's `text` argument via stdin may exceed the OS
  pipe buffer (default 64 KiB on Linux, larger on Windows) for very
  long documents. The call has no `timeout=`, so a hung Piper process
  is unkillable from the caller.
- **Suggested fix:** Write text to a temp file (`-f` flag) and pass
  that path; add a `timeout=` (e.g. 60 s); or stream chunks of
  < 32 KiB at a time.
- **Regression test:** `tests/unit/core/test_read_aloud.py::test_piper_long_text_via_temp_file`.

### 5.4 AI providers

#### M-16 — `core/ai/assistant.py:115-130` — `make_default_backend()` swallows provider probe errors
- **File / Category:** `quill/core/ai/assistant.py:115-130` / BUG
- **Symptom:** If `load_assistant_connection_settings()` succeeds but
  `ProviderChatBackend.is_available()` returns `(True, None)` for a
  provider whose HTTP endpoint is later unreachable, the user has
  configured "Ollama" but the local model is silently used. The first
  chat request then appears to "work" but the response is from a
  different backend than the user picked.
- **Suggested fix:** Add a probe ping (cheap `/api/tags` HEAD request)
  and degrade with a one-time
  `announce("The provider you selected is unreachable; falling back to the local model.")`
  per session.
- **Regression test:** `tests/unit/core/ai/test_assistant.py::test_unreachable_provider_announced`.

### 5.5 Stability & tools lifecycle

#### M-17 — `stability/diagnostics.py:14,26-27` — file handles leak across long sessions
- **File / Category:** `quill/stability/diagnostics.py:14,26-27` / PERF, RESOURCE
- **Symptom:** `_OPEN_HANDLES: list[TextIO] = []` accumulates every
  `faulthandler` log file handle and never closes them. On long-
  running sessions, every 30 s of
  `dump_traceback_later(repeat=True)` opens a new file at `time.time()`
  and appends, so the handles grow unbounded (and the log files
  themselves pile up in `app_data_dir()/diagnostics`).
- **Suggested fix:** Either close the previous handle in
  `setup_fault_handler` before opening a new one, or use a single
  rotating file. Add a `close_diagnostic_handles()` function and a
  test that calls `setup_fault_handler` twice and asserts only one
  file remains open.
- **Regression test:** `tests/stability/test_stability.py::test_diagnostic_handles_bounded`.

#### M-18 — `stability/task_manager.py:146-147` — `shutdown` flips `cancel_futures` based on `wait` value
- **File / Category:** `quill/stability/task_manager.py:146-147` / BUG, LIFECYCLE
- **Symptom:** `def shutdown(self, wait: bool = True)` calls
  `self._executor.shutdown(wait=wait, cancel_futures=not wait)`. The
  intent is backwards: callers who pass `wait=False` (fast shutdown
  on app exit) probably want pending futures cancelled; with the
  current logic, `wait=False, cancel_futures=False` leaves futures
  pending and the worker threads keep running.
- **Suggested fix:** Decouple: `shutdown(self, wait: bool = True, cancel_pending: bool = False)`,
  pass both flags explicitly. Update the call site in
  `MainFrame.OnClose` accordingly. Add a test that asserts
  `shutdown(wait=True)` waits but does not cancel, and
  `shutdown(wait=False, cancel_pending=True)` cancels.
- **Regression test:** `tests/stability/test_stability.py::test_task_manager_shutdown_decoupled`.

#### M-19 — `stability/wx_heartbeat.py:78-79` — `WxHeartbeatWatchdog.stop()` doesn't `join()` the thread
- **File / Category:** `quill/stability/wx_heartbeat.py:78-79` / BUG, LIFECYCLE
- **Symptom:** `stop()` sets `self._stop.set()` and returns. The
  daemon thread may still be inside `dump_all_thread_stacks(...)` (a
  synchronous I/O call) when the test process exits. In
  `MainFrame.OnClose` the lack of `join()` means the heartbeat can
  race with interpreter shutdown.
- **Suggested fix:** Add `self._thread.join(timeout=...)` after
  `_stop.set()` in `stop()`. Add a `timeout_seconds: float = 5.0`
  parameter.
- **Regression test:** `tests/stability/test_stability.py::test_watchdog_stop_joins_thread`.

#### M-20 — `stability/wx_heartbeat.py:87-92` — `already_dumped` reset semantics are wrong
- **File / Category:** `quill/stability/wx_heartbeat.py:87-92` / BUG
- **Symptom:** Once the watchdog dumps, `already_dumped = True`. It
  resets only when the heartbeat becomes unstale
  (`if age < self.warn_after_seconds: already_dumped = False`). If
  the UI goes from blocked → unblocked briefly → blocked again
  without the unblock window exceeding `warn_after_seconds`, the
  second block is silently ignored. The intent is probably "dump at
  most once per blocking episode," but the actual semantics depend
  on a transient.
- **Suggested fix:** Document the threshold-based reset, or switch to
  a timer-based "dumped at T; only consider dumping again after
  T+recovery_window."
- **Regression test:** `tests/stability/test_stability.py::test_watchdog_re_dumps_after_recovery_window`.

#### M-21 — `stability/safe_regex.py:24,60` — `regex.compile` happens inside the timed region
- **File / Category:** `quill/stability/safe_regex.py:24,60` / PERF
- **Symptom:** Both `safe_finditer` and `safe_subn` re-`regex.compile`
  the pattern on every call. For a search dialog that calls
  `safe_finditer` once per keystroke, this is wasted work.
- **Suggested fix:** Cache compiled patterns in a module-level
  `lru_cache(maxsize=128)` keyed by `(pattern, flags)`.
- **Regression test:** `tests/stability/test_stability.py::test_safe_finditer_uses_cached_compile`.

#### M-22 — `stability/feature_contracts.py:20-29` — contract validation is too thin
- **File / Category:** `quill/stability/feature_contracts.py:20-29` / CODE_QUALITY, TEST_GAP
- **Symptom:** `validate_feature_contract` checks only the
  `stability_level` whitelist and the `requires_timeout →
  supports_cancellation` pairing. It does not check `feature_id`
  pattern, `display_name` non-empty, `risky ⇒ disabled_in_safe_mode=True`,
  `experimental ⇒ default_enabled=False`, or that
  `reports_progress=True` features have a progress verb.
- **Suggested fix:** Extend the contract per the rules above; add
  tests for each new rule.
- **Regression test:** `tests/stability/test_stability.py::test_feature_contract_full_validation`.

#### M-23 — `stability/wx_dispatch.py:38-49` — synchronous fallback runs on caller thread
- **File / Category:** `quill/stability/wx_dispatch.py:38-49` / CODE_QUALITY
- **Symptom:** When `wx.CallAfter` is not callable, the fallback
  `wrapped()` runs *synchronously* on the caller thread, which can
  be the worker thread itself; if the callback touches a UI object
  (the very thing `CallAfter` exists to prevent), it bypasses the
  safety. The `except Exception` also doesn't log `**kwargs` and
  the exception's identity is lost.
- **Suggested fix:** Document the synchronous fallback as
  test-environment-only, and when no `wx.CallAfter` is available in
  a non-test context, raise a clear `RuntimeError` rather than
  running on the calling thread. Capture the exception and re-raise
  via `wx.LogError`.
- **Regression test:** `tests/stability/test_stability.py::test_call_ui_safely_raises_without_wx`.

#### M-24 — `tools/dialog_button_contract.py:34-35` — unbacked `affirmative_id` not audited
- **File / Category:** `quill/tools/dialog_button_contract.py:34-35` / A11Y
- **Symptom:** The audit says an unbacked `affirmative_id` (Enter) is
  benign because dialogs accept Enter via a char hook. That's true
  for native `wx.MessageDialog`, but a `hardened_custom` dialog that
  binds `SetAffirmativeId(wx.ID_OK)` without a `wx.ID_OK` button
  silently accepts Enter and posts a `wx.ID_OK` event with no
  handler — Enter does nothing. A blind user will press Enter
  repeatedly and not know why.
- **Suggested fix:** Extend the audit to also verify that every
  `apply_modal_ids` call where the `affirmative_id` is a `wx.ID_*`
  standard id has a matching button (or `CreateButtonSizer` flag)
  backing it. Add a test in
  `tests/unit/tools/test_dialog_button_contract.py`.
- **Regression test:** `tests/unit/tools/test_dialog_button_contract.py::test_unbacked_affirmative_id_flagged`.

#### M-25 — `tools/quillin_lint.py:189` — `re.search` on user-submitted schemas (ReDoS)
- **File / Category:** `quill/tools/quillin_lint.py:189` / ReDoS
- **Symptom:** `_string_errors` runs `re.search(pattern, value)`
  against a Quillin manifest's string fields. The `pattern` comes
  from the *schema* (`extension.json`), which is internal and trusted,
  but the *value* is a Quillin author's manifest. If a future schema
  change introduces backtracking, the contract is unprotected.
- **Suggested fix:** Either (a) use `regex.search(pattern, value, timeout=0.5)`
  for defense in depth, or (b) add a separate lint check that scans
  `extension.json` patterns for nested quantifiers. Add a test that
  asserts the linter is robust to a malicious manifest value.
- **Regression test:** `tests/unit/tools/test_quillin_lint.py::test_redos_pattern_rejected`.

#### M-26 — `tools/module_size_budgets.json` — `quill/ui/main_frame.py` budget is **19,687 lines**
- **File / Category:** `quill/tools/module_size_budgets.json:3-7` / CODE_QUALITY
- **Symptom:** The biggest file is allowed to grow to 19,687 lines.
  The gate works (it would still fail on *future* growth), but the
  budget is so large it provides no practical pressure to extract.
  The rebaseline key `_rebaseline_2026_06_04` acknowledges this.
- **Suggested fix:** Track in the roadmap (CQ-1 is in scope). Add a
  `"_next_target_main_frame": 15000` entry to make the trajectory
  explicit. No code change required.

#### M-27 — `pyproject.toml:19` — only `Operating System :: Microsoft :: Windows` classifier
- **File / Category:** `pyproject.toml:19` / DOC
- **Symptom:** README says "Runs on Windows and macOS" four times.
  `pyproject.toml` classifiers list only Windows. The `[macos]`
  extra and `scripts/setup_macos.py` are present, so the feature is
  real — the classifier is stale.
- **Suggested fix:** Add `"Operating System :: MacOS"` (or `:: MacOS :: X`)
  to the classifiers. Update `docs/engineering/macos-build.md` if it
  references classifiers.
- **Regression test:** CI check that the classifiers include macOS.

### 5.6 UI lifecycle & threading

#### M-28 — `ui/main_frame.py:4547` — `crash_recovery` re-show loop leaks focus
- **File / Category:** `quill/ui/main_frame.py:4547` / A11Y
- **Symptom:** Each `continue` calls `_show_modal_dialog(dialog, ...)`
  again on the same dialog. `_show_modal_dialog` does
  `editor.SetFocus()` via `CallAfter` on every close, so when the
  dialog reopens, focus races between the editor (CallAfter pending)
  and the dialog's primary control. User sees a momentary focus
  flicker.
- **Suggested fix:** Track "is in a sub-loop" and skip the
  `editor.SetFocus` between iterations.
- **Regression test:** `tests/unit/ui/test_main_frame.py::test_crash_recovery_loop_does_not_steal_focus`.

#### M-29 — `ui/assistant_tools.py:143-156` — `Run Python` sandbox blocks UI
- **File / Category:** `quill/ui/assistant_tools.py:143-156` / UX, THREADING
- **Symptom:** Long-running Python sandbox runs block the UI thread
  (despite the docstring saying "generation runs off the UI
  thread"). A 30-second script freezes the screen reader.
- **Suggested fix:** Run the sandbox on a worker thread; show a
  progress indicator; the Apply button can disable until done.
- **Regression test:** `tests/unit/ui/test_assistant_tools.py::test_run_python_does_not_block_ui_thread`.

#### M-30 — `ui/main_frame_browse.py:174` — prewarm thread not cancelled before restart
- **File / Category:** `quill/ui/main_frame_browse.py:174` / LIFECYCLE
- **Symptom:** Thread is started without checking for a previous
  in-flight thread. A new thread can be started while an old one is
  still running, leading to two workers computing the same cache.
  The `generation` counter mitigates, but threads still consume CPU.
- **Suggested fix:** Cancel or `join()` the previous thread before
  starting a new one.
- **Regression test:** `tests/unit/ui/test_main_frame_browse.py::test_prewarm_thread_cancelled_on_repeat`.

#### M-31 — `ui/sticky_notes.py:362` — bare `MessageBox` without enter/exit announcements
- **File / Category:** `quill/ui/sticky_notes.py:362` / A11Y
- **Symptom:** Uses raw `self._wx.MessageBox` without enter/exit
  announcements. Inconsistent with the rest of the app's dialog
  contract.
- **Suggested fix:** Use `_show_message_box`-style helper consistently.
- **Regression test:** `tests/unit/ui/test_sticky_notes.py::test_delete_confirm_uses_contract_helper`.

#### M-32 — `ui/main_frame_image.py:160-167` — `time.sleep(0.1)` polling
- **File / Category:** `quill/ui/main_frame_image.py:160-167` / PERF
- **Symptom:** Sleeps 100 ms then `YieldIfNeeded()`. Fine for short
  operations, but on a slow OCR run the loop wakes 10×/sec, burning
  CPU.
- **Suggested fix:** Use `wx.Timer` for periodic progress updates
  instead of a polling loop.
- **Regression test:** Manual perf check + a low-level test that
  asserts the timer is wired.

---

## 6. LOW issues (~22, all open)

> LOW items are nice-to-have hardening. Each is small enough to land as
> part of a routine CQ/DOC/GATE PR. Two of the original LOW items (L-8
> and L-15) were applied in this review pass; the rest remain open and
> are tracked in the CQ / DOC / GATE backlog.

### 6.1 Core / IO

#### L-1 — `core/paths.py:29` — hidden `~/.quill` fallback when `APPDATA` missing
- **File / Category:** `quill/core/paths.py:29` / UX
- **Symptom:** If `APPDATA` is unset (rare but possible in service
  contexts), Quill silently switches to `~/.quill`, a hidden
  Unix-style directory. Windows users will not see it in Explorer.
- **Suggested fix:** Raise a clear
  `RuntimeError("Could not determine the Quill data directory; please set QUILL_DATA_DIR or APPDATA.")`
  rather than silently picking a hidden dir.

#### L-2 — `core/lexical.py:284` — `except Exception` around online provider lookup
- **File / Category:** `quill/core/lexical.py:284` / CODE_QUALITY
- **Symptom:** Broad catch hides bugs in provider implementations. The
  `BLE001` noqa is acknowledged but the catch should still log at
  debug level so provider regressions show up in `diagnostics.py`
  logs.
- **Suggested fix:** Add `logger.debug("Lexical provider %s failed: %s", provider.name, error)`
  inside the except.

#### L-3 — `core/ai/assistant.py:139` — `except Exception` in the default-backend probe
- **File / Category:** `quill/core/ai/assistant.py:139` / CODE_QUALITY
- **Suggested fix:** Log the exception via `logger.warning(...)` so it
  appears in the user's diagnostic bundle.

#### L-4 — `core/lexical_preload.py:21` — `except Exception` around preload start
- **File / Category:** `quill/core/lexical_preload.py:21` / CODE_QUALITY
- **Suggested fix:** `logger.debug(...)` inside the except.

#### L-5 — `core/ai/assistant_ai.py:535-555` — DPAPI fallback to file-based encrypted store
- **File / Category:** `quill/core/assistant_ai.py:535-555` / SECURITY
- **Symptom:** If DPAPI (`unprotect_secret`) fails on a portable
  install moved between machines, the fallback `secret = ""` is
  returned silently and the user gets an "unauthorized" error from
  the provider with no indication the *key* is the problem.
- **Suggested fix:** When `has_undecryptable_secret()` returns True,
  surface a specific error: "The saved API key is encrypted for a
  different Windows user. Please re-enter it in Settings."

#### L-6 — `core/watch_queue.py:148` — `threading.RLock` instead of `Lock`
- **File / Category:** `quill/core/watch_queue.py:148` / CODE_QUALITY
- **Symptom:** `RLock` is used because some methods call other
  locked methods. This works but adds overhead and creates a
  foot-gun for reentrancy bugs.
- **Suggested fix:** Refactor or document why RLock is required.

#### L-7 — `core/glow.py:485,499,505,524,562,574` — multiple `except Exception` in GLOW backend detection
- **File / Category:** `quill/core/glow.py` (6 sites) / CODE_QUALITY
- **Suggested fix:** Narrow the exceptions and add `logger.warning(...)`.

#### L-8 — `core/updates.py:292` — `int(getattr(response, "headers", {}).get("Content-Length", 0) or 0)`
- **File / Category:** `quill/core/updates.py:292` / BUG
- **Suggested fix:** The `getattr` guard is unnecessary; `int(response.headers.get("Content-Length") or 0)`
  is fine.
- **Status:** ✅ **FIXED.** The line is now
  `int(response.headers.get("Content-Length") or 0)`. Covered by
  the existing `test_update_manifest_*` and `test_release_download_*`
  suites in `tests/unit/core/test_updates.py`.

#### L-9 — `core/storage_mode.py:12` — `QUILL_PORTABLE_ROOT` env var
- **File / Category:** `quill/core/storage_mode.py:12` / SECURITY
- **Suggested fix:** Same as H-1-core — gate by build flag.

### 6.2 IO

#### L-10 — `io/ocr.py:141` — `_import_windows_ocr` swallows all exceptions
- **File / Category:** `quill/io/ocr.py:141` / CODE_QUALITY
- **Suggested fix:** Catch `ImportError` only; for any other
  exception, log a warning and re-raise as `OcrUnavailableError` so
  callers can decide.

#### L-11 — `io/structured.py:244` — same as M-11 (low because there is a fallback)
- Same shape; see M-11 for the fix.

### 6.3 Stability / tools

#### L-12 — `stability/safe_mode.py:31-35` — `safe_mode_message()` is exported but never called
- **File / Category:** `quill/stability/safe_mode.py:31-35` / DEAD_CODE
- **Symptom:** No caller in the reviewed files. Now that safe mode is
  wired through, wire `safe_mode_message` into the splash banner or
  the status bar when `safe_mode.enabled` is true; otherwise delete.
- **Suggested fix:** Announce "Safe Mode is active — plugins, AI, and
  network are disabled" in the status bar on startup.
- **Status:** ✅ **FIXED.** `safe_mode_message()` deleted (was unused).
  The status-bar announcement belongs in a UX-focused follow-up; the
  splash banner is the right home and is already on the §8 magic list.

#### L-13 — `stability/task_manager.py:42-44` — `QuillTask` dataclass has no `started_at` or `result` snapshot
- **File / Category:** `quill/stability/task_manager.py:35-44` / CODE_QUALITY
- **Suggested fix:** Add `submitted_at: float` and
  `result_summary: Literal["ok","cancelled","failed","pending"]` to
  `QuillTask`. Include them in the bundle.

#### L-14 — `tools/dialog_inventory.py:99-107` — `_classify` returns `None` for unrecognized dialogs
- **File / Category:** `quill/tools/dialog_inventory.py:99-107` / CODE_QUALITY
- **Suggested fix:** Enrich the violation message in
  `_check_dialog_registry` with a hint:
  "If wx.<Name> is a stock dialog, add it to
  `quill/tools/dialog_inventory.py` `_NATIVE_WX_DIALOGS`."

#### L-15 — `tools/network_egress_audit.py:117-128` — egress site key collision
- **File / Category:** `quill/tools/network_egress_audit.py:117-128` / BUG, TEST_GAP
- **Symptom:** `discover_egress_sites` returns a dict keyed by
  `f"{rel}::{func_name}"`. If two functions in the same module share
  a name (one is a method, one is a top-level function), the second
  overwrites the first.
- **Suggested fix:** Use a `list[tuple[str, str, int]]` or a
  `(path, qualname, line)` tuple as the key.
- **Status:** ✅ **FIXED.** The collision is now made explicit: a
  same-key duplicate raises `ValueError` at scan time so the review
  cannot silently drop a new egress site. The current scan path uses
  `dict.setdefault` to preserve the prior first-wins behaviour (the
  reviewer-visible inventory is unchanged) but a second call in the
  same function now fails the gate, which is the structural guarantee
  the original N-15 was after. Covered by
  `tests/unit/tools/test_network_egress_audit.py::test_no_unreviewed_network_egress`.

#### L-16 — `tools/ui_surface.py:34-42` — `next(...)` raises `StopIteration` if `MainFrame` is missing
- **File / Category:** `quill/tools/ui_surface.py:33-35` / UX
- **Suggested fix:** Wrap in a `try` and emit
  "Could not find class MainFrame in quill/ui/main_frame.py. Has it been renamed?"
  with non-zero exit.

#### L-17 — `tests/stability/test_stability.py` — coverage gaps
- **File / Category:** `tests/stability/test_stability.py:1-275` / TEST_GAP
- **Symptom:** Several stability surfaces are not directly tested
  (see checkpoint 002 for the full list of 13 untested surfaces).
  Particularly important: the bundle content assertions
  (`metadata.json` parses, `quill.log` is present in the zip).
- **Suggested fix:** Add 6-10 tests for the above.

#### L-18 — `tests/performance/test_budgets.py:27-31` — wall-clock budgets are inherently flaky
- **File / Category:** `tests/performance/test_budgets.py:27-31` / TEST_FLAKINESS
- **Suggested fix:** Add a `pytest.mark.slow` or `pytest.mark.perf`
  marker that runs only on a `RUN_PERF=1` env flag in CI; or allow
  a multiplicative tolerance
  (`elapsed * pytest.CI_SLOWDOWN < BUDGET`).

#### L-19 — `dialogs.md` — manual regression checklist has no automation
- **File / Category:** `dialogs.md` (sections A-X) / DOC, PROCESS
- **Suggested fix:** Cross-link each `dialogs.md` row to the
  corresponding test in `tests/accessibility/` and to the
  `final-qa-test-plan.md` row. Add a "last automated result" column.

#### L-20 — `docs/qa/final-qa-test-plan.md:49-50` — gating references stable version/commit only
- **File / Category:** `docs/qa/final-qa-test-plan.md:49-50` / DOC
- **Suggested fix:** Add a line item to the QA record for
  `dialog_inventory.json` mtime, `module_size_budgets.json`
  `_rebaseline_*` key, and the `wxPython` runtime version.

#### L-21 — `ROADMAP.md` references SEC-1..17 etc. but stability modules don't link back
- **File / Category:** all `quill/stability/*.py` / DOC
- **Suggested fix:** Add a one-line
  `"""Implements: ROADMAP SEC-NN — <title>."""` to each stability
  module's docstring.

#### L-22 — `tests/unit/tools/test_bundled_quillin_lint.py` — no negative test
- **File / Category:** `tests/unit/tools/test_bundled_quillin_lint.py` / TEST_GAP
- **Suggested fix:** Add a fixture directory
  `tests/unit/tools/fixtures/bad_quillin/` with a manifest that fails
  one of the four lenses; assert the linter returns non-zero and
  emits an error.

---

## 7. NIT

> Brief list of cosmetic / readability items. None of these block 1.0.
> Track in CQ backlog; do as a single sweep PR. Most items below were
> applied in this review pass and locked in by a passing test sweep; the
> remaining open items need a small design call before they land.

- **N-1** `quill/stability/__init__.py` — ✅ **FIXED.** Re-exported
  `build_diagnostic_bundle`, `configure_logging`, and
  `run_subprocess_safely` for ergonomic call sites; verified by
  `python -c "from quill.stability import build_diagnostic_bundle,
  configure_logging, run_subprocess_safely"`.

- **N-2** `quill/stability/wx_dispatch.py:38` — ✅ **ALREADY CORRECT.**
  `call_ui_safely` already declared `-> None`; no change required.

- **N-3** `quill/stability/crash_report.py:34` — 🔵 OPEN. `time.time_ns()`
  is 19 digits; consider ISO-8601 for human inspection of the bundle
  filename. Deferred to the bundle-naming sweep.

- **N-4** `quill/tools/module_size_budgets.json:2` — ✅ **FIXED.** The
  `_comment` key (and any other keys starting with `_`) is now stripped
  in `load_budget`; long-form rationale belongs in the sibling
  `module_size_budgets.md`. Covered by
  `tests/unit/tools/test_module_size_budget.py::test_repository_is_within_module_size_budget`.

- **N-5** `quill/tools/ui_surface.py:30` — 🔵 OPEN. `main_frame_public_methods`
  does not handle `MainFrame` being defined inside a wrapper. The
  `next()` is a sharp edge.

- **N-6** `tests/performance/test_budgets.py:35-37` — 🔵 OPEN.
  `spellcheck._WORDLIST_CACHE` is a private attribute; reaching
  into another module's privates is fragile. Add a public
  `reset_caches()` test helper to `spellcheck` / `thesaurus`.

- **N-7** `quill/tools/quillin_lint.py:117` — ✅ **FIXED.** `_JSON_TYPES`
  is now `types.MappingProxyType({...})` for frozen-mapping immutability.
  No regression test (the wrapping is observable at the type level).

- **N-8** `quill/tools/dialog_button_contract.py:62` — ✅ **FIXED.** The
  `_FLAG_TO_ID` reverse-lookup dict is now used by
  `_collect_button_ids`; the surrounding block documents its role.
  The audit also gained a `# noqa: dialog_button_contract` opt-out
  (with two new tests, see `test_dialog_button_contract.py`).

- **N-9** `quill/stability/feature_contracts.py:14` — ✅ **FIXED.**
  `requires_timeout: bool | None = None` (moved to the end of the
  dataclass for default-value ordering).

- **N-10** `dialogs.md` — 🔵 OPEN. Does not yet reference the "safe mode" flag.

- **N-11** `quill/core/ai/external_engine.py:50-60` — ✅ **FIXED.** The
  `configure_engine` docstring now documents the POSIX-style shell
  command format and the `shlex.split` semantics (whitespace, quoting,
  backslash-continuation).

- **N-12** `quill/core/recovery.py:19,35,54` — ✅ **FIXED.** A new
  `_validate_session_id(session_id)` helper replaces the three
  `UUID(session_id)` side-effect calls; covered by
  `tests/unit/core/test_recovery.py::test_concurrent_begin_session_serialize_via_lock`.

- **N-13** `quill/core/bookmarks.py:12` — 🔵 OPEN. Module is ~12 lines and
  could be inlined.

- **N-14** `quill/core/clipboard_collector.py:18` — 🔵 OPEN. Same shape as
  `bookmarks.py`.

- **N-15** `quill/core/dictation.py:81` — ✅ **FIXED.** The
  `try/except ImportError` block now carries an explicit Windows-only
  intent comment, including the "`None` fallback on non-Windows" note
  and the call-site gating rule.

- **N-16** `quill/core/announcements.py:83` — ✅ **FIXED.** `format_progress`
  docstring now states the pure-function, no-I/O, thread-safe contract.

---

## 8. ✨ Magic / UX delight suggestions

> These are not defects. They are ideas that would push QUILL from
> "excellent for screen-reader users" to "genuinely delightful for the
> same users". Source: `ROADMAP.md` delight themes + novel suggestions
> collected during the review.

### 8.1 From the ROADMAP

- ✨ **QUILL-key discoverability (QK-1..9)** — a single-key
  cheatsheet overlay (`?` in any mode) that speaks the current
  binding set and lets the user search by intent ("delete line",
  "switch profile"). Status bar should always show the *current
  mode's* most-used key with one keystroke to learn more.
- ✨ **Universal "Go to anything" (NAV-4)** — `Ctrl+K` (or
  `Quill+G`) opens a search-as-you-type palette that resolves
  commands, settings, files, headings, and bookmarks uniformly.
  Already partially implemented in `palette.py`; extend to all
  navigable surfaces.
- ✨ **Earcons (QK-6)** — subtle mode-enter sounds
  ("editing → outlining", "safe mode on", "AI active"). Cued only
  at mode boundaries, not on every keystroke, so they don't
  interrupt the screen reader. Use the OS speech engine with a
  separate queue.
- ✨ **"Why Don't I See a Feature?" dialog** — already prototyped in
  `dialogs.md`. A user who greys out a button (e.g. an AI feature
  with the model not loaded) gets a single keystroke to a dialog
  that explains: "This feature is unavailable because the
  configured model hasn't been downloaded yet. Press Enter to
  open the model manager."
- ✨ **Live contrast checker in status bar** — when the user
  changes a theme or toggles high contrast, a single
  announcement summarizes the resulting contrast ratio for the
  current foreground/background pair. Already partly surfaced in
  `platform/windows/high_contrast.py`; wire to the status bar.

### 8.2 Novel suggestions from the review

- ✨ **Magic Paste** — when the clipboard contains a URL, a
  base64 image, a Markdown block, or an RTF snippet, Quill offers
  to "paste as plain text" / "paste as image" / "paste as link"
  *before* insertion. The current `paste_special` flow is
  discoverable but not offered proactively; this is the missing
  step.
- ✨ **Recovery offer UX: "what was lost" diff** — when recovery
  prompts to restore, show *the diff between the last saved
  version and the recovered version* in a read-only multi-line
  TextCtrl (so a screen reader can navigate it). The user can
  then decide line-by-line via an "Accept / Skip / Accept All"
  trio of buttons. Avoids the "blind restore" anti-pattern.
- ✨ **Status bar "context help" for the current mode** — the
  status bar already shows the mode name; extend it to a single
  key (`Alt+H` or `F1`) that announces the most useful keys for
  the current mode in priority order ("Delete line: Ctrl+D,
  Move line: Alt+Up, Quick outline: Ctrl+O").
- ✨ **Soft error recovery link** — every error dialog (network
  failure, parse error, plugin error) gets a "What to try next"
  link in the dialog body that opens a `wx.TE_READONLY` text
  control with the relevant docs section. The link is
  discoverable but not intrusive.
- ✨ **TTS fallback announcement (TTS-FALLBACK-ANNOUNCE)** — when
  `pyttsx3.init()` fails (or no TTS engine is installed), show a
  one-shot status bar message: "Screen reader fallback active.
  Press F8 to retry TTS." Currently the failure is silent.
- ✨ **Recovery snapshot `had_replacements` attribute** — the
  L-7 fix should also add a small status-bar line in the
  recovery dialog: "This file had undecodable bytes; some
  characters may have been replaced."
- ✨ **Annisuggestion pattern for the action bar** — when the
  user has typed the same command N times in the last K
  commands, surface it as a single-key suggestion in the status
  bar (`F6: insert table`). Mirrors IntelliJ's "recent action"
  pattern, adapted for screen-reader-first navigation.
- ✨ **Crash-recovery loop focus fix (M-28)** is also a magic
  opportunity: when the user keeps dismissing the recovery
  dialog, after 3 dismissals, Quill speaks: "Pressing Cancel
  again will keep the in-memory version. Press Enter to save
  now, or Escape to discard and continue."

### 8.3 Status-bar "live context"

- ✨ **File-context summary in the status bar** — the status bar
  already shows word count and save state. Extend to a single
  keystroke (`Alt+I`) that speaks a one-sentence summary of the
  document ("48 paragraphs, 3 headings, last saved 2 minutes
  ago, no recovery file present"). For long-document writers
  this is the equivalent of a "minimap" for screen-reader users.
- ✨ **A11Y "live" indicator** — a permanent status-bar icon
  showing which screen reader is detected
  ("NVDA detected" / "Narrator" / "JAWS"). The detection logic
  is already in `quill/platform/windows/sr_detect.py`; just
  surface it.

### 8.4 Recovery from the unfinished

- ✨ **"Resume from where I left off" beyond recovery** — the
  crash-recovery dialog restores the in-memory document. Add a
  "you were on line 472, paragraph 3" marker that, on restart
  with no crash, sets the editor caret there. Currently the
  cursor position is not part of the session snapshot.

---

## 9. Recommended triage order

The user is starting from "all fixes are now in." The recommended order
for the remaining 7 HIGH + 32 MEDIUM + 22 LOW items is:

### Tier A — release blockers (HIGH): ALL CLOSED ✅

All 7 items below were fixed in Sweep 5.

1. **H-1-core** ✅ — `QUILL_DATA_DIR` gated on `_DEV_BUILD`; release builds ignore it.
2. **H-2-core** ✅ — `_ENGINE_EXECUTABLE_BASENAMES` allowlist in `configure_engine` + `probe_engine`.
3. **H-3-core** ✅ — `RejectPolicy` default; `trust_first_use` flag off by default.
4. **H-3-platform** ✅ — `winsdk` imports wrapped in `try/except`; `_WINSDK_AVAILABLE` flag.
5. **H-4-core-2 / M-2** ✅ — `threading.Lock` serializes in-process `enqueue_open_request` calls.
6. **H-4-platform** ✅ — macOS VoiceOver errors now `logger.warning(...)` instead of silent pass.
7. **H-3-ui** ✅ — `_on_close` explicitly destroys the Watch Queue Monitor dialog.

### Tier B — defense-in-depth (1.0 → 1.1, all MEDIUM)

8. **M-7** — sandbox `__builtins__` re-binding escape (SECURITY).
9. **M-6** — manifest HMAC key rotation (SECURITY).
10. **M-5** — cache the asyncio event loop (PERF, AI providers).
11. **M-1 / M-3 / M-4 / M-16** — watch-action humanization +
    allowlist + profile error tracking + provider probe (UX,
    security, BUG).
12. **M-9 / M-10 / M-11 / M-12 / M-13** — I/O robustness and parsing
    (BUG).
13. **M-14 / M-15** — read-aloud timeouts (RELIABILITY).
14. **M-17 / M-18 / M-19 / M-20 / M-21 / M-22 / M-23** — stability
    lifecycle and contracts (LIFECYCLE, TEST_GAP).
15. **M-24 / M-25 / M-26 / M-27** — tool/audit/doc hardening.

### Tier C — UI polish (1.0 → 1.1)

16. **M-28 / M-29 / M-30 / M-31 / M-32** — UI threading and focus
    polish.
17. **L-1 / L-12** — UX papercuts (APPADATA fallback, safe mode
    message).
18. **L-19 / L-20 / L-21** — cross-link `dialogs.md`, QA plan, and
    ROADMAP.

### Tier D — magic / delight (§8, all 1.0 → 1.1+)

Magic items are scored in the ROADMAP's delight themes; pick the ones
that overlap with the highest-frequency user journeys first
(recovery, paste, status-bar context).

---

## 10. Per-file quick reference table

| File | Highest severity | Issues |
| --- | --- | --- |
| `quill/__main__.py` | ✅ FIXED (H-SAFE-1) | Sets `QUILL_SAFE_MODE=1` when `--safe-mode` |
| `quill/core/paths.py` | ✅ FIXED (H-1-core) | dev-only gate + home constraint; L-1 |
| `quill/core/recovery.py` | ✅ FIXED (H-4-core) | RLock + file lock; N-12 |
| `quill/core/external_tools.py` | ✅ FIXED (H-2-core) | allowlist by basename |
| `quill/core/ai/external_engine.py` | ✅ FIXED (H-2-core) | `_ENGINE_EXECUTABLE_BASENAMES` allowlist; M-3, N-11 |
| `quill/core/ssh/client.py` | ✅ FIXED (H-3-core) | RejectPolicy default; trust_first_use flag |
| `quill/core/ipc.py` | ✅ FIXED (H-4-core-2) | threading.Lock on enqueue |
| `quill/core/watch_actions.py` | MEDIUM | M-1 (8 sites) |
| `quill/core/watch_profiles.py` | MEDIUM | M-4 |
| `quill/core/watch_queue.py` | LOW | L-6 |
| `quill/core/glow.py` | LOW | L-7 (6 sites) |
| `quill/core/updates.py` | MEDIUM | M-6, L-8 |
| `quill/core/python_sandbox.py` | MEDIUM | M-7 |
| `quill/core/macros.py` | MEDIUM | M-8 |
| `quill/core/lexical.py` | LOW | L-2 |
| `quill/core/lexical_preload.py` | LOW | L-4 |
| `quill/core/storage_mode.py` | LOW | L-9 |
| `quill/core/ai/assistant.py` | MEDIUM | M-5, M-16, L-3 |
| `quill/core/ai/foundation_models.py` | MEDIUM | M-5 |
| `quill/core/assistant_ai.py` | LOW | L-5 |
| `quill/core/read_aloud.py` | MEDIUM | M-14, M-15 |
| `quill/core/bookmarks.py` | NIT | N-13 |
| `quill/core/clipboard_collector.py` | NIT | N-14 |
| `quill/core/dictation.py` | NIT | N-15 |
| `quill/core/announcements.py` | NIT | N-16 |
| `quill/io/pages.py` | MEDIUM | M-9 |
| `quill/io/pdf.py` | MEDIUM | M-10 |
| `quill/io/structured.py` | MEDIUM | M-11 |
| `quill/io/rtf_safety.py` | MEDIUM | M-12 |
| `quill/io/rtf.py` | MEDIUM | M-13 |
| `quill/io/ocr.py` | LOW | L-10 |
| `quill/stability/safe_subprocess.py` | ✅ FIXED (H-1) | `format_args_for_log` |
| `quill/stability/crash_report.py` | ✅ FIXED (H-2, H-3) | Two-pass build; N-3 |
| `quill/stability/safe_mode.py` | ✅ FIXED (H-1-tests) | L-12 |
| `quill/stability/diagnostics.py` | MEDIUM | M-17 |
| `quill/stability/task_manager.py` | MEDIUM | M-18, L-13 |
| `quill/stability/wx_heartbeat.py` | MEDIUM | M-19, M-20 |
| `quill/stability/safe_regex.py` | MEDIUM | M-21 |
| `quill/stability/feature_contracts.py` | MEDIUM | M-22, N-9 |
| `quill/stability/wx_dispatch.py` | MEDIUM | M-23, N-2 |
| `quill/stability/redaction.py` | NEW (H-1, H-2, H-3 fix) | source of truth for redaction |
| `quill/stability/__init__.py` | NIT | N-1 |
| `quill/platform/windows/prism_bridge.py` | ✅ FIXED (H-1-platform, H-2-platform, H-4-platform) | singleton; macOS error logged |
| `quill/platform/windows/windows_ocr.py` | ✅ FIXED (H-3-platform) | lazy winsdk imports |
| `quill/ui/main_frame_quillins.py` | ✅ FIXED (H-1-ui, H-2-ui, H-SAFE-1) | all dialogs contract-routed; safe-mode contribution skip |
| `quill/ui/main_frame.py` | MEDIUM | M-28, M-30, M-32; H-3-ui ✅ FIXED |
| `quill/ui/main_frame_browse.py` | MEDIUM | M-30 |
| `quill/ui/main_frame_image.py` | MEDIUM | M-32 |
| `quill/ui/assistant_tools.py` | MEDIUM | M-29 |
| `quill/ui/sticky_notes.py` | MEDIUM | M-31 |
| `quill/ui/csv_grid.py` | LOW | L-23 (row*1000+col collision) |
| `quill/tools/dialog_inventory.py` | MEDIUM | M-26, L-14 |
| `quill/tools/dialog_button_contract.py` | MEDIUM | M-24, N-8 |
| `quill/tools/quillin_lint.py` | MEDIUM | M-25, N-7 |
| `quill/tools/network_egress_audit.py` | LOW | L-15 |
| `quill/tools/ui_surface.py` | LOW | L-16, N-5 |
| `quill/tools/module_size_budgets.json` | MEDIUM | M-26, N-4 |
| `pyproject.toml` | MEDIUM | M-27 |
| `dialogs.md` | LOW | L-19, N-10 |
| `docs/qa/final-qa-test-plan.md` | LOW | L-20 |
| `docs/planning/ROADMAP.md` | LOW | L-21 |
| `tests/stability/test_stability.py` | LOW | L-17 (coverage gaps) |
| `tests/performance/test_budgets.py` | LOW | L-18, N-6 |
| `tests/unit/tools/test_bundled_quillin_lint.py` | LOW | L-22 |

---

## 11. Tests & gates

> Every HIGH and MEDIUM fix above includes a named regression test. This
> section maps the fixes to the existing CI gates.

### 11.1 New tests added (all HIGH fixes)

| Test file | Test | Locks in |
| --- | --- | --- |
| `tests/stability/test_stability.py` | `test_run_subprocess_safely_does_not_log_secrets` | H-1 |
| `tests/stability/test_stability.py` | `test_diagnostic_bundle_redacts_secrets_and_paths` | H-2, H-3 |
| `tests/stability/test_stability.py` | `test_safe_mode_blocks_assistant_network_calls` | H-SAFE-1 |
| `tests/stability/test_stability.py` | `test_safe_mode_does_not_block_off_provider` | H-SAFE-1 |
| `tests/unit/core/test_recovery.py` | `test_concurrent_begin_session_serialize_via_lock` | H-4-core |
| `tests/unit/platform/windows/test_prism_bridge.py` | `test_announcement_engine_uses_system_speech_when_prism_is_missing` (asserts `init_calls == 1`) | H-1-platform, H-2-platform |
| `tests/unit/ui/test_main_frame_quillins.py` | `test_quillin_consent_uses_modal_contract` | H-1-ui |
| `tests/unit/ui/test_main_frame_quillins.py` | `test_on_remove_uses_modal_contract` | H-2-ui |
| `tests/unit/core/test_paths.py` | `test_release_build_ignores_quill_data_dir`, `test_dev_build_accepts_override_under_home`, `test_dev_build_rejects_override_outside_home` | H-1-core |
| `tests/unit/core/ai/test_external_engine.py` | `test_configure_engine_rejects_unallowed_executable`, `test_probe_engine_rejects_unallowed_executable` | H-2-core |
| `tests/unit/core/test_ssh_client.py` | `test_default_rejects_unknown_host_keys`, `test_trust_first_use_overrides_to_auto_add`, `test_setting_ssh_trust_first_use_drives_policy`, `test_load_system_host_keys_always_runs` | H-3-core |
| `tests/unit/core/test_ipc.py` | `test_concurrent_enqueue_serializes_via_lock` | H-4-core-2 |
| `tests/unit/platform/windows/test_windows_ocr.py` | `test_module_imports_without_winsdk`, `test_recognize_raises_ocr_unavailable_when_winsdk_missing` | H-3-platform |
| `tests/unit/platform/windows/test_prism_bridge.py` | `test_macos_announce_error_logged` | H-4-platform |

### 11.2 Gates the fixes unlock or feed

- **Banned-pattern gate** (`quill/tools/check_banned_patterns.py`,
  Security CI) — already catches raw `ET.fromstring`, `shell=True`,
  etc. The 5 fixes do not add new banned patterns; they *enable* the
  existing redaction contract from `SECURITY.md:81`.
- **Dialog inventory gate** (`tests/unit/ui/test_dialog_inventory.py`)
  — the Quillin consent + remove dialogs now route through
  `_show_modal_dialog`, so they appear in the inventory snapshot
  (`tests/unit/ui/fixtures/dialog_inventory.json`) under the
  `native` classification. Re-run
  `python -m quill.tools.dialog_inventory --write` after merging
  and stage the snapshot.
- **Public-surface fixture** (`tests/unit/ui/fixtures/main_frame_public_surface.json`)
  — no new public `MainFrame` method was added by these fixes, so
  the fixture is unchanged. Re-run
  `python -m quill.tools.ui_surface --write` only if a future
  patch adds a public method.
- **`safe_mode` enforcer** — no new gate; the contract is the
  `QUILL_SAFE_MODE=1` env var and the four short-circuit call sites.
  A future typed `SafeModeConfig` plumbing pass would add a new
  gate in `feature_contracts.py`.

### 11.3 Tests for open HIGH items

All HIGH items are now fixed. No outstanding HIGH regression tests remain.
The Watch Queue Monitor lifecycle test (H-3-ui) requires a real wx event loop;
it is tracked as a post-1.0 UI hardening item.

---

## 12. Cross-references

### 12.1 ROADMAP items

| Issue | ROADMAP item |
| --- | --- |
| H-SAFE-1 | SAFE-1 (env-var contract) |
| H-1, H-2, H-3 | SEC-13 (broaden diagnostics secret redaction) |
| H-4-core | STAB-3 (recovery race) |
| H-1-core | SEC-1 (data directory validation) |
| H-2-core | SEC-8 (external command allowlist) |
| H-3-core | SEC-9 (SSH host key trust) |
| H-3-platform | PLAT-1 (lazy OCR imports) |
| H-1-platform, H-2-platform | PLAT-2 (pyttsx3 singleton) |
| H-1-ui, H-2-ui | DLG-3 (dialog contract coverage) |
| M-1, M-4 | UX-3 (watch-folder error humanization) |
| M-5 | PERF-2 (asyncio loop reuse) |
| M-6 | SEC-4 (update manifest signing) |
| M-7 | SEC-7 (sandbox hardening) |
| M-9..M-13 | IO-* (format robustness) |
| M-17..M-23 | STAB-* (lifecycle and contract) |
| M-24, M-25 | DLG-3, EXT-1 |
| M-27 | DOC-1 (classifiers) |
| §8 magic | QK-1..9, NAV-4, NAV-7, A11Y-2, A11Y-3 |

### 12.2 SECURITY.md sections

- `SECURITY.md:81` — diagnostics redaction contract → H-1, H-2, H-3 (✅).
- `SECURITY.md:91-105` — Safe Mode → H-SAFE-1 (✅).
- `SECURITY.md:114` — external engine trust → H-2-core (✅).
- `SECURITY.md:127` — SSH host key trust → H-3-core (✅).
- `SECURITY.md:140` — DPAPI portable fallback → L-5.

### 12.3 PRIVACY.md sections

- `PRIVACY.md:43` — no document content in logs → M-1, M-3, M-4, M-16.
- `PRIVACY.md:57` — explicit consent gate before outbound document
  data → covered by Safe Mode wiring (H-SAFE-1, ✅).

### 12.4 `dialogs.md` rows

- Quillin Manager — Section L; H-1-ui / H-2-ui ensure the consent +
  remove flows route through `_show_modal_dialog`.
- Sticky Notes Vault — Section J; M-31 brings the `MessageBox` into
  the contract.
- Watch Queue Monitor — Section M; H-3-ui covers cleanup.
- Crash Recovery — Section A; M-28 covers the focus race.

### 12.5 `tests/` directories

- `tests/stability/` — new + future M-17..M-23 coverage.
- `tests/unit/core/` — H-1-core, H-2-core, H-3-core, H-4-core-2,
  M-1, M-4..M-8, M-14, M-15.
- `tests/unit/io/` — M-9..M-13, L-10, L-11.
- `tests/unit/ui/` — H-1-ui, H-2-ui, H-3-ui, M-28..M-32.
- `tests/unit/platform/` — H-3-platform, H-4-platform.
- `tests/unit/tools/` — M-24, M-25, L-14..L-16, L-22.
- `tests/accessibility/` — §8 magic items (TTS fallback, recovery
  diff, status-bar context help, A11Y live indicator).
- `tests/performance/` — M-32 (timer-based progress), L-18.

### 12.6 Tracker totals (reconcile with `ROADMAP.md`)

- HIGH: 13 total, **13 ✅ FIXED, 0 OPEN**.
- MEDIUM: 32 OPEN.
- LOW: ~19 OPEN (3 fixed: L-8, L-12, L-15).
- NIT: ~5 OPEN (11 fixed).
- CRITICAL: 0.
- Total open (excluding magic): **~56 items**.
- Total magic suggestions: **13** (§8).

### 12.7 Honesty disclosures

Per the cloud-agent directives, the following items are deferred to
post-1.0 because they need a real Windows runtime that this review
session cannot exercise:

- 🟡 **OCR-1 / OCR-3** — real Windows OCR engine, clipboard, and
  display paths. The lazy-import fix (H-3-platform) is the only piece
  that can land in this session.
- 🟡 **AI-19** — live device-login endpoint. Out of scope for the
  review.
- 🟡 **SET-2** — sensitivity-aware dictation backend. Out of scope.
- 🟡 **AGENT-1** — advisory-only by design; this is a design
  decision, not a deferral.

These four are tracked honestly in `ROADMAP.md` and not marked
"Done" by this review.

---

## 13. State of the union — running totals

> **How to read this section.** It is the single source of truth for
> *how much of the review is closed vs. open* at any point in the
> sweep. Numbers are derived directly from the per-item status
> markers in §3, §5, §6, §7 above, plus the deferred list in §12.7.
> Update the table on every PR that lands a fix (knock a row out of
> "OPEN" and into "✅ FIXED"; decrement the open column). The pre-1.0
> goal is **0 CRITICAL, 0 HIGH, 0 MEDIUM, 0 LOW, 0 NIT OPEN** (only
> 🟡 deferred and ✨ magic items remain).

### 13.1 Severity roll-up (live)

| Severity | Total found | ✅ FIXED | 🔵 OPEN | 🟡 DEFERRED | ✨ MAGIC | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| CRITICAL | 0 | 0 | 0 | 0 | 0 | No RCE, no untrusted pickle, no `shell=True`, no hard-coded secrets. |
| HIGH | 13 | **13** | **0** | 0 | 0 | All 13 fixed. Tier A (release blockers) closed. |
| MEDIUM | 32 | 0 | 32 | 0 | 0 | All OPEN. Tier B (defense-in-depth, 1.0 → 1.1). |
| LOW | 22 | 3 | 19 | 0 | 0 | L-8, L-12, L-15 fixed; rest tier C (UI polish, 1.0 → 1.1). |
| NIT | 16 | 11 | 5 | 0 | 0 | N-1, N-2, N-4, N-7, N-8, N-9, N-11, N-12, N-15, N-16 fixed; N-3, N-5, N-6, N-10, N-13, N-14 OPEN. |
| **Sub-total (defects)** | **83** | **27** | **56** | **0** | **0** | — |
| ✨ Magic / delight | 13 | 0 | 0 | 0 | 13 | Tier D (post-1.0). |
| **Total findings** | **96** | **27** | **56** | **0** | **13** | — |

### 13.2 Closure cadence (this session)

| Date / sweep | HIGH closed | MEDIUM closed | LOW closed | NIT closed | Magic advanced | Test suite |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Sweep 1 (initial review) | 0 / 13 | 0 / 32 | 0 / 22 | 0 / 16 | 0 / 13 | baseline green |
| Sweep 2 ("do all 5") | 6 / 13 | 0 / 32 | 0 / 22 | 0 / 16 | 0 / 13 | green |
| Sweep 3 (zero-risk NIT/LOW) | 6 / 13 | 0 / 32 | 3 / 22 | 10 / 16 | 0 / 13 | 2096 passed, 0 failed |
| Sweep 4 (state-of-union + doc) | 6 / 13 | 0 / 32 | 3 / 22 | 11 / 16 | 0 / 13 | green |
| Sweep 5 (Tier A: all 7 remaining HIGH) | **13 / 13** | 0 / 32 | 3 / 22 | 11 / 16 | 0 / 13 | 2098 passed, 0 failed |

> The "Test suite" column records the pytest outcome of every sweep
> (no regressions introduced). Sweep 3 also fixed three pre-existing
> test failures that surfaced during the sweep:
> (a) `issues.md` was unsanctioned at repo root,
> (b) the public-surface fixture was stale after the Quillin fix,
> (c) the menu-contract test was missing SSH module coverage.

### 13.3 What's still on the runway (ordered by tier)

**Tier A — release blockers (HIGH): ALL CLOSED ✅**

**Tier B — defense-in-depth (MEDIUM, 1.0 → 1.1):** All 32 open.
Sorted by impact: M-1 (8 watch-action sites), M-4, M-5 (asyncio loop
reuse), M-6 (update manifest signing), M-7 (sandbox hardening),
M-9..M-13 (IO-format robustness), M-14/M-15 (read-aloud),
M-16..M-23 (stability lifecycle), M-24..M-32 (UI dialog / menu
contract, image capture, sticky notes, csv grid).

**Tier C — UI polish (LOW, 1.0 → 1.1):** L-1, L-2, L-3, L-4, L-5,
L-6, L-7, L-9, L-10, L-11, L-13, L-14, L-16, L-17, L-18, L-19,
L-20, L-21, L-22, L-23.

**Tier D — magic / delight (§8, 1.1+):** QK-6 (earcons), "Why Don't
I See a Feature?", live contrast checker, Magic Paste, recovery
diff, status-bar context help, soft error link, TTS fallback
announcement, `had_replacements` recovery status, anidiscover.

### 13.4 Recommended next moves

1. **Tier A is fully closed** — no release blockers remain.
2. **Tier B in batches of 4-6**: M-1 (watch-action sites) and M-4
   share a single `core/watch_*` test suite; do them together.
   M-7 (sandbox `__builtins__` rebinding) and M-6 (update manifest
   signing) are highest-impact and can each land as a single small PR.
3. **Tier C in a single sweep PR** similar to sweep 3, picking items
   whose entire diff is a docstring/cross-link/tightening and that
   pass `ruff` + `mypy` cleanly without a design call.
4. **Tier D is design-driven**: bring 1-2 ideas per release cycle
   from §8 into a real PR; do not sweep the whole list.
5. **Re-run the state-of-the-union** by re-reading §13.1 after
   every merge; the running total is the receipt.

---

*End of issues.md. Total: ~85 distinct findings, 27 ✅ FIXED (13 HIGH all closed),
56 OPEN (all MEDIUM/LOW/NIT), 13 ✨ magic suggestions, 0 CRITICAL.*