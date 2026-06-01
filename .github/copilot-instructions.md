# Copilot instructions for this repository

## Repository state

This repository contains the implementation source tree together with the product requirements document under `docs/QUILL-PRD.md` and `docs/QUILL-PRD.html`.

When generating code or task plans, treat the PRD as the source of truth for intended architecture and conventions.

## Build, test, and lint commands

There are no runnable project commands in this repo yet. The PRD defines the expected toolchain and CI commands for the future codebase:

```powershell
# Environment setup
uv python install 3.12
uv sync --all-extras
pre-commit install

# Lint + type-check (planned CI)
ruff check .
ruff format .
mypy quill\core quill\io

# Tests (planned CI)
pytest tests\unit -n auto
pytest tests\integration
pytest tests\a11y
pytest tests\perf

# Single test pattern (pytest)
pytest tests\unit\path\to\test_file.py::test_name
```

## High-level architecture (from PRD)

Quill is designed as a screen-reader-first Windows desktop app in Python + wxPython, with a strict separation between UI, core logic, I/O format handlers, platform bindings, and optional AI providers.

- `quill/core/*`: document model, commands, history, keymap, backups, events, metrics, schemas. No `wx` imports.
- `quill/io/*`: per-format readers/writers and outline emitters. Contract is `read(path) -> Document`, optional `write(doc, path)`, optional `outline(doc)`.
- `quill/ui/*`: wxPython shell/editor/dialogs/palette/status bar; consumes `core` and `io`.
- `quill/platform/windows/*`: Windows-specific APIs (screen-reader bridges, DPAPI, shell integration, single-instance, high-contrast, TTS).
- `quill/ai/*`: provider adapters and safety/consent gating for networked actions.
- `quill/plugins/*`: plugin API + manifest validation (v1.0 loader skeleton).
- `quill/tools/*`: internal CLIs (a11y audit, docs generators, diagnostics helpers).
- `tests/{unit,integration,a11y,perf,fixtures}`: split test strategy reflected in CI.

Concurrency model in the PRD:
- UI thread owns widgets and editor buffer.
- Thread pools handle file I/O and heavier compute.
- `wxasync`-managed asyncio handles HTTP/network operations.
- OCR runs in a separate worker process.
- Cross-thread UI updates marshal through `wx.CallAfter`/`wx.CallLater`.

Persistence model in the PRD:
- User data rooted at `%APPDATA%\Quill\...`
- JSON stores validated by schemas under `quill/core/schemas/`
- Atomic writes via temp file + `os.replace`

## Key conventions to preserve

- Screen-reader-first UI: use stock controls in the writing path (`wx.TextCtrl`, `wx.ListBox`, `wx.Dialog`), avoid custom-drawn editor controls.
- The editor surface is the primary interaction surface and should remain plain-text-first.
- Announcements should report action outcomes consistently (NVDA/JAWS/Narrator parity).
- No silent network calls: all cloud/AI actions are explicit opt-in per action with visible progress and outcome.
- `core` must stay UI-framework-agnostic; keep `wx` imports confined to `quill/ui` and `quill/platform/windows`.
- Do not bypass `io` contracts for new format handlers; add format logic as isolated `io/*` modules.
- Avoid shared mutable-state locking patterns in `core`; follow snapshot/merge worker model described in PRD.
- Keep storage robust: schema-validated JSON, `.bak`/recovery behavior, atomic writes on all persistent stores.
- Type and lint policy from PRD: ruff formatting/lint, strict mypy in `core` + `io`, gradual typing in `ui`.
- Security/privacy defaults are non-negotiable: DPAPI for secrets, no document content in logs, explicit consent gate before outbound document data.

## Dialog, Window, and Accessibility Lessons

Apply these rules to every UI change in `quill/ui/*`:

- Keep parent ownership consistent in dialog layout trees.
	- If controls are parented to `panel = wx.Panel(dialog)`, keep that control tree in a panel sizer and attach the panel to an outer dialog sizer.
	- Do not attach the same root sizer to both panel and dialog.
- Prefer stock controls for instructional content users must read.
	- Use `wx.TextCtrl(..., wx.TE_MULTILINE | wx.TE_READONLY)` or list controls for screen-reader review, not transient message boxes when content is long.
- Avoid mutating menu items while menus are open.
	- Defer menu label/enable/check updates until menu close to avoid focus churn and native menu instability under rapid arrow navigation.
- Treat `wx.CallAfter` as optional in tests and fallback environments.
	- Guard with `getattr(wx, "CallAfter", None)` and provide a synchronous fallback where safe.
- Keep dialog focus behavior predictable.
	- Set explicit default buttons, bind Escape/Close consistently, and return focus to editor after modal close.
- Add focused tests for dialog and menu regressions.
	- Include at least one behavior test (or source-contract test when UI stubs are limited) per bug class.
