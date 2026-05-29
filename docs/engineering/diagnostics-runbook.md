# Diagnostics bundle specification and support runbook

## Purpose

Quill diagnostics are a user-exported bundle for support and bug triage. The bundle is explicit opt-in and never auto-sent.

## Bundle contents

1. `metadata.json`
   - Quill version
   - OS version
   - Python runtime version
   - timestamp (UTC)
2. `recent-actions.json`
   - last 50 command/event entries from the in-process event stream
3. `settings-redacted.json`
   - non-secret user settings (theme, wrap mode, limits, feature toggles)
4. `keymap.json`
   - active keymap
5. `logs/`
   - recent log files (up to 14 days)
6. `crash/` (if present)
   - last crash traceback dump

## Exclusions and redaction

1. Never include document body text.
2. Never include AI provider keys, tokens, or raw credential material.
3. File paths are included only when user explicitly checks "include file paths"; otherwise hashed paths are used.
4. URL query strings are stripped by default in diagnostics metadata.

## Support workflow

1. User runs **Help → Save Diagnostics…**
2. Quill previews included artifacts and redaction rules.
3. User confirms output path.
4. Quill writes `quill-diagnostics-YYYYMMDD-HHMMSS.zip`.
5. User attaches the zip to the Community Access support form or another support ticket if requested.

## Triage checklist

1. Confirm version and environment from `metadata.json`.
2. Review `recent-actions.json` for the failing action sequence.
3. Correlate with log timestamps.
4. If crash dump exists, map traceback to current source and known issues.
5. Record triage outcome and next action in issue labels/comments.
