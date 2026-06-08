# QUILL 1.0 final-QA test plan

Status: living document — execution owned by the maintainer for the Tier 6
release gate (DLG-3.8). This is the authoritative manual and exploratory test
plan for the QUILL 1.0 release. It complements, and does not replace, the
machine-enforced gate ladder (PR CI, Security CI, Accessibility CI) and the
`dialogs.md` manual dialog regression checklist.

## 1. Purpose and scope

This plan defines the final, human-executed quality pass required before QUILL
1.0 ships. Its job is to verify, on a real Windows runtime with real assistive
technology, the behaviours that static analysis and headless unit tests
**cannot** prove: screen-reader announcements, focus journeys, audio output,
OCR against live images, the device-login network round trip, and the felt
quality of the writing experience.

In scope:

- Every user-facing dialog enumerated in `dialogs.md`.
- Keyboard operability and focus management across the whole shell.
- Screen-reader parity (NVDA, JAWS, Narrator) for announcements and navigation.
- The QUILL key, browse mode, and Quick Nav surfaces.
- File, session, and document lifecycle (open, edit, save, recover).
- AI / assistant tool flows, including consent gating and async "busy" states.
- OCR capture and review.
- Startup, onboarding, trust-consent, and crash-recovery paths.
- Read-aloud / speech output.
- Installer and first-run on a clean machine.
- Performance and stability under realistic documents.

Out of scope for 1.0 (deferred to 2.0, tracked in `ROADMAP.md`): axe-core / Nu
Html Checker validation, BITS Whisperer, the GLOW watch-action binding
(WATCH-8), and the Accessibility Agents workstream.

## 2. Test environments

Run the full pass on at least one machine from each row. Record the exact build
identifier (version + commit) on every result.

| Environment | OS | Screen reader | Notes |
| --- | --- | --- | --- |
| Primary | Windows 11 (latest) | NVDA (latest stable) | Baseline for every case |
| Secondary | Windows 11 (latest) | JAWS (latest) | Spot-check the high-traffic surfaces |
| Sanity | Windows 10 + Windows 11 | Narrator | Confirm no hard breakage |
| Clean-install | Fresh Windows VM, no Python | (NVDA) | Installer + first-run only |
| High contrast | Windows 11, High Contrast on | NVDA | Visual + announcement parity |

Build under test: record `version` from About Quill and the commit SHA. A pass
is only valid against a single, named build.

## 3. Entry and exit criteria

Entry criteria (all must hold before a final-QA pass begins):

- All required CI gates are green on `main`: PR CI, Security CI, Accessibility
  CI, GATE-6 (public surface), GATE-11 (module size), A11Y-4 (banned patterns
  and dialog registry), and the DLG-3 `dialog_inventory.json` snapshot.
- `dialogs.md` and the `dialog_inventory.json` snapshot agree with the source
  (run `python -m quill.tools.dialog_inventory` and confirm no diff).
- The build installs cleanly on the clean-install environment.

Exit criteria (all must hold to sign off 1.0):

- Every section below has a recorded result against the named build.
- Every `dialogs.md` row carries pass/fail evidence (see §5).
- No open Critical or High severity defect (see §11).
- Each known limitation is documented in the ACR/VPAT and release notes.

## 4. Severity model

| Severity | Definition | Release impact |
| --- | --- | --- |
| Critical | Data loss, crash, silent network egress, or a screen-reader user cannot complete a core task | Blocks release |
| High | A core task is severely degraded, or an announcement/focus contract is broken | Blocks release unless explicitly waived |
| Medium | A non-core task is degraded, or an announcement is imprecise | Fix or document before release |
| Low | Cosmetic, or a minor wording nit | Track for a follow-up |

## 5. Evidence capture

For every test case record: build id, environment row, screen reader + version,
pass/fail, and a one-line observation. For dialog cases, capture the exact
announced title and the announced text of the default and cancel actions. For
failures, capture: reproduction steps, expected vs actual announcement/focus,
severity, and a linked issue.

Store the completed evidence alongside this plan (a dated copy of the filled
`dialogs.md` plus a results sheet) so each release has a durable record.

## 6. Dialog estate pass (covers DLG-2, DLG-3.6, DLG-3.8)

The authoritative list is `dialogs.md` (sections A–X). Do not duplicate it here;
execute it directly. The contract every dialog must satisfy is the A11Y-4
contract restated at the top of `dialogs.md`:

1. It opens from the listed command or menu path.
2. Tab and Shift+Tab reach every control in a sensible order.
3. The screen reader announces the dialog title and each control.
4. Enter activates the default action; Escape and the close button cancel.
5. On close, focus returns to the editor.
6. The dialog never traps, freezes, or goes silent.

Screen-reader coverage matrix for the dialog estate:

| Surface group (`dialogs.md`) | NVDA | JAWS | Narrator |
| --- | --- | --- | --- |
| A. File / session | Full | Spot | Sanity |
| B. Settings, palette, menu editor | Full | Spot | Sanity |
| C. Navigate (Go To, Outline, bookmarks) | Full | — | Sanity |
| D–F. Text analysis, accessibility, intake | Full | — | Sanity |
| G. Read aloud + OCR (incl. OCR Review) | Full | Spot | Sanity |
| H. Sticky notes | Full | Spot | Sanity |
| I–P. Formats, compare, keyboard, macros | Full | — | Sanity |
| Q. AI and assistant (DLG-2 / DLG-3.6) | Full | Spot | Sanity |
| R. BITS Whisperer | Out of scope for 1.0 | — | — |
| S–T. Help, features, startup, support | Full | Spot | Sanity |
| U. Selection and QUILL key | Full | — | Sanity |
| V. Nested and secondary dialogs | Full | — | Sanity |
| W. Power Tools | Full | — | Sanity |
| X. Startup-only (crash recovery, trust) | Full | Spot | Sanity |

"Full" = exercise the complete A11Y-4 contract. "Spot" = open, confirm title +
default + Escape + focus return. "Sanity" = open and confirm it is not silent or
trapped. JAWS spot priority: startup, the assistant/AI tools, sticky notes, and
watch profiles (the surfaces with live lists, async work, and chained modals).

Special attention for the AI/assistant tools (Q) — the DLG-2 / DLG-3.6
acceptance the maintainer is signing off:

- Each long-running action disables its trigger before work starts and
  re-enables on completion.
- "Busy" state is announced; the surface never appears hung.
- Results marshalled back to the UI thread are announced once, not duplicated.
- A worker exception surfaces as an announced error, not a silent failure.
- No cloud/AI action runs without an explicit, per-action consent.

## 7. Keyboard and focus pass

- Tab order is sensible and complete on the main shell and every dialog.
- No keyboard trap anywhere; Escape always has a defined meaning.
- The QUILL key prefix (`Ctrl+Shift+Grave` by default) enters, announces, times
  out, and is remappable; the old default stops working after a remap.
- Browse mode enters, announces, navigates by element, and times out.
- Quick Nav / Heading Organizer / Outline Navigator move the caret and announce.
- Status-bar cells are reachable, announce their value, and expose their menu.
- Focus returns to the editor after every modal closes.

## 8. File, session, and document lifecycle

- Open, edit, save, Save As, and encoding selection round-trip correctly.
- Dirty-state title suffix appears and clears accurately.
- Prompt-to-save offers Save / Don't Save / Cancel and honours each.
- Multi-tab switch wraps correctly and is announced.
- Session save/open restores the working set.
- Atomic writes: a forced failure mid-save never corrupts the original file;
  `.bak` / recovery behaves per the data-layout contract.
- Restore Backup recovers a prior version.

## 9. AI, consent, and privacy pass

- No outbound document content without an explicit, visible, per-action consent.
- The consent surface states what will be sent and to where before sending.
- A declined consent cancels the action and announces the cancellation.
- API keys are stored via DPAPI; "Forget API Key" clears them and confirms.
- The device-login round trip (AI-19) completes against the live endpoint on a
  real network (cannot be verified headless).
- No document text appears in any log file after an AI action.

## 10. OCR pass (OCR-1, OCR-3)

Requires a live display, clipboard, and OCR engine, so it cannot be verified
headless.

- OCR Image, OCR Clipboard Image, and OCR Screen Capture each produce text.
- The screen-capture target chooser offers whole screen vs active window.
- OCR Review opens after completion, is fully keyboard/SR operable, and inserts
  the accepted text at the caret.
- A failed or empty OCR announces a clear outcome, not silence.

## 11. Startup, onboarding, and recovery pass

- First run shows onboarding; consent is recorded only on explicit accept.
- A declined trust-consent at startup closes the app rather than continuing.
- Each deferred startup step is isolated: a forced failure in one step logs to
  `logs/startup-errors.log` and keeps QUILL open.
- Crash Recovery appears after an unclean exit and restores or discards per the
  user's choice.
- The Untrusted Location Warning appears for files from untrusted folders.

## 12. Read-aloud and speech pass

- Read Aloud Voice Settings and Read Aloud Settings apply and persist.
- Generate Speech Audio produces a file and announces completion.
- Voice selection chain falls back gracefully when an engine is unavailable.

## 13. Installer and first-run pass (clean machine)

- The installer runs to completion on a fresh Windows VM with no Python.
- Single-instance behaviour holds (a second launch focuses the first).
- First launch reaches a usable editor with a screen reader running.
- Uninstall removes the app and leaves user data per the documented policy.

## 14. Performance and stability pass

- Open and edit a large document (target sizes per the PERF acceptance rows)
  without UI-thread stalls; cross-thread updates marshal through `wx.CallAfter`.
- Typing latency stays within the documented budget on the primary environment.
- No memory growth over a sustained editing session.
- The diagnostics bundle (Save Diagnostics) collects without document content.

## 15. High-contrast and visual pass

- High Contrast mode renders every surface legibly; nothing disappears.
- Focus indicators remain visible.
- Contrast validation tooling reports the shipped theme as compliant.

## 16. Localization sanity

- The shipped locales load; no layout breaks truncate a control's name.
- Announcements remain grammatical in each shipped locale.

## 17. Sign-off

Final sign-off is recorded by the maintainer against a single named build when
every section has evidence, `dialogs.md` is fully ticked for that build, and no
open Critical or High defect remains. This sign-off closes DLG-3.8 and, with it,
the deferred SR-verification criteria of DLG-2 and DLG-3.6.

| Role | Name | Build | Date | Result |
| --- | --- | --- | --- | --- |
| Maintainer (SR sign-off) | | | | |
