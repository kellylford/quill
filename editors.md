# Editors.md — Competitive Analysis and Design Synthesis for QUILL

> Author: this document. Date: 2026-06-01. Scope: a working competitive
> analysis of QUILL against leading general-purpose, programmer, and
> prose editors; a feature matrix; an honest gap analysis with industry
> expectations; a recommended menu consolidation; a Ulysses/Obsidian/Scrivener-
> inspired redesign of Workspaces and the Document Navigator that is
> unmistakably QUILL in spirit; and a long list of "make it amazing"
> proposals. Every recommendation is written for a screen-reader-first
> Windows desktop app whose north star is the QUILL key, Quick Nav, and
> the dialog contract.

---

## 1. Executive summary

QUILL is already a strikingly opinionated editor: stock controls in the
writing path, a screen-reader-first design, the QUILL key chord, Quick
Nav across 13 element types, a deep command palette, Workspace
Snapshots, headings organizer, compare documents, macros, an AI menu
gated by consent, GLOW accessibility, BITS Whisperer dictation, a rich
Quillins extension model, and a stability/safety surface that
mainstream editors rarely equal. Compared to the editor market it sits
somewhere between a programmer's text tool and a pro writing tool —
and that hybrid is exactly its edge.

The competitive analysis shows three things:

1. QUILL's *interactive navigation* and *accessibility-grade confirmations*
   are industry-leading. No mainstream editor matches its 13-element
   Quick Nav, its structured selection primitives, or its dialog
   contract enforcement.
2. QUILL's *document and project organization* (the Workspace concept,
   Document Navigator, multi-document sessions) is functional but
   under-developed compared with Ulysses's library, Obsidian's vault
   and backlinks index, Scrivener's index sheet, and Org-mode's
   hierarchy and agenda.
3. QUILL's *menu* has grown organically and now approaches the depth
   of a kitchen sink. The good news is the architecture supports a
   much cleaner organization. The bad news is that the current Tools
   menu reaches three levels in places and a few entries are mis-homed.

The rest of this document lays out the matrix, the gap list, the
proposed menu consolidation, the Workspaces + Document Navigator
redesign, and a long creative list of "make it amazing" ideas tailored
to QUILL's voice.

---

## 2. Feature matrix

Legend: ✅ first-class, ◑ partial, ○ not present, — N/A. The
"industry expectation" column is the user-facing behavior a sighted,
keyboard-only, or screen-reader user would expect to find without
explanation. The "QUILL today" column is observed from the codebase
and user guide as of 2026-06-01.

| Capability                                          | Industry expectation                                                                                          | QUILL today                              | Status |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------ |
| Undo / redo with persistence                        | Multi-level undo; survives crash                                                                              | Multi-level undo; persistent undo toggle | ✅     |
| Find / replace (text)                               | Modal find bar; next/prev; replace; selection scope                                                            | In-document Find bar, replace, next/prev | ✅     |
| Regex find / replace                                | Toggle for regex; group preview                                                                               | Regex supported; named-group preview planned | ◑ |
| Find in files                                       | Cross-file search with results list                                                                           | Search menu (search_in_files, replace_in_files) | ✅ |
| Bookmarks (named, persistent)                       | Set / go to / list; per-document                                                                              | `navigate.set_bookmark`, `go_to_bookmark`, `list_bookmarks` | ✅ |
| Temporary marks / "point and mark"                  | Push/pop ring; exchange point/mark; list marks                                                                | `edit.set_mark`, `pop_mark`, `exchange_point_mark`, `list_marks` | ✅ |
| Line / paragraph / block selection                  | Three distinct selection units; announce which                                                                 | `select_line`, `select_paragraph`, `select_block` | ✅ |
| Structural navigation                               | Next/prev heading, block, structure; match bracket; region                                                    | `navigate.next_heading`, `next_block`, `next_structure`, `match_bracket`, `next_region` | ✅ |
| Outline / structure panel                           | Dockable tree with preview and jump; per-markup-kind                                                           | `open_outline_navigator`, `_show_tree_navigator` (modal); also a YAML navigator | ◑ |
| Quick Nav (jump to anything)                        | Single keystroke to a categorised index with type-ahead                                                        | `open_quick_nav` (NAV-1/NAV-4) with 13 element types | ✅ |
| Command palette                                     | Fuzzy find over all commands with scope and recent                                                             | `_id_palette`, palette.py                 | ✅     |
| Project / "workspace" concept                       | Named, restorable collection of open documents, settings, and UI state                                          | "Workspace Snapshots" submenu in File (`_sessions_menu`) and `_refresh_sessions_menu`; `core/sessions.py` | ◑ |
| Multi-cursor / multi-selection                      | Multiple carets, column selection, box select                                                                 | Not in core; `extend_selection_mode` toggle | ○ |
| Snippets / text expansion                           | Trigger, tab stops, placeholders, scope                                                                        | `core/snippets.py` (11 KB), `format.insert_snippet`, `format.manage_snippets` | ✅ |
| Snippet variables (date, filename, cursor)          | Tokens at expansion time                                                                                      | Supported (see Snippet format)           | ✅     |
| Command-based snippet system                        | JScript / Lua / Python actions inside snippets                                                                | Python sandbox in core; no in-snippet scripting in user guide | ◑ |
| Spell check                                         | As-you-type; dialog; dictionary management                                                                    | Three-tier spell-check; status / dialog; dictionary status | ✅ |
| Thesaurus                                           | Synonym lookup, inline replace                                                                                | `tools.thesaurus` (background pre-load planned) | ◑ |
| Grammar / style lint                                | Rules engine, inline annotations                                                                              | GLOW audit + fix, selection-level       | ✅     |
| Word count / reading time                           | Document, selection, periodic                                                                                 | `tools.word_count`                       | ✅     |
| Auto-save / recovery                                | Periodic save; recovery on crash with preview                                                                  | `core/autosave.py`; recovery snapshot dialog with 30-line preview | ✅ |
| Backups                                                                     | Local copies of prior versions                                                                                | `core/backups.py`; restore from backup   | ✅     |
| Compare documents                                                              | Side-by-side or unified diff; navigate; announce                                                              | `compare_menu` (Compare Documents) with announce, summary, copy, sync toggle | ✅ |
| Macros                                                                       | Record / play / save; named                                                                                   | `core/macros`; macro menu with start/stop/play/manage | ✅ |
| TTS / read aloud                                                             | Start/pause/stop; voice pick; speed; export audio                                                              | `core/read_aloud.py` (~46 KB), full menu | ✅ |
| Dictation                                                                    | Toggle; voice commands; offline model                                                                          | BITS Whisperer (deferred to 2.0 as a top-level menu; 1.0 ships dictation under Watch/Dictation submenu) | ◑ |
| OCR                                                                          | Image, clipboard, screen; image description                                                                     | `tools.ocr_image`, `tools.ocr_clipboard`, `tools.ocr_screen`, `tools.describe_image` | ✅ |
| OCR result post-processing (cleanup recipes)                                 | One-key cleanup of OCR output                                                                                  | "Clean exports" profile mentioned in roadmap; not surfaced in menu | ◑ |
| On-device / private AI                                                       | Opt-in; explicit consent; no silent network                                                                     | AI menu gated; `core.bw_whisperer` provider model; consent flow | ✅ |
| Cloud AI (ChatGPT, Claude, local endpoints)                                 | Model picker; API key; forget key                                                                              | `AI Model and Connection...`; `Forget API Key`; status badge | ✅ |
| AI rewrite / summarize / continue / fix grammar                              | In-editor actions                                                                                              | `ai_rewrite_selection`, `ai_summarize_selection`, `ai_continue_writing`, `ai_fix_grammar` | ✅ |
| AI prompt studio / agent center                                              | Custom prompts; agent tools                                                                                    | `ai_prompt_studio`, `ai_agent_center`, `ai_hub` | ✅ |
| Conversational AI side panel                                                 | Chat persistent side region, share selection                                                                       | `ask_quill_chat`, `ai_assistant` (windowed) | ◑ |
| Image description / alt-text helper                                          | Generate alt-text for embedded images                                                                          | `tools.describe_image`; accessibility tune-up agent | ✅ |
| Accessibility audit                                                          | Periodic; spoken report                                                                                        | `tools.accessibility_audit`              | ✅     |
| Keyboard trap / tab-order snapshot                                           | Diagnose focus traps                                                                                            | `tools.keyboard_trap_snapshot`           | ✅     |
| Contrast validation                                                          | Check palette against WCAG                                                                                     | `tools.validate_contrast`                | ✅     |
| Sticky notes                                                                  | Quick capture; searchable vault                                                                                | Sticky Notes submenu (sticky_notes, new sticky note) | ✅ |
| Watch folder                                                                  | Many folders, many actions, one monitorable queue                                                                | Watch Service (`quill.core.watch_service.WatchService`) with `WatchProfileStore` + `WatchManager` + `WatchQueue`; "Watch Folder Profiles..." / "Watch Folder Queue..." / toggle; CRUD on each profile | ◑ |
| Pandoc integration                                                            | Convert between formats                                                                                         | `tools.pandoc_wizard`                    | ✅     |
| External tools / format support                                              | Allowlist of executables                                                                                        | `tools.external_tools`                   | ✅     |
| SSH / remote file open                                                        | Quick connect; site manager                                                                                    | `Open over SSH` submenu (Quick Connect, Site Manager) | ✅ |
| File format readers/writers                                                   | Markdown, HTML, RTF, EPUB, DOCX, PDF, JSON, CSV, YAML, plain text                                             | `quill/io/structured.py` and per-format modules | ✅ |
| EPUB reader / navigator                                                       | Open and jump inside EPUB                                                                                       | `open_epub_navigator`                    | ✅     |
| YAML structure editor                                                         | Visual tree edit for YAML documents                                                                            | `open_yaml_structure_editor`             | ✅     |
| Heading organizer                                                             | Validate and reshape heading sequence                                                                          | `open_heading_organizer`                 | ✅     |
| Customizable menus / keymap                                                   | Editor for menu and keymap                                                                                     | `app.menu_editor`, `keymap_editor`; `core/menu_customization.py` (12 KB) | ✅ |
| Profiles (Essential, Writer, Developer, A11y Pro, Full)                      | Switch whole profile; health check                                                                              | Feature profiles + `switch_feature_profile`; `feature_profile_health_check` | ✅ |
| Feature flag manager                                                          | Per-feature toggle                                                                                              | `individual_feature_toggles`             | ✅     |
| Custom profiles / Quick Profiles                                              | User-saved bundles of settings                                                                                  | `core/custom_profiles.py`                | ✅     |
| Status bar layout customization                                               | Pick cells, persist                                                                                            | `status_bar_settings`                    | ✅     |
| Plug-in / extension model                                                     | Manifest, sandbox, signing                                                                                     | Quillins manifest validated; `quillins_bundled/` examples | ◑ |
| Export and back up / import                                                   | One-key share                                                                                                   | `share_export`, `share_import`           | ✅     |
| Export presets (EPUB, PDF, DOCX, HTML)                                        | Pick target and options                                                                                         | Pandoc wizard; export presets partial    | ◑ |
| Print                                                                          | Page setup, print preview                                                                                      | `file.page_setup`, `file.print`          | ✅     |
| Auto-format / smart punctuation                                              | Smart quotes, dashes, ellipses                                                                                  | Core autoformat; smart quotes not surfaced as toggle | ◑ |
| Word prediction                                                                | Inline completion                                                                                              | `edit.word_prediction`                   | ✅     |
| Intellisense as you type                                                       | Lightweight, scoped to language                                                                                | `core/intellisense.py`                   | ◑ |
| Markdown / HTML / rich-text preview                                           | Side by side or focused                                                                                        | `view.preview`, `view.split_preview`, `view.focus_preview`, `view.browser_preview` | ✅ |
| Distraction / focus mode                                                      | Hide chrome, center text, silence chatter                                                                       | "Focus Preview" is the closest; no full-screen "Focal" mode | ◑ |
| Reading ruler / line focus                                                    | Highlight current line/paragraph                                                                                | Not surfaced; high-contrast settings only | ◑ |
| Inline definitions / word lookup                                              | Single key for dictionary + thesaurus                                                                            | Thesaurus dialog; no inline look-up      | ◑ |
| Document health unified report                                                | One pane for accessibility + lint + link inventory                                                              | Accessibility audit; link inventory; contrast; not unified | ◑ |
| External file change watch                                                    | Detect edits; reload safely                                                                                    | `core/external_change.py`                | ✅     |
| Code folding                                                                  | Collapse / expand                                                                                              | Not surfaced                              | ○     |
| Multi-pane editor (split, grid)                                              | Horizontal/vertical split, save layout                                                                          | "Preview Side by Side" exists; no true multi-pane text editor split | ◑ |
| Tab / tile open documents                                                     | One tab per document                                                                                            | `show_tab_control` toggle in View        | ✅     |
| Status bar: line, col, selection length                                      | Always present                                                                                                  | Status bar with cells (status_bar_settings to choose) | ✅ |
| Recent files / recent folders                                                 | MRU list                                                                                                        | `Open Recent` submenu                    | ✅     |
| Recent sessions / restore last session                                        | Auto-restore on launch                                                                                          | "Workspace Snapshots" submenu in File; auto-restore on launch | ✅ |
| Auto-update                                                                    | Notify; one-key update                                                                                          | `check_updates`; auto-check toggle in Settings | ✅ |
| Crash reporting                                                                | Opt-in bundle                                                                                                  | `save_diagnostics`; `report_bug`        | ✅     |
| Localization                                                                   | Multi-language UI                                                                                              | Translation contributor plan in place    | ◑     |
| High-contrast / dark mode                                                     | System-aware                                                                                                    | `toggle_dark_mode`; `validate_contrast`; high-contrast respected | ✅ |
| Math / equation editor                                                        | LaTeX-style inline and block                                                                                    | Not surfaced                              | ○     |
| Bibliographies / citations                                                    | Reference list management                                                                                       | Not surfaced                              | ○     |
| Co-located todos / checkboxes                                                 | Task list with states                                                                                          | Task list insertion (`insert_task_list`); List Manager | ✅ |
| Bidirectional links / backlinks                                               | Wiki-style [[link]] with back-link pane                                                                          | Follow link exists; no backlink pane    | ○     |
| Backlinks / relational index                                                   | Cross-document links and references                                                                              | Not in QUILL (deferred to 2.0)            | ○     |
| Index-sheet view                                                               | One card per document or section                                                                                | Not in QUILL                              | ○     |
| Outline view (persistent side region)                                          | Persistent tree side panel                                                                                      | Outline Navigator is a modal; no persistent side region | ◑ |

The takeaway: QUILL is in the top tier for navigation, accessibility,
AI integration (gated), writing-quality tooling, and document safety.
Its *project organization* layer (workspaces, library, multi-document
backlinks, smart folders, goals) is functional but under-developed
relative to dedicated writing apps.

---

## 3. Where QUILL aligns with industry

These are the strengths that match or exceed editor expectations, and
the rough proof points inside the codebase.

1. **Stock controls in the writing path.** Per
   `accessible-dialogs.instructions.md`, every input is `wx.TextCtrl` or
   `wx.ListBox`. No custom-drawn editor surface, which means
   screen readers see the same role and name everywhere.
2. **Three-tier spell check** with enchant, wordlist, and stub. Background
   pre-load is on the roadmap (PERF-1) and the menu surfaces every
   level: Spell Check dialog, Previous/Next Misspelling, Misspelling
   List, Dictionary Status, Add to Document Dictionary, Ignore for
   Session.
3. **Structured selection primitives.** Select Line / Paragraph / Block
   are separate commands, not a single ambiguous "extend selection"
   that other editors make the user discover.
4. **Mark ring.** Set / Pop / Exchange / List. Few mainstream editors
   ship a visible mark ring as a first-class menu.
5. **Quick Nav across 13 element types** with a category filter and
   type-ahead. This is VS Code's Command Palette behavior applied to
   document structure, with a count badge.
6. **Heading organizer** validates and rewrites heading sequences for
   accessibility and clean exports. No mainstream editor has this.
7. **Compare Documents** with synchronized navigation, announcement of
   the current difference, a "Difference Summary," and copy
   individual/all differences. Compare in Word is a hidden ribbon
   dialog; in Notepad++ it is a plugin; in VS Code it is an extension
   unless you have Pro. QUILL ships it as a first-class tool.
8. **Workspace Snapshots** that name and restore document sets, caret
   positions, and active document. The naming and saving model is
   Ulysses-like.
9. **Two-stage AI consent.** No silent network; provider, model, scope,
   and confidence are announced.
10. **BITS Whisperer** (deferred to 2.0 as a top-level menu but present
    in 1.0 as a submenu) is genuinely novel for a screen-reader-first
    editor: offline speech-to-text with model management and a queue
    you can monitor without sight.
11. **Watch Folder Profiles** is the rare automation hub that is
    operable with a screen reader; the "many folders, many actions,
    one queue" redesign on the roadmap is a real differentiator.
12. **GLOW (Grammar, Logic, Organization, Writing)** is QUILL's
    accessibility-and-prose-fix engine; the four sub-commands (audit
    document, audit selection, fix document, fix selection) make it
    simple by design.
13. **Quillins extension model** is sandboxed, manifest-validated, and
    ships with a Lint tool (`quill.tools.quillin_lint`). Compared with
    Vimscript or VS Code's open extension marketplace, it is a
    deliberately tight perimeter.

The user-visible principle behind all of this: *every action has a
spoken outcome, every dialog has a default and an escape, every
feature can be turned off*. That is the bar the rest of the editor
market does not consistently meet.

---

## 4. Where QUILL is behind or behaves unexpectedly

These are the gaps the matrix surfaces, with the "industry expects"
framing, the QUILL reality, and an honest callout when current
behavior diverges from what a user would assume.

### 4.1 Project organization is shallow

- **Industry expectation.** Ulysses users live in a "library" with
  groups, filters, and goals. Obsidian users live in a "vault" with
  backlinks, tags, and Bases. Scrivener users live in a "binder" with
  index sheet and outliner. Org-mode users live in a tree with
  agenda.
- **QUILL today.** Workspace Snapshots save and restore the current
  open-document set. There is no persistent library, no grouping, no
  filters, no per-workspace palette of recent activity. The
  "Recent Files" menu exists but Workspace Snapshots is a sibling
  concept, not a superset.
- **Honest callout.** "Open from Workspace Snapshot" can look like a
  glorified "Reopen Closed Tab" to a new user. The snapshot is
  loadable, but the snapshot UI is not yet a library.

### 4.2 Outline Navigator is a modal, not a persistent side region

- **Industry expectation.** Word, Scrivener, and most writing apps
  ship a persistent outline pane that you can show, hide, and let
  track the cursor. Ulysses shows the editor + sheet list always.
  Obsidian shows the file tree.
- **QUILL today.** `_show_tree_navigator` builds a `wx.Dialog` with a
  splitter (tree + preview), is launched by `open_outline_navigator`
  (and `open_epub_navigator`, `open_yaml_structure_editor`), and is
  destroyed on close. The same pattern is reused for Misspelling
  Navigator, Document Intake, and others.
- **Honest callout.** The dialog is excellent and screen-reader
  friendly, but a power user editing a 200-page manuscript will
  repeatedly open and close the modal. A persistent outline panel
  (toggle from View) would match industry behavior without
  breaking the dialog contract.

### 4.3 Multi-cursor / column select is absent

- **Industry expectation.** VS Code, Sublime, JetBrains IDEs, vim,
  Emacs all support multiple carets. Notepad++ supports column /
  block selection. Word supports column select with Alt.
- **QUILL today.** Only an "extend selection mode" toggle exists,
  which extends the next selection motion. No multi-caret, no
  column / box select.
- **Honest callout.** This is the single largest missing editing
  primitive for users who came from a programmer editor. Add a
  power-tool that toggles column-select on Alt+drag and a
  keyboard command to add a caret above / below.

### 4.4 Word-prediction and intellisense are present but not visible

- **Industry expectation.** Word shows suggestions inline. VS Code
  shows completions on demand and as you type. Notepad++ has an
  autocomplete plugin that does the same.
- **QUILL today.** `edit.word_prediction` opens a dialog. There is no
  as-you-type inline completion surfaced in the menu or the status
  bar. `core/intellisense.py` exists; nothing in the menu says so.
- **Honest callout.** Users will assume the feature is broken. The
  fix is to make it a visible, opt-in "Inline word prediction" toggle
  in the status bar / settings, with announcement on accept.

### 4.5 AI chat is windowed, not a persistent side region

- **Industry expectation.** Cursor, VS Code + Copilot, JetBrains AI,
  Notion AI, and Ulysses's "Ask Ulysses" all anchor a chat side
  panel that shares selection with the editor.
- **QUILL today.** "Ask Quill Chat..." and "Writing Assistant..."
  open floating windows. The selection is shared only through copy
  and paste.
- **Honest callout.** The chat is functional; it just is not a
  persistent side region, and a chat panel that owns a left or right
  persistent side region with the outline tree on the other side
  would be a much more useful default.

### 4.6 Grammar fix is not in the document until asked

- **Industry expectation.** Grammarly underlines; one key accepts.
  GLOW already audits and fixes, but the audit step is explicit.
- **QUILL today.** `glow_audit_document` and `glow_audit_selection`
  must run before `glow_fix_document` and `glow_fix_selection`. The
  fix only changes the document after the user sees the report.
- **Honest callout.** This is a defensible design (transparency), but
  the menu should make it obvious: the "GLOW" submenu already does.
  Keep the contract; add a "GLOW Quick Fix on Selection" that audits
  + fixes + announces the change count in one key.

### 4.7 No "Focus Mode" / "Focal" surface

- **Industry expectation.** Word has Focus Mode. Bear has a
  chrome-less compose. Ulysses has a minimal editor. iA Writer has
  Focus Mode with a sentence highlight. Notepad++ has a "Distraction
  Free" plugin.
- **QUILL today.** The closest is "Focus Preview." That hides the
  editor chrome for the preview, not the editor itself.
- **Honest callout.** "Focus Preview" is misleadingly named. A real
  "Focal Mode" (F11?) that hides status bar, menu bar, side
  region, and centers the current paragraph with optional reading
  ruler and sentence highlighting is the correct fit for a
  screen-reader product; it should silence non-essential chatter,
  keep essential confirmations, and be a one-key toggle.

### 4.8 Snippet tab stops / placeholders are not announced

- **Industry expectation.** VS Code, Sublime, JetBrains, vim, and
  TextMate all support tab stops with placeholders; the user is
  walked through each stop with `Tab` and `Shift+Tab`.
- **QUILL today.** Snippets exist and the menu offers Insert and
  Manage; there is no documented "tab stop" walk-through. The snippet
  format may support placeholders (it does in EdSharp and most modern
  editors).
- **Honest callout.** Verify in `core/snippets.py` and document.
  If placeholders are not yet announced, add a `Snippets` tutorial
  to the user guide and make the placeholder name spoken on arrival.

### 4.9 Goto line / page has no "line" speech preview

- **Industry expectation.** A "Go to line" usually shows the line
  content in a preview before the user commits.
- **QUILL today.** `navigate.go_to_line` jumps; no preview.
- **Honest callout.** Add a one-line preview pane in the Go-To-Line
  dialog with the current line's text, the line number, the column,
  and a "Speak Line" button. Trivial to add, big screen-reader win.

### 4.10 No saved searches / no smart folders

- **Industry expectation.** Most pro editors and writing apps
  support saved filters: "All headings containing TODO," "All
  documents opened this week," "All files with more than N
  misspellings."
- **QUILL today.** None. `file_search` exists but is a one-shot
  search.
- **Honest callout.** Add a "Saved Searches" manager and tie it to
  Workspace Snapshots. Saved searches are an under-rated
  accessibility win because they let a screen-reader user ask
  "what's new?" in a single keystroke.

### 4.11 No word-count goal / writing target

- **Industry expectation.** Ulysses has writing goals (words,
  characters, time). Scrivener has project targets. Word has
  word-count target notifications. Bear has a daily streak.
- **QUILL today.** Word count exists; no goal / target surface.
- **Honest callout.** Add a "Writing Goal" dialog and a status-bar
  cell that announces progress. Tying the goal to a Workspace
  Snapshot makes this very Ulysses-like.

### 4.12 Status bar cells are customizable but the UX is hidden

- **Industry expectation.** VS Code and Word expose a clear "Status
  Bar Layout..." picker.
- **QUILL today.** `status_bar_settings` exists. The menu labels it
  clearly. The dialog must be polished.
- **Honest callout.** Verify the dialog (a screen-reader test pass)
  and add an "Add a cell" / "Remove a cell" / "Reorder" flow that
  is fully keyboard-driven.

### 4.13 No reading ruler / line focus for low-vision users

- **Industry expectation.** Word, Pages, macOS, NVDA, and many
  editors support a reading ruler that follows the caret.
- **QUILL today.** Not surfaced.
- **Honest callout.** Add a "Reading Ruler" toggle and a "Line
  Focus" toggle under View, behind a feature flag, with high-contrast
  aware theming.

### 4.14 Smart quotes / auto-format not surfaced

- **Industry expectation.** Word, Pages, Ulysses, Bear all convert
  straight quotes to typographic quotes as you type.
- **QUILL today.** `core/autoformat.py` exists; not on by default,
  not visible in the menu.
- **Honest callout.** Surface as a setting ("Auto-format as you
  type") with sub-toggles for quotes, dashes, ellipses. Announce the
  substitution so a screen-reader user knows the character changed.

### 4.15 No image embed flow (other than OCR)

- **Industry expectation.** Markdown editors let you paste / drop an
  image. Ulysses, Bear, iA Writer all do.
- **QUILL today.** OCR Image and Describe Image are present. Image
  insertion is not. Markdown reference links work.
- **Honest callout.** Add "Insert Image from File..." and "Insert
  Image from Clipboard" under Insert. The accessibility win is that
  the dialog should immediately offer a "Describe Image..." button
  that uses Describe Image, so the alt text and the embed happen
  together.

### 4.16 Inline spelling suggestions are not visible in the menu

- **Industry expectation.** Word, Pages, macOS show a context menu
  with "Replace with..." suggestions.
- **QUILL today.** Misspelling List exists; no inline context menu
  for replacements.
- **Honest callout.** Add a context menu for misspelled words
  offering the top three suggestions + "Add to Dictionary" + "Ignore
  for Session." Already possible with the wx context menu; surface
  the wired action in the menu so it is discoverable.

### 4.17 No "duplicate selection" as a structural copy

- **Industry expectation.** Several editors have "Duplicate Line"
  and "Duplicate Selection."
- **QUILL today.** `format.duplicate_line` exists. No
  `duplicate_selection` (block-level copy).
- **Honest callout.** Add `edit.duplicate_selection` to the Edit
  menu; it's two lines of code and a big productivity win.

### 4.18 The Tools menu is deep

- **Industry expectation.** Most successful editors keep top-level
  menus flat with one level of submenu. VS Code's File menu has 9
  items, Edit has 12, View has 22, all flat.
- **QUILL today.** The Tools menu has 14 direct submenus and the
  Read Aloud, BITS Whisperer, and AI submenus each go a level
  deeper. The Custom Profiles under Help also add a third level.
- **Honest callout.** This is a documentation and discoverability
  problem, not a code problem. See §6 for the proposed
  consolidation.

### 4.19 Watch Folder — multi-profile infrastructure is in, the screen-reader UX is the gap

- **Industry expectation.** Folder Watching tools (Hazel on Mac,
  File Juggler on Windows) all support many rules. A
  screen-reader-first editor needs the same, with every rule,
  match, and action spoken on the same channel as the rest of the
  editor.
- **QUILL today.** The infrastructure is genuinely in. The
  `WatchService` facade (`quill/core/watch_service.py`) owns:
  - a `WatchProfileStore` with full CRUD —
    `add_profile`, `update_profile`, `delete_profile`,
    `set_profile_enabled`, `duplicate_profile`, `profiles()`;
  - a `WatchManager` that runs pollers for *all* enabled profiles
    concurrently, with a single `WatchQueue`;
  - a `WatchWorker` plus the durable queue at
    `%APPDATA%\Quill\watch\watch-queue.json`;
  - a `WatchActionRegistry` (open / convert / run macro / AI)
    wired through the UI layer's callbacks.
  The Tools menu exposes "Watch Folder &Profiles...",
  "Watch Folder &Queue...", and the toggle.
- **Honest callout.** The plumbing matches Hazel / File Juggler in
  scope, not "single profile." The real gap is the
  screen-reader-tuned UX: a stock `wx.Dialog` for add / edit /
  enable / disable that announces every field; a queue dialog that
  announces profile, file, action, and result with a spoken tail
  on completion; a one-key "Open Watch Queue"; an opt-in
  "announce on match" toggle in Preferences. The settings dialog
  currently lives in the main frame and likely needs the
  dialog-inventory treatment before it can honestly be called
  "aligned with industry."

### 4.20 BITS Whisperer (offline speech-to-text) is deferred

- **Industry expectation.** Dragon, Apple Dictation, Windows Voice
  Typing all exist.
- **QUILL today.** Dictation is a submenu, BITS Whisperer is feature-
  flagged behind `core.bw_whisperer` (off by default in 1.0), and
  per the standing rules, items needing a real Windows runtime must
  stay honestly "In progress."
- **Honest callout.** This is correctly called out in the standing
  rules; keep it in progress and don't pretend it's done.

### 4.21 Selection mechanics — what the code already does, what it doesn't

The selection pipeline lives in three files
(`quill/core/selection.py`, `quill/core/marks.py`,
`quill/ui/main_frame_selection.py`) and is genuinely well-factored
for a screen-reader product. The screen-reader contract — *announce
the scope, the word count, and the new bounds after every change* —
is held by `_announce_selection_scope` in the mixin.

| Mechanism                            | QUILL today                                                                                                                                  | Industry comparison                                                            |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Word / line / paragraph / block span | Five primitive span functions (`word_span`, `line_span`, `paragraph_span`, `sentence_span`, `block_span`) return `(start, end)` for a caret | Emacs has `mark-word` / `mark-paragraph`; Word has Extend Mode; vim has `vw`     |
| Scope classification                 | `selection_scope` returns one of `none / word / line / sentence / paragraph / block / document / lines / span`                                | Sublime/VS Code announce "1 selection, 4 words"; QUILL is more granular       |
| Expand / shrink                      | `expand_selection` walks word → line → sentence → paragraph → block → document with a stack; `shrink_selection` pops the stack                | VS Code's Expand / Shrink Selection; IntelliJ "Extend Selection"               |
| Extend selection mode                | `edit.toggle_extend_selection_mode` (F8) flips a sticky flag; while on, shift+arrow extends from the current caret; toggle off to leave | Emacs transient-mark; vim visual-mode; *different* from EdSharp's F8 (single-shot session, see §4.21.1) |
| Mark ring                            | `MarkRing` (20 entries, dedup, exchange) with `set_mark` / `pop_mark` / `exchange_point_and_mark` / `list_marks`                            | Emacs' global-mark-ring; EdSharp's mark ring; Scrivener's bookmark ring         |
| Select-to commands                   | `select_to_start_of_line`, `select_to_end_of_line`, `select_to_start_of_document`, `select_to_end_of_document`                              | Standard; UX is the announcement                                               |
| QUILL key selection actions          | `quill_key_selection_actions` opens a stock `wx.SingleChoiceDialog` whose options adapt to scope + markup surface                              | Ulysses's "Quick Action" panel; VS Code's "Refactor This..." — QUILL is better |

#### 4.21.1 EdSharp's F8 vs. QUILL's F8 — the two dialects of "begin a selection"

Both editors let you mark a region of text so you can copy, cut,
reformat, or read it aloud, but they model the *act of marking*
quite differently. This is the single most important
selection-UX comparison for a screen-reader-first editor, and the
audit recommendation is to **speak both dialects** rather than
pick one.

**EdSharp's F8 is a "begin / end" event pair, not a mode.**

- **Press F8 once** → "Start Selection." EdSharp drops an invisible
  anchor exactly where the caret sits and remembers the caret
  position as the *start* of a future selection. The status bar /
  screen reader announces something like *"Selection started at
  line 12, column 5."* The cursor can now move around freely
  (arrows, mouse, click, search) without selecting anything yet.
  This is *not* a sticky mode — it is the first half of a two-step
  operation.
- **Move the caret** anywhere (including via search results,
  go-to-line, etc.) — nothing is highlighted as you go. The anchor
  stays put at the original spot.
- **Press Shift+F8** → "Complete Selection." EdSharp now draws and
  announces the rectangular region from the anchor to wherever the
  caret has moved to, and that region is the "active selection."
  From this point on, Copy, Cut, Say Selected, Quote, etc. operate
  on it.
- **Press F8 again on an existing selection** → "Reselect"
  (Ctrl+Shift+F8) or "Go to Start of Selection" (Alt+Shift+F8) to
  refine.

So the EdSharp flow is **Anchor → Roam → Capture**: anchor once,
wander anywhere, capture the region at the moment you choose.
There is no state to remember to turn off; F8 / Shift+F8 are an
*event pair*, not a toggle.

**QUILL's F8 is a sticky mode flag.**

- `edit.toggle_extend_selection_mode` (F8) is a *toggle*: pressing
  F8 turns the flag on, pressing F8 again turns it off. The flag
  lives in `self._extend_selection_mode` and the anchor lives in
  `self._extend_selection_anchor` on `MainFrame` (see
  `quill/ui/main_frame.py:945` and the branches that consult the
  flag at 3074, 3530, 3535, 3593, 3601, 11741, 11758, 11774,
  16296, 16309).
- When the flag is **on**, the *next* shift+arrow / shift+click /
  shift+End / shift+Home / etc. extends the selection from the
  current caret — there is no separate "begin" step. The flag
  stays on across many motions; it stays on across copy / cut
  (those don't touch the flag); it stays on until you press F8
  again, press Escape (a dedicated Escape branch at 3074 and 3530
  turns it off), or do something like a click without shift
  (treated as an implicit off-switch).
- When the flag is **off**, shift+arrow behaves the *normal* wx
  way — a one-character shift-select that disappears as soon as
  you release shift.

So the QUILL flow is **Enable → Shift-move → Disable**: a mode
you have to remember to leave on, with the bonus that *every*
shift+motion honors it (e.g. shift+Ctrl+End extends to end of
document), and the cost that the SR user has to remember the
flag is still set when they think they are doing a normal
selection.

**The QUILL flow has real ergonomic issues that the prose above
understates.** Reading the actual code
(`quill/ui/main_frame.py:3530–3558`, `_move_extend_selection_caret`
at 3621–3701, and the commit helpers at 3592–3619), the
"F8 + arrows + copy" gesture does *not* behave the way the
summary sentence above suggests:

1. **F8 does not capture the anchor.** The first keypress of F8
   only flips the flag. The anchor is set *lazily* on the first
   movement-key event (line 3552–3553) or on the first
   non-excluded action (e.g. find, line 16295 calls
   `_ensure_extend_selection_anchor`). So if you press F8 and
   then *do nothing* for ten seconds, the editor has a flag set
   and no anchor.
2. **The anchor is set to the *pre-motion* caret, not the *F8
   time* caret.** In practice these are the same — you pressed
   F8, you didn't move — but the contract is "the anchor is
   wherever the caret is on the first move." If you press F8,
   click the mouse somewhere, then arrow down, the anchor is the
   *click* position, not the F8 position.
3. **During the arrow-down phase, the selection is *invisible*.**
   `_handle_extend_selection_key` (3530–3558) moves the caret via
   `_move_extend_selection_caret`, then at 3556 explicitly
   collapses the selection to `(caret, caret)`. The SR hears
   *only* caret-move announcements ("line 14, column 5… line 15,
   column 5…") with no "selected" prefix. A sighted user sees
   the highlight stretch; a blind user gets no audio equivalent
   of the growing region.
4. **The selection is only *applied* to the editor at the moment
   a "commit" key fires.** Copy, Cut, Delete, Format commands,
   and tools.glow_fix_selection are in the commit set
   (`_EXTEND_SELECTION_ACTION_COMMANDS` at 864, with the prefix
   test at 860–863). The commit runs `_apply_extend_selection`
   (3592–3598), which finally does
   `SetSelection(min(anchor, caret), max(anchor, caret))`. Until
   then, the editor's selection range is `None..None`.
5. **If you stop without committing, the work is lost.** Pressing
   F8 a second time hits the Escape-style branch at 3530–3534
   and discards the anchor with `SetSelection(caret, caret)`. So
   "F8, arrow 6, F8 to stop" leaves *no* selection — and the
   arrow key announcements in step 3 made it *sound* like the
   region was being built. A blind user has no way to recover
   the anchor.
6. **Ctrl+C works only by accident of the Skip order.** At
   3548–3551, the handler calls `_commit_pending_extend_selection`
   *before* `event.Skip()`. wx's native Ctrl+C then reads
   `GetSelection()` after the commit, so the clipboard gets the
   correct region. But this depends on the key handler running
   *before* wx's copy, and on the user pressing a key that is
   recognized as a "commit" key. Hit Escape and the region is
   gone (step 5).
7. **Mouse-based extend is half-supported.** A bare click is
   treated as an implicit off-switch, so click-move-shift-click
   does not benefit from the F8 flag. Shift+click works as a
   normal wx shift-select. There is no "F8 then click" anchor
   placement.

**Net effect.** A power user with eyes on the screen gets a
selection that grows visibly and copies correctly. A screen-reader
user gets *no* spoken evidence of the growing region, no spoken
announcement of the final anchor, no announced bounds at copy
time, and a high risk of losing the work entirely if they hit
F8 again or Escape by reflex. The mode toggle is genuinely a
power-user feature for sighted code editing; for a screen-reader-
first product the **recommended default is the EdSharp event-pair
model**, with the F8 mode preserved as an opt-in profile.

#### 4.21.2 Should we change F8 to match the EdSharp model? — recommendation

Short answer: **no, do not change F8. Add three new commands and
let the user choose.** Here is the reasoning, broken into the
parts that are easy to get wrong.

**Why "just change F8" is the wrong move for 1.0**

1. **It would break every existing muscle-memory user.** F8 is in
   `quill/core/keymap.py:52` as a default binding, in the Edit
   menu check item at `quill/ui/main_frame_menu.py:138–144` and
   1748–1750, in the feature-command map at
   `quill/core/feature_command_map.py:150`, and in the public
   surface fixture at
   `tests/unit/ui/fixtures/main_frame_public_surface.json:213`.
   The "extend mode" semantics are tested in five places in
   `tests/unit/ui/test_main_frame_navigation.py` (1275, 1303,
   1316, 1330, 1690, 1704, 1715). A semantics change would force
   a keymap migration, a menu relabel, a feature-flag rename, a
   public-surface fixture regen, and a regression pass on those
   seven tests. None of that is a 1.0 win.
2. **The mode is *correctly* used as a power-user feature.** The
   toggle composes with every shift+motion and shift+command.
   F8 → shift+Ctrl+End selects to end of document in one gesture;
   F8 → find_next → find_next captures a "search hits" region;
   F8 → select_line then re-pressing F8 toggles the line into a
   region. None of that is in EdSharp's event-pair model without
   extra keypresses.
3. **The bugs are bugs, not design flaws.** The screen-reader pain
   is real, but it is caused by *missing announcements* and
   *missing commit visibility*, not by the mode itself. The
   right fix is to add the announcements (one line per
   handler in `_handle_extend_selection_key`, one PR), not to
   delete the mode.

**Why EdSharp-style commands are the right *addition***

1. **They fill the actual gap.** A screen-reader user who presses
   F8 today gets "Extend selection mode on (F8)" — they don't
   get the line / column. They press the down arrow six times
   and get six caret announcements with no growing region. They
   press Ctrl+C and the clipboard has the right text but no
   audio confirmation. None of that is fixed by changing the F8
   semantics; all of it is fixed by adding commands that
   announce.
2. **They cost very little.** The implementation surface for the
   event-pair model in QUILL is roughly:
   - `edit.start_selection` — sets an explicit anchor at the
     caret, announces "Selection started at line N, column M,"
     and stores the anchor in a new field
     `self._selection_anchor: int | None`. Toggle behavior on
     the same key (Ctrl+.) so re-pressing just refreshes the
     anchor.
   - `edit.complete_selection` — collapses the anchor and the
     current caret into a region via
     `editor.SetSelection(min, max)`, announces "Selected N
     words from line A col B to line C col D," and clears the
     anchor.
   - `edit.reselect` — re-applies the last applied region
     (cheap if `core/selection.py` already tracks the last
     applied pair).
   - `edit.go_to_start_of_selection` / `edit.go_to_end_of_selection`
     — move the caret to one end or the other, leaving the
     selection visible.

   The first two are ~40 lines of code in the same place as
   `toggle_extend_selection_mode` (main_frame.py:6369). The
   second two are ~20 lines. Total: under 100 LOC plus
   announcements and keymap entries.
3. **They compose with the existing mode.** A user can press F8
   for the power-user mode, *or* Ctrl+. for the EdSharp
   anchor/finish pair, *or* just use plain shift+arrows for
   normal one-off selections. The three are not mutually
   exclusive. A user who keeps the F8 flag on by accident and
   then presses Ctrl+. gets a fresh anchor at the caret; the
   F8 flag is irrelevant to the event-pair model.
4. **They let QUILL speak both dialects.** This is the right
   call for a screen-reader-first product: do not pick a
   favorite editor's mental model, *expose all the useful ones*
   with a consistent spoken contract.

**The recommended F8 change is small and additive**

What we *should* change in the F8 code path is the announcement
gap, not the mode:

- At 6369–6375 (the `toggle_extend_selection_mode` body), when
  the flag goes on, announce "Extend selection mode on. Anchor
  at line N, column M" using
  `line_column_for_position(insertion_point)`. The helper
  already exists in `quill/core/marks.py`.
- At 3074 (the Escape branch) and 3530–3534 (the F8-off
  branch), if there is a pending region, announce "Extend
  selection mode off. Last region: N words from line A col B
  to line C col D" *before* clearing the anchor. This is the
  "no silent loss" fix.
- At 3548–3551 (the non-movement-key branch), after
  `_commit_pending_extend_selection` runs and the
  `event.Skip()` returns, the next native key handler (Copy,
  Cut, etc.) operates on the committed region; we already
  have the region in scope. Add a one-line announcement
  there: "Committed selection: N words from line A col B to
  line C col D." This is the "audible proof the copy worked"
  fix.
- Add a status-bar cell "Selection session: anchored at line
  N" that updates on every F8 / Ctrl+. / Reselect. A
  screen-reader user can query the cell with a custom key
  ("Where is the anchor?") and get an immediate answer.

The four changes above are roughly 30 lines of code and three
unit tests. They do not require a keymap migration, a menu
relabel, a fixture regen, or a regression pass. They are
backwards-compatible and they bring the F8 mode into the same
announcement discipline as the rest of the selection pipeline.
**That is the right scope for QUILL 1.0.**

**What we should *not* do in 1.0**

- Do not rename F8. Do not change the menu label "Extend
  Selection Mode (F8)." Do not change the
  `edit.toggle_extend_selection_mode` semantics. Do not change
  the feature-command map. Do not regen the public surface
  fixture.
- Do not introduce a "EdSharp mode" toggle that flips the
  meaning of F8. The risk of footguns (a user toggles it,
  forgets, presses F8, gets the wrong behavior) is higher
  than the benefit of the unification.
- Do not deprecate the F8 mode. A power user who edits code
  or XML or CSV lives in this mode. Removing it is a real
  regression for that cohort.

**What we *should* do in 1.0** (revised Tier 1 list):

1. Add the four announce-on-commit changes above to
   `toggle_extend_selection_mode` and friends.
2. Add `edit.start_selection` (Ctrl+.) and
   `edit.complete_selection` (Ctrl+Shift+.).
3. Add `edit.reselect` and `edit.go_to_start_of_selection`.
4. Document all three in `dialogs.md` (because the new
   commands appear in the Edit menu and the keymap) and in
   the Help > QUILL Key Primer surface.
5. Add a selection-mechanics regression test that exercises
   the announce-on-commit path with a mocked TTS sink so the
   announcement contract is locked in.

If we get all five right, the EdSharp model is *available*,
the F8 mode is *announced correctly*, the screen-reader user
has a clear answer to "where is the anchor?" at all times,
and no existing user breaks.

**Where the two designs differ in feel:**

| Aspect                        | EdSharp F8 (event pair)                                                          | QUILL F8 (mode toggle)                                                  |
| ----------------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Mental model                  | "I am starting a selection session; I will end it later."                       | "I am in extend mode; every shift+arrow extends."                       |
| When the anchor is set        | At the moment you press F8 — never moves again until you Reset.                 | Implicit, at the moment of the *first* shift+motion in the session.    |
| How the selection is captured | A second, distinct keypress (Shift+F8) announces the region.                    | Each shift+arrow redraws and re-announces the region live.              |
| What "F8" means in a script   | "Begin." Always idempotent, never lingering.                                    | "Flip a state." Idempotent in pairs (on / off), surprising in between. |
| Failure mode                  | User forgets the anchor; presses Shift+F8 and gets a stale region.              | User forgets the flag is on; every shift+arrow keeps extending and the selection balloons. |
| SR announcement               | One anchor announcement at the start, one region announcement at the end.        | No anchor announcement; a region announcement per shift+motion.         |
| Composition with search       | "Search then F8 then Shift+F8" — the search hit becomes the end.                 | "Search then shift+Enter" extends, but the search is not part of the selection session; F8 is irrelevant. |

**Where QUILL wins.** The mode approach composes with *every*
shift+motion and shift+command in the editor for free. You can
F8 → shift+Ctrl+End and get "selection to end of document" with
one gesture. EdSharp would need an extra "Complete" keypress to
capture. The Escape branch means a screen-reader user who hears
*anything* go wrong can hit Escape and be safely out, which
matches the rest of the dialog contract.

**Where EdSharp wins.** The event-pair model is *declarative and
stateless*: at any moment the answer to "is the editor in a
selection session?" is "look for the most recent F8 with no
matching Shift+F8." There is no flag to forget, no anchor to
leak, no mode indicator to misinterpret. This is the model
Word's Quick Parts dialog, macOS text fields, and most modern
web text fields use. The anchor is announced explicitly
("Selection started at line 12, column 5"), so the screen
reader always knows the *origin* of a future selection, not
just the *current bounds*. QUILL's mixin announces the *bounds*
of the result; EdSharp announces the *anchor* of the intent.
"Reselect" and "Go to Start of Selection" are first-class
commands; QUILL has an expand / shrink stack but no explicit
"last region before current" recall across sessions.

**Honest call.** The right thing for QUILL 1.0 is **not** to
replace the mode toggle — that is a lot of code to throw away
and a real workflow win for power users — but to **add**
EdSharp-style commands alongside it:

- `edit.start_selection` (Ctrl+.) — sets an explicit anchor at
  the caret, announces it, and starts a "selection session."
  Unlike F8, it does not touch `_extend_selection_mode` and does
  not require the user to remember to disable anything.
- `edit.complete_selection` (Ctrl+Shift+.) — collapses the anchor
  + current caret into a region, announces it, and the editor
  is back to a normal single-caret state.
- `edit.reselect` and `edit.go_to_start_of_selection` — populate
  the LibreOffice / EdSharp gap.
- `edit.copy_with_position` — paste a copy of the selection with
  a trailing `[line 12 col 5 – line 14 col 22]` footer; useful
  for AI prompts.

These five commands cost roughly what Select Chunk costs (one
core helper in `quill/core/selection.py`, one announcement in
the mixin, one binding in `quill/core/keymap.py`) and they let
QUILL speak *both* dialects: the power-user mode toggle for
shift-motion composition, and the explicit begin / finish pair
for SR users who prefer the declarative model. That is the same
"every action has a spoken outcome" principle QUILL already
follows, applied to selection itself.

**Gaps vs. industry** (honest):

- **No Select Chunk (Ctrl+Space).** EdSharp's "Select Chunk" is a
  whitespace-bounded "W"-like motion. QUILL has word-span and
  line-span; a chunk-span (whitespace-and-punctuation run) is
  missing. Implement as a thin wrapper around
  `re.finditer(r'\S+', text)` and a cursor-position lookup.
- **No "Reselect" (EdSharp Ctrl+Shift+F8) or "Go to Start of
  Selection" (Alt+Shift+F8).** The expand / shrink stack effectively
  serves Reselect, but only for the current extend session. A
  Reselect that survives the extend session (last-popped-but-not-
  current) is a small, useful addition.
- **No anchor / point swap that survives the clipboard.** Emacs'
  `exchange-point-and-mark` is correct; QUILL mirrors it. But QUILL
  does not echo the anchor location when set — a screen-reader user
  pressing F8 then Shift+arrow hears the *new* bounds but not the
  anchor. Add an announcement: "Anchor at line 12, column 5."
- **No column / box select.** See §4.3.
- **No "Copy with anchor" pair (start + end positions).** Useful
  for AI prompts that need offset ranges. Add a `copy_with_position`
  to the Edit menu: copies the selection and a footnote with the
  line / column range.
- **No "Mark here, jump there" status line.** The mark-ring list
  dialog lists marks with line / column but does not show the
  current ring head. Add a status-bar cell that announces "Mark ring
  depth: 4."

### 4.22 EdSharp 4.0.1 specific gaps

EdSharp is the closest reference for QUILL's screen-reader-first
niche. The hotkey summary in `S:\EdSharp-4.0.1\hotkeys.txt`
exposes a number of primitives that are *not* in QUILL but are
trivial to add. Honest call: the items below are real gaps.

| EdSharp hotkey / command                 | QUILL status                                                                                  | Notes for implementation                                                                     |
| ---------------------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Select Chunk (Ctrl+Space)**            | Not present; `edit.word_prediction` is bound to Ctrl+Space                                    | Reassign or add `edit.select_chunk`; build `chunk_span(text, cursor)` primitive             |
| **Start Selection (F8) / Complete (Shift+F8)** | QUILL's F8 toggles extend-mode (different semantics)                                   | Two distinct ideas. Keep extend-mode on F8 (the QUILL convention) and add a separate "Start Selection" on Ctrl+. that anchors without extending |
| **Reselect (Ctrl+Shift+F8)**             | Partially — expand/shrink stack                                                                | Implement as "pop expand stack without committing"                                          |
| **Go to Start of Selection (Alt+Shift+F8)** | Not present                                                                                  | One-liner: collapse anchor to the smaller of the two bounds                                 |
| **Copy All (Ctrl+F8) / Unselect All (Ctrl+Shift+A)** | Not present                                                                            | Trivial                                                                                      |
| **Read All (Alt+F8) / Say Selected (Shift+Space) / Say Chunk (Shift+BackSpace)** | Not surfaced in the QUILL menu (Read Aloud exists for document playback)        | "Say Selected" maps cleanly to the existing TTS pipeline; "Say Chunk" is a chunk-span + TTS  |
| **Copy Append (Alt+C) / Cut Append (Alt+X)** | Not present                                                                                | Append to a per-document "Scratchpad" or to the clipboard with a " (continued)" separator    |
| **Append from Clipboard (Alt+7)**         | Not present                                                                                  | A toggle that, when on, auto-pastes every clipboard copy at the caret. Screen-reader users may find this noisy; gate it behind a "QUILL" chord |
| **Quote (Ctrl+Q) / Unquote (Ctrl+Shift+Q)** | Not present                                                                                | Wrap each line of the selection with a comment prefix inferred from the file extension (`#` for Python, `//` for C, `<!-- -->` for HTML, `>` for Markdown) |
| **Special Character (F2)**                | Not present in the QUILL menu (Power Tools may have it; verify)                              | Promote to Insert > Special Character... and bind to F2. Show a `wx.ListBox` of named Unicode blocks + a code-point entry |
| **Hard Line Break (Ctrl+Shift+H)**        | Not present                                                                                  | Calls `wrap_ops.hard_wrap(text, width)` with a prompted width. The inverse of `format.join_lines` |
| **Join Lines (Ctrl+Shift+J)**             | QUILL has `format.join_lines` (Ctrl+J family in some profiles; see `quill/core/keymap.py`) | Already there; verify the binding and the announcement parity with `wrap_ops.join_paragraph` |
| **Trim Blanks (Ctrl+Shift+Enter)**        | Not present                                                                                  | Trim trailing whitespace on every line of the selection; `format_ops.trim_trailing_whitespace` exists but is not on a single key |
| **Number Items (Alt+Shift+N) / Order Items (Alt+Shift+O) / Reverse Items (Alt+Shift+Z)** | QUILL has `sort_lines_ascending` / `descending` / `reverse_lines`; no per-item renumber | `line_ops.number_lines(text, start=1)` exists; expose a "Number Items" command and a "Number Items in Document" command |
| **Keep Unique (Alt+Shift+K)**             | `remove_duplicate_lines` exists; not on a single key                                          | Bind to a free chord and announce "Removed N duplicate lines"                                |
| **PyDent / PyBrace**                      | Not present                                                                                  | Python-indent ↔ braces converter. Power Tool or Quillin candidate                             |
| **Curly Brace Match (Ctrl+Shift+] / [)**  | `navigate.match_bracket` exists; no jump to enclosing / next                                 | Two commands: jump-to-enclosing and jump-to-next                                            |
| **Format Code (Ctrl+4)**                  | Not surfaced                                                                                | Wrap a Quillin: "Format Code" that uses Black / Ruff / isort depending on the file extension  |
| **Repeat Line (Ctrl+Y)**                  | QUILL's Ctrl+Y is Redo                                                                      | Either remap or add an Edit > "Repeat Line" with a different key                              |
| **Evaluate Expression (Ctrl+=)**         | Not present                                                                                  | Quillin: JScript / Python sandbox evaluation against the selection. Power Tool                |
| **Alternate Menu (Alt+F10)**             | Not present                                                                                  | A flat alphabetized list of every command. Easy to build from `quill.core.command_registry` |
| **SendTo Menu (Ctrl+F10)**                | Not present                                                                                  | A "Send to..." menu of internal actions (Editor, Read Aloud, Browser Preview, Compare)        |
| **Insert Time (Alt+Shift+;) / Calculate Date (Ctrl+Shift+;)** | Snippet variables exist (`$date$`, `$time$`) | Surface the two on first-class hotkeys                                                       |

The most important *single* addition here is **Select Chunk
(Ctrl+Space)**: it is a structural motion that QUILL's selection
pipeline can support today (one helper, one binding change, one
announcement). The second is **Quote / Unquote (Ctrl+Q /
Ctrl+Shift+Q)**: trivially useful, screen-reader-friendly
(announce the comment style that was applied), and the code is
already half-written in `quill.core.format_ops.toggle_line_comment`.

### 4.23 Text Monkey PRO transformation gaps

Text Monkey PRO (`http://www.boxersoftware.com/tmfeat.htm`) is a
useful reference for the *kind* of text cleanup that writers do all
day. QUILL's `Format > Transform Lines` submenu already covers a
respectable slice; the table below maps Text Monkey's categories
to QUILL's primitives, marking honest gaps.

| Text Monkey category                  | QUILL today                                                                                                | Gap                                                                                              |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Email cleanup** (sense quoted email, remove `>` prefixes, line break → space) | Not present                                                                                              | One Quillin. Strip `> ` and `>`, then replace each `\n` with a space when the next line starts with `> ` |
| **Web document cleanup** (delete HTML tags, decode `&quot;` and `&#034;`) | `quill.io.structured` and `quill.io.export` import/export HTML using `html.escape` / `html.unescape`; no in-document "Strip HTML" command | Add `format.strip_html` and `format.decode_entities`; the latter is one call: `html.unescape(text)` |
| **Space ops** (reduce space runs, one / two spaces after sentence enders) | `format_ops.normalize_whitespace` collapses all whitespace runs to a single space; not a first-class command in the Format menu | Promote to a command and add a "Two spaces after period" toggle for the typography crowd |
| **Line ops** (delete duplicate lines, delete lines containing text) | `format_ops.remove_duplicate_lines` (with `case_sensitive` flag) is used by `LineCommandsMixin.remove_duplicate_lines`; "delete lines containing" is not surfaced | Add `format.delete_lines_containing` and `format.delete_lines_not_containing` (the opposite)     |
| **Indent ops** (indent with N spaces, custom string) | `format_ops.indent_lines` and `outdent_lines` use a configurable `indent_unit`                       | Promote to a dialog that lets the user type the indent string and applies it to the selection     |
| **HTML operations** (delete tags, decode / encode entities, &#nnn; obfuscation for email) | `quill.io.structured` and `quill.io.export` handle entities on import / export; no in-document command | Add `format.delete_html_tags` and `format.encode_entities` (use `html.escape`)                     |
| **Sort variations** (numerical, by line length, ANSI / Locale, random) | `format_ops.sort_lines(text, descending=False, case_sensitive=False)` uses an alphabetic key | Add `sort_lines_numeric`, `sort_lines_by_length`, `sort_lines_locale`, and `shuffle_lines` as Power Tools (or new commands) |
| **Auto-number** (roman numerals, padding, leading zeros) | `line_ops.number_lines(text, start=1, separator=". ")` is a basic implementation                | Extend to a dialog that picks start, separator, roman / arabic, padding                          |
| **Strip** (low ASCII, high ASCII, OEM line drawing) | Not present                                                                                              | Quillin candidate. Use `str.isprintable` / Unicode categories                                    |
| **Replace** (up to 4 simultaneous search / replace pairs) | `format.replace_all` is a single pair                                                                       | Quillin or Power Tool: a "Multi-Replace" dialog with N (configurable) pairs                      |
| **Stats** (sum, average, median, mode, std deviation on selected numbers) | `compute_document_stats` returns characters / words / lines                                              | Add a "Statistics on Selection" dialog that parses numbers and reports sum / mean / median / mode / stddev |
| **Hex dump conversion**                 | Not present                                                                                              | `format.to_hex_dump` / `format.from_hex_dump` Quillin candidate                                  |
| **Teen Text / Crazy Text** conversion  | Not present                                                                                              | Fun Quillin candidate. Not a 1.0 feature                                                         |
| **Clipboard viewer / editor with undo** | `wx.TheClipboard` is used by `magic_paste`, `copy_with_source`, and the standard paste path; no built-in viewer | A "Clipboard History" persistent side region that stores the last N (configurable) clipboard items; this also lets QUILL build the Copy Append / Cut Append behaviors EdSharp users want |

**High-priority additions** (mapped to existing core modules):

1. **`format.strip_html_tags(text) -> str`** — strip everything
   matching `<[^>]+>` from the selection. Useful for AI-pasted
   output. Put in `quill/core/format_ops.py` and wire to Format >
   Transform Selection.
2. **`format.decode_html_entities(text) -> str`** — `html.unescape`
   wrapper. Same home, same menu.
3. **`format.keep_unique_lines`** — the `case_sensitive` flag on
   `remove_duplicate_lines` already covers it; rename / alias the
   command to "Keep Unique Lines (Case Sensitive)" so the
   discoverability matches the industry term.
4. **`format.shuffle_lines`** — Quillin candidate, one core helper.
5. **`tools.statistics_on_selection`** — the dialog from
   `quill/core/metrics.py` + a number-parser. Spec the dialog as a
   stock `wx.Dialog` with a `wx.TextCtrl` for the report.

The clipboard history panel is the single biggest Text-Monkey-
adjacent win for screen-reader users: it makes Copy Append / Cut
Append / Append from Clipboard implementable, and it gives the user
a spoken record of the last N things they copied.

---

## 5. Industry callouts that QUILL handles correctly

Some behaviors that are easy to get wrong and that QUILL has right —
these are worth saying out loud so they don't regress.

1. **Find and Replace are inside Edit; cross-file search is in
   Search.** This matches the conventional split and matches VS Code
   / Word.
2. **Selection submenu** keeps line / paragraph / block distinct and
   adds "Recent Marks (Ring)" as a nested submenu. This is the Emacs
   influence done well, and it is keyboard-friendly.
3. **The Status Bar settings** live in Tools > Customize, not in
   View. This is a Microsoft convention; it survives menu shuffles.
4. **Insert / Format / Navigate are separate menus.** This matches
   Word and avoids the Notepad++ "everything is in one Format menu"
   trap.
5. **BITS Whisperer is a submenu of Tools when enabled**, and
   demoted from a top-level menu so the main bar stays at ten
   entries.
6. **Pandoc Wizard lives in Tools > Authoring and Automation** —
   not in a buried settings dialog. Power users can find it.
7. **External Tools** lives next to Pandoc and has an executable
   allowlist enforced by the codebase. This is the correct security
   posture.
8. **Compare Documents** is a real submenu (not a sub-submenu) with
   "Next Difference" / "Previous Difference" / "Announce Current" /
   "Difference List" / "Synchronized Navigation" / "Summary" / "Copy
   Current" / "Copy All." That is unusually complete.
9. **Custom Profiles and Feature Profiles** are under Help, not
   buried. Users can find them.
10. **Accessibility Audit, Keyboard Trap Snapshot, Contrast, Link
    Inventory** are all in Tools > Accessibility, not scattered. This
    is a deliberate discoverability choice.

---

## 6. Menu consolidation proposal

The current menu is 10 top-level entries, with Tools being 14-deep
and three submenus reaching a third level. The proposal is to keep
ten top-level menus (the Windows norm) and keep two as the
maximum depth inside any submenu.

### 6.1 Top-level layout (unchanged)

> File, Edit, View, Insert, Format, Navigate, Search, Tools, Window,
> Help. The conventional Windows order. Status bar settings lives in
> Tools > Customize.

### 6.2 Tools submenu: the proposed reorganization

Group the 14 current Tools submenus into 7 logical clusters. The
ordering is by frequency of use: writing essentials first, then
automation, then meta / configuration.

| Cluster                  | Items (submenu)                                                                              | Why                                                                       |
| ------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Writing & Language       | Word Count, Spell Check, Previous/Next Misspelling, Misspelling List, Thesaurus, Dictionary Status | Unchanged from current "Writing and Language" submenu.                  |
| Reading & Dictation      | Read Aloud (with Voice / Settings / Generate Audio), Announcement Backend, Dictation, Watch Folder, OCR & Image | Merge Read Aloud + Dictation + Watch Folder + OCR/Image into one "Reading & Dictation" submenu. |
| Automation               | Macros, GLOW, Compare Documents, AI Assistant, BITS Whisperer                                 | Rename the current "Authoring & Automation" cluster; pull AI into it (it already lives under Tools). |
| Workspace                | Workspace Snapshots (relocated here from File), Sticky Notes, Sessions, Recent Files (relocated) | A new cluster that owns document organization. See §7.                 |
| Power Tools              | (All current Power Tools items)                                                              | Unchanged.                                                                 |
| Quillins                 | (All current Quillin items)                                                                  | Unchanged.                                                                 |
| Customization & Support  | Customize (Preferences, Menus, Profiles & Features, Status Bar, Export, Import, Keymap), Accessibility (Audit, Trap, Contrast, Link Inventory), Support (Notifications, Report Bug, Save Diagnostics, Logs, Updates) | A single "Settings & Support" cluster.                                  |

The Tools menu in two-deep form looks like:

```
Tools
├── Command Palette
├── ──────────
├── Writing & Language
│     ├── Word Count
│     ├── Spell Check
│     ├── Previous Misspelling
│     ├── Next Misspelling
│     ├── Misspelling List
│     ├── Thesaurus
│     └── Dictionary Status
├── Reading & Dictation
│     ├── Read Aloud  ▸
│     │     ├── Start / Pause
│     │     ├── Stop
│     │     ├── Voice
│     │     ├── Settings
│     │     └── Generate Audio
│     ├── Announcement Backend
│     ├── Dictation
│     ├── Watch Folder ▸
│     │     ├── Monitoring (in Settings)
│     │     ├── Profiles
│     │     └── Queue
│     ├── OCR Image
│     ├── OCR Clipboard
│     ├── OCR Screen
│     └── Describe Image
├── Automation
│     ├── Macros
│     ├── GLOW
│     ├── Compare Documents
│     ├── Document Intake
│     ├── Pandoc Wizard
│     ├── Regex Helper
│     ├── External Tools
│     └── YAML Structure Editor
├── AI Assistant
│     ├── Use AI
│     ├── AI Status
│     ├── AI Detail
│     ├── AI Hub
│     ├── Ask Quill Chat
│     ├── AI Model and Connection
│     ├── Forget API Key
│     ├── Session Branches
│     ├── Writing Assistant
│     ├── Prompt Studio
│     ├── Agent Center
│     ├── Accessibility Tune-Up
│     ├── Rewrite Selection
│     ├── Summarize Selection
│     ├── Continue Writing
│     ├── Fix Grammar
│     ├── Train Writing Style
│     └── Writing Instructions
├── BITS Whisperer (if enabled)
├── Workspace
│     ├── Workspace Snapshots ▸
│     │     ├── Save Current Snapshot
│     │     ├── Save As...
│     │     ├── Recent Snapshots ▸
│     │     └── Manage Snapshots...
│     ├── New Workspace from Folder...
│     ├── Sticky Notes
│     └── New Sticky Note
├── Power Tools
├── Quillins
├── Accessibility
│     ├── Accessibility Audit
│     ├── Keyboard Trap & Tab-Order Snapshot
│     ├── Validate Contrast
│     ├── Link Inventory & Alt-Text Catalog
│     ├── Inline Word Prediction (toggle)
│     ├── Auto-Format as You Type (toggle)
│     └── Smart Quotes (toggle)
└── Customize & Support
      ├── Preferences
      ├── Customize Menus
      ├── Profiles and Features
      ├── Status Bar Layout
      ├── Export and Back Up
      ├── Import or Restore
      ├── Keymap Editor
      ├── Export Keymap
      ├── Import Keymap
      ├── Reset Keymap
      ├── Notifications
      ├── Report a Bug
      ├── Save Diagnostics
      ├── Open Logs Folder
      ├── Open Diagnostics Folder
      └── Check for Updates
```

Two notable relocations:

- **Workspace Snapshots moves from File > Workspace Snapshots to
  Tools > Workspace**. The File menu is for "open / save this
  document" actions. Workspace is a "session of documents" concept
  and belongs with the cluster that will own the new Library
  surface (§7). A "Recent Snapshots" submenu replaces "Recent
  Sessions" inside the cluster.
- **Read Aloud** keeps its current submenu shape but is now nested
  inside Reading & Dictation. This keeps the two deep clusters
  (Read Aloud and Watch Folder) capped at the second level, which
  matches the standing "no third level" rule from the menu
  consolidation notes.

### 6.3 File menu

Suggested File menu reorganization (kept flat):

```
File
├── New
├── New from Template ▸  (existing Power Tools file-create items)
├── Open...
├── Open Recent ▸
├── Open from URL...
├── Open over SSH ▸
├── Workspace ▸  (new top-level submenu; see §6.4)
├── ──────────
├── Save
├── Save As...
├── Save All
├── Save As Plain Text...
├── ──────────
├── Reload from Disk
├── Restore Backup...
├── ──────────
├── Page Setup...
├── Print...
├── ──────────
├── Close Document
└── Exit
```

The Workspace submenu here is a *gateway* that links to the new
Workspace surfaces (Library, Snapshots, New from Folder) and to the
Tools > Workspace cluster where the management dialogs live. This
gives keyboard and screen-reader users two paths into the same
content.

### 6.4 View menu

```
View
├── Toggle Soft Wrap
├── Auto Side-by-Side Preview
├── Show Tab Control
├── Wrap Find Searches
├── Start With No Document Open
├── ──────────
├── Preview
├── Preview Side by Side
├── Focus Preview
├── Browser Preview
├── ──────────
├── Outline (toggle persistent outline panel; new)
├── Library (toggle persistent library panel; new)
├── Sticky Notes (toggle persistent sticky notes panel; new)
├── AI Chat (toggle persistent AI panel; new)
├── ──────────
├── Focus Mode (new; see §9.7)
└── Reading Ruler (new; see §9.8)
```

The four new toggles (Outline / Library / Sticky Notes / AI Chat)
show or hide the corresponding dialog content as a persistent
side region (see §7). "Focus Mode" is a one-key "F11" full-screen
writing surface that hides every chrome. "Reading Ruler" is a
high-contrast line-focus toggle for low-vision users.

### 6.5 Navigate menu

Already strong. Suggested additions (all behind the existing
feature-flag system):

- **Go To Bookmark in Workspace** — jump across documents in the
  current Workspace.
- **Go To Snippet** — fuzzy jump to a snippet.
- **Go To Misspelling** — already in the menu under Tools > Writing &
  Language; add a hotkey.
- **Go To Link** — already in Insert and Edit; ensure a key.
- **Go To Heading in Workspace** — cross-document heading jump
  when the active Workspace exposes headings.

### 6.6 Insert menu

Add: **Insert Image from File...**, **Insert Image from Clipboard**,
**Insert Math Block (LaTeX)**, **Insert Citation...** (when a
citation style is configured), **Insert Divider (Horizontal Rule)**,
**Insert Special Character...** (already likely in Power Tools;
promote to a first-class Insert entry).

### 6.7 Format menu

Add: **Auto-Format as You Type** toggle (under
Customize & Support currently; promote to Format or to View), and
**Smart Quotes / Smart Dashes / Smart Ellipses** toggles.

### 6.8 Help menu

Already has a sensible structure. Suggested additions:

- **QUILL Key Primer** (a screen-reader-friendly in-app quick
  reference, gated by the Help system).
- **Keyboard Reference (Printable)** — produces an accessible HTML /
  EPUB cheat sheet filtered by the active profile.
- **Workspace Tour** — first-run walkthrough of the new Library
  surface.

### 6.9 Search menu

Add: **Saved Searches**, **Search Results Window** (toggle docked
results), **Filter by Document** (when a Workspace is loaded).

---

## 7. Workspaces and Document Navigator: the redesign

This is the heart of the ask: take the existing Workspace Snapshots
concept and the existing `open_outline_navigator` modal and turn them
into a Ulysses/Obsidian/Scrivener-inspired but unmistakably QUILL
organization layer. The north star is *calm, keyboard-first, screen-
reader-narrated project organization*, with no new visual chrome a
sighted user would not also value.

### 7.1 Terminology

- **Workspace.** A named, restorable collection of documents,
  bookmarks, snippets, sticky notes, AI conversations, settings
  overrides, and shell hooks. The unit of "this is the project I am
  working on right now."
- **Sheet.** A single document inside a Workspace. Sheets are the
  atomic unit of focus. (The Ulysses name for a single document is
  "sheet" — borrowed on purpose because it is the right metaphor.)
- **Group.** A named, ordered folder of sheets within a Workspace.
  Groups nest. Groups are stored in the Workspace, not on the
  filesystem; the on-disk layout is the user's choice. (Ulysses
  uses "groups"; Scrivener uses "folders" inside the binder.)
- **Section.** A heading range inside a sheet. Sections are the
  unit of focus within a sheet. Already surfaced by
  `_outline_navigator`; now first-class inside the Library.
- **Library.** The on-screen, persistent side panel that shows the
  current Workspace's structure (Groups, Sheets, Sections) and
  drives the editor. (Ulysses name; matches the metaphor.)
- **Sticky Note.** A per-Workspace or global note pinned to a sheet
  or section. (Already exists; promote to a first-class Library
  surface.)
- **Snip.** A saved snippet bound to a Workspace. (New; extends the
  snippet system with a per-Workspace scope.)
- **Goal.** A writing target bound to a Workspace (daily / session /
  deadline). (Ulysses feature; new to QUILL.)
- **Filter.** A saved search / smart folder inside a Workspace.
  Filters are evaluated against the Workspace's sheets and persist
  with it.
- **Snapshot.** A saved point-in-time state of a Workspace.
  (Already exists; renamed for clarity.)
- **Session.** A loaded Workspace with the live documents open in
  the editor.

### 7.2 The Library panel

A docked `wx.Panel` on the left of the editor, toggleable from View
("Library"). The Library is the screen-reader page region with a
list of groups, sheets, and sections. It is *not* a tree (a flat
list with a heading level is more accessible); it shows the
Workspace's structure as a list with a single "level" disclosure
indicator.

Components (all stock wx):

- **Header** — Workspace name, last-saved time, word / character
  count, optional progress goal.
- **Filter** — a `wx.TextCtrl` at the top with a type-ahead filter.
  Matches sheet titles, sheet text, section titles, sticky note
  text, and tags. Announces the match count as it changes.
- **List region** — a `wx.ListBox` populated from the current
  Workspace's structure. Each entry has a label ("Chapter 3 >
  Beat sheet > 4. The reversal"), a kind (Group / Sheet / Section
  / Sticky Note / Filter result), and an optional state badge
  ("draft," "reviewed," "misspellings: 4," "modified").
- **Action bar** — buttons (or keyboard shortcuts): New Sheet, New
  Group, Rename, Delete, Move Up / Down, Promote / Demote, Open
  Sticky Note, Set Goal, Snapshot Now.
- **Context menu** — wired to the same actions. Stock wx context
  menu; no custom-drawn tree.

Behavior:

- **Live focus follows caret.** When the cursor moves to a section,
  the Library's selection moves with it (if the user has not
  manually scrolled the Library). Announce the change.
- **Keyboard re-order.** "Move Sheet Up" / "Move Sheet Down" /
  "Move Sheet to Group..." all in the Edit and Library menus.
- **Open in new editor tab / new window.** Long-form editing
  benefits from multiple open sheets. The Window menu gets "Next
  Sheet" / "Previous Sheet" if the user opts in to "open sheets in
  a tabbed editor."
- **Read-only by default; explicit write.** New Workspaces are
  empty until the user creates a sheet. Opening an existing
  Workspace Snapshot loads the document set, the caret positions,
  the AI sessions, and the sticky notes.
- **Save behavior.** A Workspace saves automatically on sheet save,
  on snapshot, and on a debounced interval (similar to settings
  persistence). Manual "Save Snapshot" is a menu item.

### 7.3 Outline panel (a docked tree)

Use the existing `_show_tree_navigator` logic but render it as a
panel, not a modal. The current modal is excellent for the
"right-now jump to" use case; the docked panel is for "let me see
the structure as I work." Behind the scenes both share a common
"outline index" primitive in `core/outline.py`. Both render the
same data through the same announcement grammar so the two
surfaces never disagree.

- The docked panel reads from the active sheet only.
- The modal still works for cross-document jumps inside a
  Workspace.
- Both speak the same names: headings, sections, blocks.

### 7.4 Workspace creation and persistence

A Workspace is a JSON file under `%APPDATA%\Quill\workspaces\`
(validated against `quill/core/schemas/workspace.json`). The
schema is intentionally tight:

```jsonc
{
  "schema_version": 1,
  "id": "ws_<uuid>",
  "name": "My Novel",
  "description": "Working title for the third book.",
  "created_at": "2026-06-01T12:00:00Z",
  "updated_at": "2026-06-01T12:00:00Z",
  "groups": [
    {
      "id": "g_chapters",
      "name": "Chapters",
      "sheets": ["s_intro", "s_chapter1", "s_chapter2"],
      "groups": []
    }
  ],
  "sheets": {
    "s_intro": {
      "id": "s_intro",
      "title": "Introduction",
      "path": "C:\\...\\intro.md",
      "format": "markdown",
      "sticky_notes": ["n_open_question"],
      "snippets": ["sn_opening_quote"],
      "tags": ["draft"],
      "last_caret": 1234
    }
  },
  "sticky_notes": {
    "n_open_question": {
      "id": "n_open_question",
      "title": "Open question",
      "body": "Is the protagonist a reliable narrator?",
      "pinned_to": "s_intro"
    }
  },
  "snippets": {
    "sn_opening_quote": {
      "id": "sn_opening_quote",
      "title": "Opening quote",
      "body": "> ..."
    }
  },
  "tags": ["draft", "reviewed"],
  "filters": [
    {
      "id": "f_open_loose_ends",
      "name": "Open loose ends",
      "query": "TODO OR FIXME"
    }
  ],
  "goal": {
    "kind": "words_per_day",
    "target": 500,
    "period": "day"
  },
  "snapshots": [
    {
      "id": "snap_<uuid>",
      "name": "First draft complete",
      "saved_at": "2026-06-01T12:00:00Z"
    }
  ]
}
```

The schema is intentionally simple: groups nest, sheets live in
groups, sticky notes and snippets are flat collections with
optional pinning. Tags are a free-form string list. Filters and
goals are optional.

### 7.5 File-system mapping

A Workspace is a *logical* layer on top of the user's filesystem;
it does not require a particular directory layout. The user
chooses where each sheet lives; the Workspace stores the path. The
"New from Folder..." command:

1. Walks the chosen folder.
2. Filters by extension (configurable: `.md`, `.txt`, `.epub`, etc.).
3. Suggests a Group / Sheet structure based on the folder tree.
4. Asks once: "Use this layout? Yes / Preview / Edit." The Preview
   shows the proposed tree before any save.
5. Writes the Workspace file.

A "New from EPUB..." command opens an EPUB and creates a Workspace
where the chapters are sheets and the headings are sections.
Matches `open_epub_navigator` semantics.

### 7.6 Workspace Snapshots reborn

- Rename "Workspace Snapshots" to **Snapshots** (the term in the
  Ulysses vocabulary).
- A Snapshot stores the *complete state* of a Workspace at a point
  in time: sheets, caret positions, sticky notes, snippets, AI
  sessions, and the document bytes. This is what the current
  Workspace Snapshots already does; it just needs the rename and
  the menu relocation.
- A Snapshot is immutable. Restoring a Snapshot reopens the
  Workspace from the saved state. Diffing Snapshots is exposed
  through Compare Documents (current menu, current engine).
- Snapshots are exportable as a single `.qws.json` file (the
  Workspace file) and importable, with a conflict-resolution
  dialog for name collisions.

### 7.7 Filters and Smart Folders

A Filter is a saved search. Evaluation rules:

- Match sheets by title, body, sticky-note text, snippet text, or
  tags.
- Boolean expressions: `tag:draft AND title:ch*`.
- Regex support is opt-in.
- Result is a virtual group; opening a result jumps to the match
  in the source sheet.

Filters surface in the Library as a "Filters" sub-list. Selecting
a filter narrows the Library list to its matches; selecting
"Clear Filter" returns to the full list.

### 7.8 Goals and Progress

A Goal is a daily, session, or deadline target. The simplest form:

- Words per day (or characters or sentences).
- Words per session.
- Word count deadline ("reach 50,000 words by 2026-09-30").

The status bar gets a "Progress" cell that announces the
percentage and the remaining words. The Library header shows the
same. A "Streak" cell tracks consecutive days. A spoken
notification at end of session ("Goal reached: 500 words today")
is opt-in and respects the shared announcement grammar.

### 7.9 Cross-document navigation

A Workspace exposes new Navigate menu items:

- **Go To Heading in Workspace** — fuzzy jump across sheets in
  the current Workspace.
- **Go To Bookmark in Workspace** — same.
- **Go To Sticky Note in Workspace** — same.
- **Go To Tag** — opens the Library with the tag filter applied.
- **Go To Filter Result** — opens the active filter's matches.

All of these compose with the existing `quick_nav` index and
benefit from the same prewarm cache.

### 7.10 What this looks like as a flow

A first-run writer opens QUILL and is offered: "Start a new
Workspace, open a recent Workspace, or open a file." Selecting
"Start a new Workspace" shows a dialog: "Name, optional
description, optional folder to import from." A new Library
panel appears (or the docked outline tree appears) and the user
starts writing.

After 20 minutes the Library is full of groups, sheets, sticky
notes, and one filter ("TODO"). The status bar shows "Words:
1,234 of 500 today — goal reached." A single keystroke (Ctrl+K,
or QUILL+K) opens the command palette; typing "snapshot" offers
"Snapshot Workspace" and "Manage Snapshots."

A blind user goes through the same flow with the screen reader
narrating "Group: Chapters. Sheet: Introduction. Section: The
premise. Heading level 1. Word count 312." The panel is a
single list region, not a tree, and the focus is always
predictable.

### 7.11 Why this matches the Ulysses / Obsidian / Scrivener bar

- **Ulysses** — library, sheets, groups, filters, goals. QUILL
  borrows the *vocabulary* and the *single-list region* but
  replaces the Mac-only metaphors (sheet sidebar, keyboarder
  two-pane split) with the QUILL key + Quick Nav + docked panel
  + Workspace Snapshot model.
- **Obsidian** — vault, graph, backlinks, Bases. QUILL borrows
  the *vault metaphor* (Workspace = local vault) and the
  *saved filters* (Filters) but explicitly does not adopt the
  graph view in 1.0 (per the standing rules, axe-core, etc., are
  deferred to 2.0). A future "Backlinks" panel that scans the
  Workspace for `[[wiki-style]]` links is a natural 2.0 add-on.
- **Scrivener** — binder, corkboard, outliner, snapshots.
  QUILL borrows the *snapshots* (immutable saves) and the
  *binder* (Library panel) and adds a *Filter* concept that
  Scrivener lacks.
- **Org-mode** — tree, tags, agenda, babel. QUILL borrows the
  *tags* and the *agenda* (Goal) but not the babel / executable
  block. The user Python sandbox and Quillins cover similar
  ground in a more contained way.
The shape is *QUILL-native*: a docked left panel, the QUILL key,
Quick Nav, command palette, and a Workspace Snapshot JSON. The
metaphors are borrowed because they are the right ones; the
implementation is QUILL's.

---

## 8. "Make it amazing" — creative proposals

These are not strict backlog items. They are sketches to inspire
discussion, in priority order.

### 8.1 The QUILL key "what can I do here" panel

The roadmap already calls for a non-modal QUILL key overlay. The
proposal: when the user presses the QUILL key and pauses (no
follow-on key within 250ms), a small overlay appears at the
bottom-left of the editor showing the top ten follow-on keys for
the current context. The overlay is *navigable by arrows*, *closes
on Escape*, and is *announced by the screen reader*. Pressing a
follow-on key dismisses the overlay and runs the command. This is
"Spotlight meets the QUILL key."

### 8.2 Spoken Workspace Tour

A first-run experience for Workspaces: when the user opens a new
Workspace, the QUILL voice narrator walks through the structure
("Workspace: My Novel. 3 groups, 12 sheets, 4 sticky notes. Group
1: Chapters. Sheet 1: Introduction..."). The user can press
Escape to skip, or Space to continue. This is Ulysses's "Sheets"
onboarding, screen-reader-first.

### 8.3 Inline word and character count per section

A docked *Section Stats* cell that shows the word count, the
character count, the reading time, and the "misspelling hint" (a
small badge that links to the Misspelling List filtered to this
section). Updates as the user types. Announced on demand by a
status-bar query.

### 8.4 "Focal Mode" (F11)

A full-screen writing surface that hides the menu bar, the status
bar, the Library panel, the sticky notes, and the AI chat. The
editor is centered, the current paragraph is highlighted, and a
reading ruler (an optional 2-line band) follows the cursor. The
screen reader narrates the current sentence, the next sentence,
and the document position on every caret move. Voice: "Sentence
twelve of forty-two, paragraph three of seven, sheet
'Introduction', line 41." This is a writer's room, not a
distraction surface.

### 8.5 Audio Workspace

A Workspace that lives in the audio domain. A user opens an
audio file (or records into QUILL via BITS Whisperer), the
transcript becomes a sheet, the sticky notes become bookmarks,
and the Workspace's Goal is "minutes recorded today." This is
the same Workspace concept applied to a different content
type — and it is genuinely novel for a screen-reader-first
editor.

### 8.6 In-line AI "ghost" suggestions

A non-modal AI completion surface: as the user types, a small
ghost text appears (gray, italic) showing the AI's suggested
continuation. Pressing a configurable key ("QUILL + ." or "Tab
when no other completion is showing") accepts the suggestion.
"QUILL + ," dismisses. The suggestions are opt-in per Workspace
and respect the consent gate. This is a much lighter-weight AI
experience than the dialog-based rewrite / continue flow that
already exists.

### 8.7 Reading Mode

A mode that turns the editor into a read-only surface with a
configurable line-focus highlight, an optional reading ruler,
and a single key ("R") that reads the current sentence / line /
paragraph aloud using the existing Read Aloud engine. The screen
reader is *not* competing; the editor narrates only on demand.
This is iA Writer's Focus Mode with a screen-reader twist.

### 8.8 "Speak workspace" command

A single key that reads the Library's current selection in full:
the Workspace name, the structure (group > sheet > section), the
sticky notes pinned to the current sheet, the goal status, and
the last snapshot time. This is QUILL's "I am here" speech. It
takes one line of code and is a confidence-builder for new
users.

### 8.9 Inline status for sticky notes

When a sticky note is pinned to a sheet, a small status-bar cell
shows the count and the most-recent title. Focusing the cell
opens a query dialog; pressing Enter jumps to the Sticky Notes
panel filtered to the current sheet.

### 8.10 Quick Goal

A status-bar cell that opens a one-field "Daily Goal" prompt on
Enter. The user types 500, presses Enter, and the Goal is set
for the current Workspace. The cell updates to show progress.

### 8.11 Section-level Word Prediction

Take the existing `edit.word_prediction` dialog and add an inline,
opt-in, as-you-type variant that completes the current word from
the surrounding 50 characters of context. The screen reader is
*not* interrupted; the suggestion appears as a status-bar cell
and is accepted with one key. This is a much smaller lift than
LLM completion and is a high-frequency productivity win.

### 8.12 "Reveal in Workspace"

A context-menu action on any file path in the editor: "Reveal in
Workspace." If the file is in the current Workspace, the Library
panel scrolls to the matching sheet and announces it. If the
file is not in the current Workspace, the user is offered "Add
to Workspace" / "Open in New Workspace" / "Cancel."

### 8.13 Cross-document outline

A new Quick Nav category: "Workspace Headings" — every heading
in every sheet in the current Workspace, with a small badge
("Chapter 3 > 4. The reversal") showing the parent sheet. A
single keystroke jumps to it. This composes with `quick_nav`
without a new code path.

### 8.14 Section-level diff and review

A "Review Changes" mode that shows the diff between the current
sheet and the last Snapshot, organized by section. The screen
reader announces the section name and the change count. This is
Scrivener's "Compare" applied at the section level.

### 8.15 Section-anchored sticky notes

A sticky note can be pinned to a *section*, not just a sheet. The
note moves with the section as the user edits. This is a small
data-model change with a large usability impact for writers
doing research-heavy work.

### 8.16 Snippet: "paste Workspace context"

A snippet that, when expanded, pastes a YAML or Markdown
front-matter block with the current Workspace name, sheet name,
section name, line, and column. Useful for AI prompts, bug
reports, and structured notes.

### 8.17 Per-sheet feature profile

Allow a Workspace to override the global feature profile per
sheet. A research sheet might have AI disabled; a draft sheet
might have GLOW disabled; a publish sheet might have macros
disabled. This is a power-user feature; it does not need to be
the default.

### 8.18 Custom panel slots

A `View > Panels` submenu that lets the user choose which docked
panels to show: Library, Outline, Sticky Notes, AI Chat, Spell
Check, Search Results, Misspelling List. Each panel is a single
wx region; the user composes the layout.

### 8.19 Workspace-only "export to EPUB"

A command on the Workspace that orders the sheets, applies the
heading hierarchy, generates a table of contents, and exports a
single EPUB. The Pandoc wizard already does the conversion; the
Workspace layer does the assembly.

### 8.20 Workspace as a search corpus

Add a checkbox to the existing `search_in_files` dialog: "Limit
to current Workspace." The user can search the whole machine
or just the project.

### 8.21 "Sticky Note to Sheet" promote

A command on a sticky note that promotes it to a full sheet.
The note's title becomes the sheet title; the body becomes the
sheet's first paragraph. This is the inverse of "Sheet to
Sticky Note" and a common workflow ("I wrote a note, now I want
to expand it").

### 8.22 AI on a Workspace

The AI Hub gets a "Workspace" tab that shows the current
Workspace's structure and lets the user ask questions like
"What open loose ends do I have?" or "List the three
introductions that mention the antagonist." Answers cite the
sheet and section. The consent gate is the same.

### 8.23 Cross-Workspace references

A Workspace can include sheets from other Workspaces as
"references." Useful for a research Workspace feeding a
manuscript Workspace. The reference is a read-only copy in the
referring Workspace; updates are detected on Snapshot save.

### 8.24 "Today" view

A new panel that shows everything that changed in the current
Workspace today: new sheets, edited sheets, new sticky notes,
new snapshots, AI sessions, and the Goal progress. This is
Ulysses's "Today" list, screen-reader-first.

### 8.25 Workspace Diff

Two Workspaces can be diffed (sheet presence, sticky note text,
filter results). Useful for "what's different between the draft
I sent to the editor and the one I have now?"

### 8.26 Voice-driven Workspace navigation

A voice command (Hey QUILL) that opens a sheet by name, sets a
goal, or pins a sticky note. "Hey QUILL, open the introduction."
"Hey QUILL, set today's goal to 750 words." The dictation
engine is the same; the command grammar is Workspace-aware.

### 8.27 Workspace onboarding

A first-run "Try a Sample Workspace" that ships with QUILL:
a tiny project ("Letter to a friend") with three sheets, one
sticky note, one filter, and one goal. The user opens it,
explores the Library, the Outline, the Sticky Notes, the
Snapshots, and the AI Hub — all without writing a word. The
onboarding is itself screen-reader-friendly.

### 8.28 Per-section reading time and Flesch-Kincaid

Each section gets an announced reading time and a Flesch-Kincaid
grade level. The status bar cell toggles between "Words,"
"Reading time," and "Grade level." This is a writing-quality
superpower for a screen-reader user who can't see the wall of
text and wants a number.
### 8.29 Workspace focus session

A "Start a 25-minute focus session" command that opens a single
sheet, hides the Library and Sticky Notes, sets a 25-minute
timer, and announces the start and end. At the end, the Library
returns, the Goal cell updates, and a "Snapshot" button is
offered.

### 8.30 "I am stuck" command

A single key that opens a Workspace-aware AI prompt: "Help me
write the next paragraph of the current sheet, using these
three notes and this filter result as context." The consent
gate is the same; the response is previewed in a docked panel
and accepted with a single key. This is the AI "writer's block"
killer.

---

## 9. Implementation roadmap

Suggested sequencing, mapped to the existing roadmap priority
language.

### 9.1 Tier 1 (1.0 essentials)

- **Workspaces and Library panel** (§7). The core of the redesign.
  The new schema, the persistent side panel, the snapshot rename.
- **Menu consolidation** (§6). Pure reorganization. Ship a
  `menus.md` companion document alongside.
- **Focus Mode** (§8.4). Single screen, hides chrome.
- **Inline word prediction** (§8.11). High-frequency, low-risk.
- **Auto-format toggle** (§4.14). High discoverability win.
- **Context menu for misspellings** (§4.16). High discoverability
  win.
- **Duplicate selection** (§4.17). Tiny lift, big win.
- **Image insert** (§4.15). Required for many writing apps.
- **Go To Line preview** (§4.9). Trivial.
- **Select Chunk (Ctrl+Space)** (§4.22). Single most important
  EdSharp gap. One core helper, one binding change.
- **Quote / Unquote lines (Ctrl+Q / Ctrl+Shift+Q)** (§4.22). Half
  the code already exists in `format_ops.toggle_line_comment`.
- **Strip HTML tags + decode entities** (§4.23). Two
  `format_ops` helpers, two menu commands.
- **Announce anchor on F8** (§4.21). The most under-noticed
  selection-UX gap.

### 9.2 Tier 2 (post-1.0, near-term)

- **Filters and Smart Folders** (§7.7). Composes with Library.
- **Goals and Progress** (§7.8). Composes with Library.
- **Cross-document outline and quick nav extensions** (§7.9, §8.13).
- **Section-level stats** (§8.3).
- **Inline status for sticky notes** (§8.9).
- **Quick Goal** (§8.10).
- **Reveal in Workspace** (§8.12).
- **Multi-cursor / column select** (§4.3). Larger lift; needs a
  design pass.
- **Saved Searches** (§4.10).
- **Snippets tab stop / placeholder walkthrough** (§4.8).
- **AI chat docked** (§4.5).
- **Reading Ruler** (§4.13).

### 9.3 Tier 3 (exploratory, 2.0 and beyond)

- **Backlinks panel / vault graph** (Obsidian-style; explicit
  deferral per standing rules).
- **Corkboard view** (Scrivener-style).
- **Audio Workspace** (§8.5). Needs BITS Whisperer complete.
- **In-line AI ghost suggestions** (§8.6). Needs the consent
  surface to be a first-class UI element.
- **Cross-Workspace references** (§8.23).
- **Workspace diff** (§8.25).
- **Voice-driven Workspace navigation** (§8.26). Needs the
  voice-commands grammar to mature.
- **Clipboard history panel** (§4.23). Needs the dialog
  inventory's docked-panel classification; useful for Copy
  Append / Cut Append, but bigger surface than a Tier 1 item.
- **Statistical summary on selection** (§4.23). Bigger scope
  than Strip-HTML; needs a number-parser and a report dialog.
- **Multi-replace dialog** (§4.23). Genuine writer workflow
  improvement, but the dialog design and undo semantics need
  a design pass.
- **PyDent / PyBrace converter** (§4.22). Quillin candidate;
  needs test corpus.

### 9.4 Tier 4 (creativity, optional)

- **"Speak workspace" command** (§8.8). One-liner; high delight.
- **Workspace-only "export to EPUB"** (§8.19).
- **Per-section reading time and grade level** (§8.28).
- **Section-anchored sticky notes** (§8.15).
- **Sticky Note to Sheet promote** (§8.21).
- **"Today" view** (§8.24).
- **Workspace focus session timer** (§8.29).
- **"I am stuck" command** (§8.30).
- **Sample Workspace onboarding** (§8.27).
- **Snippet: paste Workspace context** (§8.16).
- **Per-sheet feature profile** (§8.17).
- **Custom panel slots** (§8.18).
- **Reading Mode** (§8.7).
- **Inline status for sticky notes** (§8.9, overlap).
- **Snippets for Workspace context** (§8.16, overlap).

---

## 10. The Revision Plan (binding)

This section is the **single source of truth** for what QUILL 1.0
will land, in what order, and why. Every recommendation in §1
through §9 is either accepted as written, accepted with edits
recorded below, or explicitly deferred with a reason. No
recommendation is "to be decided later."

Three corrections to the rest of the document are made here, not
sprinkled through the previous sections, so the plan is reviewable
as one piece:

- **Ulysses "Sheets" → "Entries."** §7 used the Ulysses word
  *Sheet* for a single document inside a Workspace. The user
  flagged that the word is too Ulysses-specific. From this
  point forward a single document inside a Workspace is an
  **Entry**. Multiple documents are **Entries**. The Workspace
  is a **Notebook** of Entries. This is a name-only change; no
  data model field is renamed in 1.0 — the JSON key
  `sheets[]` becomes `entries[]` in the new schema, but old
  files with `sheets[]` continue to load until 2.0.
- **No reading ruler, no focus mode pane.** §8.4, §8.7, §8.13,
  §4.7, §4.13 described a Reading Ruler and a focal pane. The
  user said: *we don't need a ruler, we don't need a pane, use
  the Document Navigator for the feature here.* The Document
  Navigator is the existing `_show_tree_navigator` modal at
  `quill/ui/main_frame.py:11732` and its partners
  (`open_outline_navigator`, `open_epub_navigator`,
  `open_yaml_structure_editor`, the Misspelling Navigator, the
  Document Intake dialog). All "focal" / "ruler" / "line focus"
  / "Reading Mode" ideas are withdrawn; the Document Navigator
  is the canonical "where am I, what is around me" surface, and
  it is **promoted to a top-tier verb** (Open Navigator, F7
  with a dedicated binding, dialog contract classified as
  `hardened_custom`, status-bar cell "Navigator: §3.2 The
  reversal").
- **Match EdSharp exactly where it matters.** The selection
  audit (§4.21) and the EdSharp gap audit (§4.22) are now
  consolidated into a single binding decision: §10.1 below
  *adopts EdSharp's selection model verbatim* for the new
  selection verbs, *keeps the F8 mode toggle* as a power-user
  opt-in, and *adds the four missing announcements* to the F8
  path. The earlier §4.21.2 "add commands alongside" framing
  is replaced by "add commands that are EdSharp-exact in
  semantics, keyed exactly as EdSharp keys them, and announce
  the same way EdSharp announces."

Everything else in §1 through §9 is accepted as written unless
explicitly struck through here.

### 10.2 Workspaces and Entries — the binding spec

This subsection replaces §7. The redesign is preserved in
spirit and reduced in scope: **Ulysses-grade full library
is deferred to 2.0**; 1.0 ships a Workspace with a
persistent Entries list, a focused Document Navigator
surface, and a Saved Searches manager. The goal is "match
what EdSharp and Notepad++ users actually do today,"
not "match Ulysses."

**Naming (binding).** A Workspace contains **Entries**.
An Entry is one file. Entries are organized in **Groups**
(ordered, nestable, stored in the Workspace JSON, not on
the filesystem). An Entry can have **Sections** (heading
ranges, computed from the document, not stored). A
Workspace can have **Sticky Notes** (already exist),
**Snippets** (already exist), and **Filters** (saved
searches, new in 1.0). A Workspace can have a **Goal**
(words per day, new in 1.0). A Workspace can be
**Snapshotted** (already exists; renamed from "Workspace
Snapshots" to **Snapshots**).

The naming replaces the §7 vocabulary:

| §7 word        | New word         | Why                                        |
| -------------- | ---------------- | ------------------------------------------ |
| Sheet          | **Entry**        | User said: not "Sheets."                   |
| Library        | **Entries panel**| More specific; matches the noun.           |
| Workspace JSON | **Notebook JSON** | Optional; "Workspace" is the verb.       |
| Library header | **Notebook header** | Optional; the panel is the Entries panel. |
| Group          | **Group** (unchanged) | Ulysses-coined, but neutral.            |
| Section        | **Section** (unchanged) | Standard.                              |
| Snapshot       | **Snapshot** (unchanged) | Already correct.                      |
| Goal           | **Goal** (unchanged)    | Already correct.                      |
| Filter         | **Filter** (unchanged)  | Already correct.                      |

**Document Navigator is the focal surface.** Per the user
direction, there is **no** new reading ruler, no new
focal pane, no new "where am I" widget. The Document
Navigator — the existing `_show_tree_navigator` modal at
`quill/ui/main_frame.py:11732` and its partners — is the
canonical "structure" surface. The 1.0 plan for it:

- Bind **F5** to `navigate.open_document_navigator` (the
  Outline Navigator, currently `Ctrl+Shift+O`). F5 is
  free in the default keymap; F7 is already taken by
  Spell Check (`tools.spell_check_dialog`,
  `quill/core/keymap.py:37`) and is anchored by
  `Alt+F7` / `Shift+Alt+F7` / `Shift+F7`, so it cannot
  be the navigator binding. The original draft of this
  plan said F7 was "previously unmapped" — that was
  wrong; this is the correction.
- Keep `Ctrl+Shift+O` as the secondary binding so users
  who learned it before the F5 promotion still get the
  navigator (legacy compatibility).
- Add a "Notebook" tab to the Document Navigator dialog
  that shows the current Workspace's Entries and Groups
  (replacing the §7 "Library panel slides in" idea).
  The tab is a `wx.Notebook` page that reuses the same
  tree-control primitive the Outline tab already uses.
- Add a status-bar cell "Navigator: §3.2 The reversal"
  that updates on caret move and announces on demand
  (`view.announce_navigator_position`, no default key).
- The Document Navigator dialog's dialog contract
  classification in `dialogs_inventory.json` is
  `hardened_custom` (already is). No new dialog class.

**Entries panel (the docked list).** A new top-level
View toggle **"Entries"** shows or hides a docked
`wx.Panel` on the left of the editor. The panel is a
`wx.ListBox` with the current Workspace's structure
(Groups, Entries, Sections). The panel:

- Has a header with Workspace name, last-saved time,
  word / character count, and optional Goal.
- Has a type-ahead filter `wx.TextCtrl` at the top.
  Matches Entry titles, body, Section titles, Sticky
  Note text, and tags. Announces match count on
  change.
- Live-focus follows the caret when the user has not
  manually scrolled the panel.
- Keyboard re-order: "Move Entry Up," "Move Entry
  Down," "Move Entry to Group..." in the Edit menu
  and the Entries panel context menu.
- A new View toggle **"Sticky Notes"** shows or hides
  a docked Sticky Notes panel (the existing
  `sticky_notes` infrastructure gets a docked surface
  in 1.0; the dialog is still `sticky_notes`).
- The docked Sticky Notes panel shares the
  "docked panel" classification in
  `dialogs_inventory.json` and follows the §6 menu
  layout.

**Workspace (Notebook) JSON schema (binding).** A new
file `quill/core/schemas/notebook.json` plus the
loader / writer in `quill/core/notebook_store.py`.
Stored at
`%APPDATA%\Quill\notebooks\<notebook-id>.qnb.json`.
Atomically written via
`quill.core.storage.write_json_atomic`. Validated
against the schema on load. Top-level shape:

```jsonc
{
  "schema_version": 1,
  "id": "nb_<uuid>",
  "name": "My Novel",
  "description": "",
  "created_at": "2026-06-01T12:00:00Z",
  "updated_at": "2026-06-01T12:00:00Z",
  "entries": {
    "e_intro": {
      "id": "e_intro",
      "title": "Introduction",
      "path": "C:\\...\\intro.md",
      "format": "markdown",
      "tags": ["draft"],
      "last_caret": 1234,
      "sticky_notes": ["n_open_question"]
    }
  },
  "groups": [
    {
      "id": "g_chapters",
      "name": "Chapters",
      "entry_ids": ["e_intro", "e_chapter1", "e_chapter2"],
      "groups": []
    }
  ],
  "sticky_notes": {
    "n_open_question": {
      "id": "n_open_question",
      "title": "Open question",
      "body": "Is the protagonist a reliable narrator?",
      "pinned_to": "e_intro"
    }
  },
  "snippets": {
    "sn_opening_quote": {
      "id": "sn_opening_quote",
      "title": "Opening quote",
      "body": "> ..."
    }
  },
  "filters": [
    {
      "id": "f_open_loose_ends",
      "name": "Open loose ends",
      "query": "TODO OR FIXME"
    }
  ],
  "goal": {
    "kind": "words_per_day",
    "target": 500,
    "period": "day"
  },
  "snapshots": [
    {
      "id": "snap_<uuid>",
      "name": "First draft complete",
      "saved_at": "2026-06-01T12:00:00Z"
    }
  ]
}
```

The schema is intentionally tight. Groups nest.
Entries live in groups. Sticky notes and snippets are
flat collections with optional pinning. Tags are a
free-form string list. Filters and goals are optional.
Snapshots are immutable saves of the entire notebook
state.

**Workspace creation commands (1.0 set).** Five new
commands in the File and Tools menus:

- `file.new_notebook` — opens a `wx.Dialog` (classified
  `hardened_custom`) prompting for name, description,
  optional folder to import from. Creates the
  `.qnb.json`. No entries yet.
- `file.new_notebook_from_folder` — walks a folder,
  filters by extension (configurable), creates one
  Entry per file, groups by relative directory. Shows
  a Preview page before save.
- `file.open_notebook` — opens a `wx.FileDialog` filtered
  to `.qnb.json`, loads the notebook, restores the
  Entries, the caret positions, the sticky notes, the
  AI sessions, and the Snippets.
- `file.save_snapshot` — saves the current state as an
  immutable Snapshot. Bound to Ctrl+Shift+S.
- `file.manage_snapshots` — opens a `wx.Dialog` listing
  the snapshots for the current notebook, with
  Restore / Rename / Delete actions.

**Cross-document navigation (1.0 set).** Four new
commands in the Navigate menu:

- `navigate.go_to_heading_in_notebook` — fuzzy jump
  across all headings in the current notebook's
  entries.
- `navigate.go_to_bookmark_in_notebook` — fuzzy jump
  across all bookmarks.
- `navigate.go_to_sticky_note_in_notebook` — fuzzy jump
  across all sticky notes.
- `navigate.go_to_tag` — opens the Entries panel with
  the tag filter applied.

All four reuse the existing `quick_nav` index from
`quill/core/navigate.py`. No new code path is needed
beyond a category filter.

**Filters (1.0 set).** A new "Saved Searches" manager
in the Search menu. A Filter is a named saved search.
Evaluation rules:

- Match entries by title, body, sticky-note text,
  snippet text, or tags.
- Boolean expressions: `tag:draft AND title:ch*`.
- Regex support is opt-in.
- Result is a virtual group; opening a result jumps to
  the match in the source entry.

Filters surface in the Entries panel as a "Filters"
sub-list. Selecting a filter narrows the Entries list
to its matches; selecting "Clear Filter" returns to
the full list.

**Goals (1.0 set).** A Goal is a daily, session, or
deadline target. The simplest form:

- Words per day (or characters or sentences).
- Words per session.
- Word count deadline.

The status bar gets a "Progress" cell that announces
the percentage and the remaining words. The Entries
panel header shows the same. A "Streak" cell tracks
consecutive days. A spoken notification at end of
session ("Goal reached: 500 words today") is opt-in
and respects the shared announcement grammar.

**Snapshot rename.** "Workspace Snapshots" is renamed
to "Snapshots." The File menu loses
"Workspace Snapshots" entirely; the Tools menu gains
"Notebook" with submenu "Save Snapshot" (Ctrl+Shift+S),
"Save As..." (name a snapshot), "Recent Snapshots"
(last 10), "Manage Snapshots..." (the dialog above).
The rename is reflected in `quill/core/keymap.py` and
the `menu_label("Workspace &Snapshots", ...)` calls at
`quill/ui/main_frame_menu.py:850` and equivalents.

**What is explicitly *not* in 1.0 (deferred to 2.0):**

- The full "Ulysses library" with groups of groups of
  groups, per-Entry feature profiles, per-Entry
  backgrounds, per-Entry goals, cross-Notebook
  references, Notebook diff, Audio Notebooks, voice-
  driven Notebook navigation, sample Notebook
  onboarding. These are §8 long-tail items that are
  genuinely 2.0 work.
- Backlinks / vault graph (Obsidian-style). Explicit
  2.0 deferral per standing rules.
- Index-sheet / corkboard view (Scrivener-style).
  Explicit 2.0 deferral.
- AI on a Workspace. The AI Hub gets a "Notebook" tab
  in 2.0; in 1.0 the AI actions operate on the active
  Entry only.

### 10.3 Menu consolidation (binding)

This subsection refines §6. The proposal is to keep
ten top-level menus (the Windows norm) and cap
submenu depth at two. The Tools menu gets a single
**reorganization**; nothing is removed from the
functionality. The relocations below are binding.

**Top-level layout (unchanged from §6):**
File, Edit, View, Insert, Format, Navigate, Search,
Tools, Window, Help. Status bar settings lives in
Tools > Customize.

**File menu (binding):**

```
File
├── New
├── New from Template ▸
├── Open...
├── Open Recent ▸
├── Open from URL...
├── Open over SSH ▸
├── ──────────
├── New Notebook
├── Open Notebook...
├── New Notebook from Folder...
├── ──────────
├── Save
├── Save As...
├── Save All
├── Save As Plain Text...
├── ──────────
├── Save Snapshot                  (was Workspace Snapshots > Save Current)
├── Save Snapshot As...
├── Recent Snapshots ▸
├── Manage Snapshots...
├── ──────────
├── Reload from Disk
├── Restore Backup...
├── ──────────
├── Page Setup...
├── Print...
├── ──────────
├── Close Document
└── Exit
```

**Edit menu (binding).** Adds the new selection verbs
from §10.1:

```
Edit
├── Undo
├── Redo
├── ──────────
├── Cut
├── Copy
├── Copy with Source                (Ctrl+Shift+C, unchanged)
├── Copy with Position              (new; trailing "[line N col M – line P col Q]")
├── Paste
├── Magic Paste                     (Ctrl+Alt+V, unchanged)
├── ──────────
├── Start Selection                 (F8; was Toggle Extend Selection Mode)
├── Complete Selection              (Shift+F8; new)
├── Reselect                        (Ctrl+Shift+F8; new)
├── Go to Start of Selection        (Alt+Shift+F8; new)
├── Go to End of Selection          (new)
├── Extend Selection Mode           (Insert+F8; was F8; preserves the mode)
├── ──────────
├── Select Line
├── Select Paragraph
├── Select Block
├── Expand Selection
├── Shrink Selection
├── Select Chunk                    (Ctrl+Space; new; replaces word_prediction on Ctrl+Space; word_prediction moves to Ctrl+.)
├── ──────────
├── Find
├── Find Next
├── Find Previous
├── Find All Matches
├── Replace...
├── Go to Line...
├── ──────────
├── Move Entry Up
├── Move Entry Down
├── Promote / Demote
└── Duplicate Selection             (new; block-level copy)
```

**Insert menu (binding).** Adds Image, Math, Citation
placeholders that were §4.15 / §4.18 recommendations:

```
Insert
├── Heading
├── Subheading
├── ──────────
├── Link
├── Footnote
├── Endnote
├── Citation...                     (new; placeholder for 1.0)
├── Divider (Horizontal Rule)
├── ──────────
├── Image from File...
├── Image from Clipboard
├── Math Block (LaTeX)
├── Special Character...            (F2; promoted from Power Tools)
├── Date / Time                     (Alt+Shift+; — EdSharp parity)
├── ──────────
├── Task List Item
├── Sticky Note
└── Quick Text ▸                    (existing snippet submenu)
```

**Format menu (binding).** Adds Strip HTML / decode
entities / Quote / Unquote / keep unique / shuffle /
statistics on selection from §4.23 and §4.22:

```
Format
├── Character Case ▸
│   ├── UPPER
│   ├── lower
│   ├── Title
│   ├── Sentence
│   └── Toggle (Swap)
├── ──────────
├── Toggle Line Comment             (Ctrl+/)
├── Toggle Block Comment            (Shift+Alt+A)
├── Quote Lines                     (Ctrl+Q; new)
├── Unquote Lines                   (Ctrl+Shift+Q; new)
├── ──────────
├── Indent
├── Outdent
├── Tab to Spaces                   (new)
├── Spaces to Tab                   (new)
├── ──────────
├── Trim Trailing Whitespace
├── Normalize Whitespace
├── Trim Blanks                     (Ctrl+Shift+Enter; new)
├── ──────────
├── Sort Lines Ascending
├── Sort Lines Descending
├── Reverse Lines
├── Shuffle Lines                   (new)
├── Keep Unique Lines               (Alt+Shift+K; new)
├── Remove Duplicate Lines          (was; kept)
├── Number Items                    (Alt+Shift+N; new)
├── Order Items                     (Alt+Shift+O; new)
├── Reverse Items                   (Alt+Shift+Z; new)
├── ──────────
├── Hard Line Break                 (Ctrl+Shift+H; new)
├── Join Lines                      (Ctrl+Shift+J; was)
├── ──────────
├── Strip HTML Tags                 (new)
├── Decode HTML Entities            (new)
├── Encode HTML Entities            (new)
└── Statistics on Selection         (new; sum/mean/median/mode/stddev)
```

**Navigate menu (binding).** Adds the four cross-
Notebook verbs and the Navigator toggle:

```
Navigate
├── Go to Line...
├── Go to Bookmark
├── Go to Heading
├── Go to Link
├── ──────────
├── Go to Heading in Notebook       (new)
├── Go to Bookmark in Notebook      (new)
├── Go to Sticky Note in Notebook   (new)
├── Go to Tag                      (new)
├── Go to Misspelling              (add; was under Tools)
├── ──────────
├── Open Document Navigator         (F5; promoted; was Ctrl+Shift+O; Ctrl+Shift+O remains)
├── Open EPUB Navigator
├── Open YAML Structure Editor
├── ──────────
├── Quick Nav
├── Announce Navigator Position     (new; status-bar cell query)
└── Announce Selection State       (new; status-bar cell query)
```

**Search menu (binding).** Adds Saved Searches and
the in-notebook filter:

```
Search
├── Find
├── Find Next
├── Find Previous
├── Replace...
├── Find in Files
├── ──────────
├── Saved Searches...
├── Search Results Window           (toggle docked results)
├── Filter by Current Notebook      (checkbox on Find in Files)
└── Clear Search History
```

**View menu (binding).** Adds the docked-panel
toggles, drops the "Focus Mode" and "Reading Ruler"
ideas:

```
View
├── Toggle Soft Wrap
├── Auto Side-by-Side Preview
├── Show Tab Control
├── Wrap Find Searches
├── Start With No Document Open
├── ──────────
├── Preview
├── Preview Side by Side
├── Focus Preview
├── Browser Preview
├── ──────────
├── Entries                         (toggle docked Entries panel; new)
├── Sticky Notes                    (toggle docked Sticky Notes panel; new)
├── Search Results                  (toggle docked Search Results; new)
├── Spell Check List                (toggle docked Misspelling List; new)
├── ──────────
├── Status Bar Layout...
├── Show All Characters             (toggle)
└── High Contrast                   (toggle)
```

**Tools menu (binding).** Reorganizes into seven
clusters. The two-deep cap is enforced.

```
Tools
├── Command Palette                  (Ctrl+K; moved from Navigate)
├── ──────────
├── Writing & Language
│   ├── Word Count
│   ├── Spell Check
│   ├── Previous Misspelling
│   ├── Next Misspelling
│   ├── Misspelling List
│   ├── Thesaurus
│   ├── Dictionary Status
│   ├── Add to Document Dictionary
│   └── Ignore for Session
├── Reading & Dictation
│   ├── Read Aloud ▸
│   ├── Stop Reading
│   ├── Say Selected                 (Shift+Space; new)
│   ├── Read All                     (Alt+F8; new)
│   ├── Dictation ▸
│   ├── OCR Image
│   ├── OCR Clipboard
│   ├── OCR Screen
│   └── Describe Image
├── GLOW
│   ├── Audit Document
│   ├── Audit Selection
│   ├── Fix Document
│   └── Fix Selection
├── Comparison
│   ├── Compare Documents
│   ├── Next Difference
│   ├── Previous Difference
│   ├── Announce Current Difference
│   ├── Difference List
│   ├── Synchronized Navigation
│   ├── Difference Summary
│   ├── Copy Current Difference
│   └── Copy All Differences
├── Watch Folder
│   ├── Watch Folder Profiles...
│   ├── Watch Folder Queue...
│   └── Toggle Watch Folder
├── AI Assistant
│   ├── Use AI
│   ├── AI Status
│   ├── AI Detail
│   ├── AI Hub
│   ├── Ask Quill Chat
│   ├── AI Model and Connection
│   ├── Forget API Key
│   ├── Session Branches
│   ├── Writing Assistant
│   ├── Prompt Studio
│   ├── Agent Center
│   ├── Accessibility Tune-Up
│   ├── Rewrite Selection
│   ├── Summarize Selection
│   ├── Continue Writing
│   ├── Fix Grammar
│   ├── Train Writing Style
│   └── Writing Instructions
├── Power Tools ▸
│   ├── Power Tools...
│   ├── Pandoc Wizard
│   ├── External Tools...
│   ├── Macros ▸
│   ├── Snippets ▸
│   ├── Form Library ▸
│   └── Authoring & Automation ▸
├── Accessibility
│   ├── Accessibility Audit
│   ├── Keyboard Trap & Tab-Order Snapshot
│   ├── Validate Contrast
│   ├── Link Inventory & Alt-Text Catalog
│   ├── Inline Word Prediction (toggle)
│   ├── Auto-Format as You Type (toggle)
│   └── Smart Quotes (toggle)
└── Customize & Support
    ├── Preferences
    ├── Customize Menus
    ├── Profiles and Features
    ├── Status Bar Layout
    ├── Export and Back Up
    ├── Import or Restore
    ├── Keymap Editor
    ├── Export Keymap
    ├── Import Keymap
    ├── Reset Keymap
    ├── Notifications
    ├── Report a Bug
    ├── Save Diagnostics
    ├── Open Logs Folder
    ├── Open Diagnostics Folder
    └── Check for Updates
```

**Window menu (unchanged from §6):** standard Window
list, plus "Next Entry" / "Previous Entry" toggles
when the user opts in to "open entries in a tabbed
editor" in Preferences.

**Help menu (binding).** Adds the QUILL Key Primer:

```
Help
├── Contents
├── QUILL Key Primer                 (new; in-app quick reference)
├── Keyboard Reference (Printable)   (new; HTML/EPUB cheat sheet filtered by active profile)
├── Notebook Tour                    (new; first-run walkthrough of the Entries panel)
├── ──────────
├── Check for Updates
├── About QUILL
└── ──────────
    ├── Custom Profiles ▸
    └── Report a Bug
```

### 10.4 The 1.0 milestone — what lands, in what order

The plan is sequenced into four milestones, each of
which is reviewable on its own. Each milestone ends
with a green test suite and a green dialog-inventory
gate.

**Milestone 1: Selection announcements + EdSharp parity. COMPLETE.**
All eight EdSharp-parity selection commands shipped (commit 46032bd).
`tests/unit/ui/test_edsharp_selection_parity.py` passes (22 tests).

**Milestone 2: Notebook (Workspace) JSON + Entries
panel + Document Navigator upgrades (this is the
organization milestone).**

- New `quill/core/notebook_store.py` and
  `quill/core/schemas/notebook.json`.
- New `quill/ui/notebook_panel.py` for the docked
  Entries panel.
- New `quill/ui/notebook_navigator_page.py` for
  the Notebook tab in the Document Navigator.
- New status-bar cells: "Navigator: §3.2," "Goal:
  1,234 / 500 today," "Selection session: anchored
  at line 12."
- Five new commands in File and Tools menus
  (`file.new_notebook`, `file.new_notebook_from_folder`,
  `file.open_notebook`, `file.save_snapshot`,
  `file.manage_snapshots`).
- Four new commands in Navigate menu (cross-Notebook
  verbs).
- Saved Searches manager and the in-Notebook filter
  on Find in Files.
- The snapshot rename in `main_frame_menu.py` and
  `keymap.py`.
- `dialogs.md` updated for `new_notebook`,
  `open_notebook`, `manage_snapshots`,
  `saved_searches`. All four are
  `hardened_custom` per the dialog contract.
- The dialog-inventory snapshot is regenerated
  via `python -m quill.tools.dialog_inventory
  --write` and committed.
- `dialog_inventory.json` snapshot regenerated
  and staged.
- **Acceptance:** a screen-reader user can create a
  Notebook from a folder of 30 Markdown files, group
  the entries by directory, open one entry, jump to
  another via Navigate > Go to Entry, set a Goal of
  500 words, type until the status bar announces
  "Goal reached," save a Snapshot, close the Notebook,
  reopen it, and find the caret exactly where it
  was.

**Milestone 3: Format and Transform completeness
(this is the "Text Monkey PRO subset" milestone —
deliberately a subset, full Text Monkey is 2.0).**

- New helpers in `quill/core/format_ops.py`:
  `strip_html_tags`, `decode_html_entities`,
  `encode_html_entities`, `tab_to_space`,
  `space_to_tab`, `shuffle_lines`, `keep_unique_lines`,
  `trim_blanks`. All wx-free; covered by mypy in
  `quill\core`.
- New helper in `quill/core/stats.py`:
  `selection_statistics(text) -> dict` returning
  `count`, `sum`, `mean`, `median`, `mode`,
  `stddev` for the numbers in `text`.
- New menu commands per the Format menu in §10.3.
- Promote `Special Character` to Insert and bind F2.
- Promote `quote_lines` / `unquote_lines` to Edit
  and bind Ctrl+Q / Ctrl+Shift+Q.
- Promote `select_chunk` to Edit and bind
  Ctrl+Space. Move `word_prediction` to Ctrl+.
- **Acceptance:** a user can paste HTML into a
  document, select it, run Format > Strip HTML Tags,
  and see plain text; select a column of numbers
  and run Format > Statistics on Selection to get a
  spoken report; select a Python comment block and
  press Ctrl+Q to comment it, Ctrl+Shift+Q to
  uncomment it.
- **Multi-cursor and rectangular selection are
  NOT in this milestone.** The 2.0 design is
  §10.7. The 1.0 plan does not paint us into a
  corner because the single-range shim in
  §10.7.2 keeps every existing consumer
  compiling; the new commands are feature-flagged
  behind `feature.multi_caret_v2`.

**Milestone 4: Menu consolidation + keymap parity
(this is the "ship it" milestone — every binding
documented, every menu flat at two levels).**

- Land §10.3 in full: every menu reorganized, every
  submenu capped at two levels, every verb
  documented in `dialogs.md` and `menus.md`.
- `python -m quill.tools.dialog_inventory --write`
  runs clean.
- `python -m quill.tools.menu_lint` (new tool) runs
  clean.
- `python -m quill.tools.quillin_lint` runs clean.
- All four §10.1 / §10.2 / §10.3 test files pass.
- The full `pytest tests\unit\tests\stability`
  suite passes (with the two known hangs ignored
  per the standing rules).
- The `tests/unit/ui/fixtures/main_frame_public_surface.json`
  is regenerated via
  `python -m quill.tools.ui_surface --write` and
  committed.
- **Acceptance:** the `menus.md` companion document
  in the repo root describes the final menu
  layout, every command is bound, every dialog is
  in the inventory, every selection verb is
  announced.

### 10.5 What is explicitly out of scope for 1.0

The following are not 1.0 work and are not part of
this plan. They are listed here so the plan is
reviewable as a single bounded piece:

- Backlinks panel / vault graph (Obsidian-style);
  axe-core / Nu Html Checker; BITS Whisperer
  top-level promotion; GLOW watch-action binding
  (WATCH-8); the AX-A..F Accessibility Agents
  workstream; multi-cursor / column select;
  clipboard history panel; full Ulysses library
- Reading Ruler, Focal Mode, Reading Mode. All
  withdrawn per the user's direction. The Document
  Navigator is the canonical structure surface.
- Live OCR (OCR-1/3), live device-login AI (AI-19),
  sensitivity-aware dictation (SET-2), advisory
  agent mode (AGENT-1). All require a real Windows
  runtime and stay "In progress" per the standing
  rules.

### 10.6 Review checklist for the plan

The user will review the plan against these eight
questions; the answers must be unambiguous:

1. **Does F8 now announce an anchor?** Yes. F8 is
   `edit.start_selection`. It sets
   `self._selection_anchor`, calls
   `line_column_for_position`, and announces
   "Selection started at line N, column M."
2. **Does arrow-down after F8 announce a growing
   region?** No, by design — the EdSharp model is
   silent during roam. The *anchor* is announced at
   F8 time, the *region* is announced at Shift+F8
   time. (For users who want a live growing-region
   announcement, the Insert+F8 mode toggle still
   works and announces anchor and region spans.)
3. **Is "Sheets" gone?** Yes. Replaced with
   "Entries" in every menu, dialog, status-bar
   cell, and JSON field.
4. **Is there a reading ruler or focal pane?**
   No. Both withdrawn. The Document Navigator
   (F5) is the canonical structure surface.
5. **Are the EdSharp keys exactly where they were
   in EdSharp?** F8 = Start Selection. Shift+F8 =
   Complete Selection. Ctrl+Shift+F8 = Reselect.
   Alt+Shift+F8 = Go to Start of Selection.
   Ctrl+F8 = Copy All. Ctrl+Shift+A = Unselect
   All. Shift+Space = Say Selected. Alt+F8 =
   Read All. (Three of the six are new in 1.0; the
   user gets the same key, the same verb, the same
   announcement as EdSharp.)
6. **What is in 1.0 vs 2.0?** 1.0 is Milestones 1–4
   above. 2.0 is §10.5 above plus the multi-cursor
   and rectangular-selection design in §10.7.
   There is no "maybe later" — every item is
   either in 1.0, in 2.0, or in §10.5 as a deferral
   with a reason.
7. **What is the test plan?** Milestone 1 is complete:
   `tests/unit/ui/test_edsharp_selection_parity.py` (22 tests, passing).
   Milestone 2 adds
   `tests/unit/ui/test_notebook_store.py`,
   `tests/unit/ui/test_notebook_panel.py`,
   `tests/unit/ui/test_notebook_navigator_page.py`.
   The 2.0 multi-cursor work adds the ten test
   files in §10.7.9.
8. **How does multi-cursor not break the screen
   reader?** §10.7.3 — three obligations: (1)
   always speak one caret at a time, (2) every
   command is deterministic and idempotent with a
   single announcement per action, (3) no
   "primary/secondary" visual language. The full
   design is §10.7; the tests are §10.7.9.

### 10.7 Multi-cursor and rectangular selection (2.0 design)

The plan keeps multi-cursor and rectangular
selection as a 2.0 feature (still listed in
§10.5). This subsection is the design we will
implement in 2.0 — screen-reader-first, no
visual metaphor, no parity theater. The job of
this subsection is to lock the design now so
the 1.0 work does not paint us into a corner
(especially around selection model, command
routing, and announcement surface).

#### 10.7.1 Why this is not 1.0

The current selection model is
`tuple[int, int]` (start, end) in
`quill/core/selection.py` and a single
`_extend_selection_anchor` in
`quill/ui/main_frame.py:945`. Every consumer —
copy, cut, paste, paste-with-source, magic-paste,
move-line-up/down, comment toggle, sort,
reverse, dedupe, every transform — assumes one
range. Promoting that to a list of ranges
silently breaks the entire command surface.
The honest path is to land the binding spec
above, then build multi-cursor on top of it
as a 2.0 milestone, with its own migration and
its own test plan. Same reasoning the plan
already uses for the AX workstream and BITS
Whisperer.

#### 10.7.2 Selection model (2.0)

Promote the single range to an ordered list of
disjoint, non-overlapping ranges called
**`SelectionSet`**. The primary caret is the
range that contains the focus point; every
other range is a **secondary caret** (no
"primary" vs "secondary" rhetoric in the
audible surface — just "caret 1 of 3, line N,
column M" when the user moves).

```python
# quill/core/selection_set.py (2.0, new file)
@dataclass(frozen=True, slots=True)
class Selection:
    start: int
    end: int  # inclusive-exclusive

class SelectionSet:
    primary: Selection
    others: tuple[Selection, ...]  # sorted by start
    anchor: int | None  # set by F8; refers to a position, not a range
```

Rules:

- All ranges are normalized (start <= end) and
  merged if they overlap when added
  (no two ranges that touch or overlap).
- The primary caret is the range that contains
  the focus point; on tie, the one that ends
  latest wins. The other ranges are read in
  start order for "next caret" navigation.
- `anchor` is **not** a range. It is the
  position set by F8 (Start Selection). When
  the user types or arrows, the *primary*
  range grows from `anchor`; secondary ranges
  do not grow. This is the EdSharp model, just
  extended to N primary regions. (See §10.1.)
- `quill/core/selection.py` keeps the existing
  `word_span` / `line_span` / `paragraph_span` /
  `sentence_span` / `block_span` / `expand_selection`
  / `shrink_selection` / `selection_scope` helpers;
  they now operate on a single `Selection` and
  return a `Selection`. New
  `selection_set_scope(set) -> list[str]` returns
  the scope of every range for the announcement
  surface.
- The single `tuple[int, int]` API stays as a
  **shim** that returns `(primary.start,
  primary.end)`. Every existing consumer keeps
  compiling; commands that touch a selection
  get a `SelectionSet`-aware variant behind a
  feature flag (`feature.multi_caret_v2`).

#### 10.7.3 Screen-reader-first model

The "screen reader first" rule is the reason
multi-cursor is a bigger lift than it is in
VS Code, and the reason it is the right lift.
The design has three obligations:

**1. Always speak one caret at a time.** The
focused caret is the **only** caret the screen
reader hears while it moves. Secondary carets
are silent during arrow / type / mouse motion.
The user can press a dedicated command
(`selection.speak_selection_set`,
**`Alt+Shift+Space`**, see §10.7.6) to hear
"3 carets. Caret 1 of 3: line 12, column 4.
'Hello world, 22 characters.' Caret 2 of 3:
line 14, column 8. 'Second line.' Caret 3 of 3:
line 16, column 1. 'Third line.'" This is the
one and only time the user hears about all
carets at once. The user can also press
`selection.next_caret` /
`selection.previous_caret` to step through
carets; stepping announces the new primary
caret the same way a single caret does today.

**2. Selection verbs are deterministic and
idempotent.** Copy, cut, delete, transform,
indent, comment toggle, sort, reverse, dedupe
all operate on the **`SelectionSet` as a
unit**, in a single undo entry, with a single
announcement. The rule is:

- "Operate on every caret, in parallel,
  against the original text snapshot." This
  is the VS Code rule; it is also the only
  rule that does not produce surprising
  results when ranges overlap a region that
  shifted because of an earlier caret's
  action.
- The announcement is the **count** of
  affected ranges and a one-line summary, not
  the full text of every region. "Replaced
  text in 3 places. 14 characters." not
  "Replaced 'Hello world' in caret 1 with
  'Goodbye world', replaced 'Second' in caret
  2 with 'Third'..." Multi-cursor is a
  power-user tool, not a screen-reader
  narrator.
- If the user explicitly wants per-caret
  speech, they call `selection.speak_affected`
  (**`Alt+Shift+'`**, see §10.7.6), which is
  the same verb broken down caret by caret.

**3. There is no "primary/secondary" visual
language.** There is a **focused caret** (the
one the screen reader is speaking), and there
are **other carets** (silent). The status-bar
cell shows "Caret 1 of 3" when the user has
asked for that cell. There is no "leader"
caret color, no "ghost caret" rendering, no
"inactive selection" gray, no blinking other
carets. The status cell is the only place
"of N" appears, and the user can hide it.

These three rules are what make the feature
ship-able to a screen-reader-first audience.
They are also the source of most of the test
matrix in §10.7.7.

#### 10.7.4 Adding and removing carets

**Add caret below**
(`selection.add_caret_below`):
**`Ctrl+Alt+Down`**. Adds a caret one visual
row below the current caret, in the same
column (or the last column of the shorter
line if the row is shorter). Announces
"Caret 2 of 2, line N, column M." If the
focused caret is already on the last visual
row, the command does nothing and announces
"No row below."

**Add caret above**
(`selection.add_caret_above`):
**`Ctrl+Alt+Up`**. Mirror of the above.

**Add carets to all occurrences**
(`selection.add_caret_to_all_occurrences`):
**`Ctrl+Shift+L`** (the VS Code binding, kept
for cross-editor muscle memory). If a
selection is active, every match of the
selected text in the document gets a caret.
If no selection, the current word is used.
Announces "3 carets. Caret 1 of 3: line 5."
The first caret is the original; matches are
sorted by document order. Empty-document and
zero-match cases announce "No matches" and
the caret count is unchanged.

**Add carets to line ends**
(`selection.add_caret_to_line_ends`):
**`Ctrl+Alt+L`**. Adds a caret at the end of
every line in the current selection. No
selection = every line in the document.
Announces "Added caret to N line ends."

**Remove focused caret**
(`selection.remove_focused_caret`):
**`Ctrl+Alt+K`** (was free; matches the
"kill caret" mnemonic). If only one caret
remains, the command does nothing and
announces "1 caret. Cannot remove." Otherwise
announces "Caret removed. 2 carets remain."

**Remove all secondary carets**
(`selection.clear_secondary_carets`):
**`Escape`** (the existing Escape path is
reused; see below). Collapses back to a
single caret at the position of the focused
caret. The single caret is now the primary,
and the SelectionSet is empty (`others = ()`).
Announces "1 caret."

The Escape key already does three things
today (cancel extend-selection mode, cancel
find, close dialogs). The 2.0 Escape
resolution is: **dialog > rectangle >
multi-caret collapse > extend-selection
mode > find bar**. The first matching
context wins. This
is the same priority rule EdSharp and
Notepad++ use. Documented in the help
cheatsheet and the
`tests/unit/ui/test_escape_priority.py` test.

#### 10.7.5 Stepping between carets

**Next caret**
(`selection.next_caret`): **`Alt+Down`**
clashes with `navigate.next_structure`
(`quill/core/keymap.py:32`). The 2.0
resolution is: **Alt+Down is context-aware**.
When the SelectionSet has more than one
caret, Alt+Down is `selection.next_caret` and
Alt+Up is `selection.previous_caret`. When
the SelectionSet has one caret, Alt+Down is
`navigate.next_structure`. The screen reader
announces the resolved binding: "Next caret.
Caret 2 of 3, line 14, column 8." vs.
"Next structure: heading 2, 'Methods'." This
is consistent with the EdSharp /
`expand_selection` model: structural
navigation is the single-caret default;
multi-caret is an opt-in mode that
temporarily takes over the arrow keys.

**Previous caret**
(`selection.previous_caret`): the mirror
binding.

**Caret N of M**
(`selection.announce_caret_position`):
**`Alt+Shift+P`** (P for Position; Alt+Shift+C
is used by Quick Column Caret, see §10.7.7).
Says the focused caret's line, column, "of N,"
and the count of characters from the start
of the document.
The same announcement the single-caret
status-bar cell already gives, extended for
multi-caret.

The behavior of Home, End, Page Up, Page
Down, Ctrl+Home, Ctrl+End, the word /
paragraph / sentence / block span commands
(§10.1) is: **apply to every caret, in
parallel, against the original text
snapshot**. The focused caret's announcement
is spoken; the other carets move silently.
The same rule as transform operations.

#### 10.7.6 Selection-set speech and copy

**Speak selection set**
(`selection.speak_selection_set`):
**`Alt+Shift+Space`**. Reads the count of
carets, then reads each caret in document
order: caret number, line, column, and the
selected text (or the word at the caret if
no selection). This is the only command that
enumerates all carets; it is the
"what is multi-cursor doing right now"
command.

**Speak affected carets**
(`selection.speak_affected`):
**`Alt+Shift+'`** (the apostrophe key).
Reads only the carets that were affected by
the last multi-caret command. After a
multi-caret paste that replaced text in 3
places, this command says "Caret 1: was
'Hello', now 'Goodbye'. Caret 2: was
'World', now 'There'. Caret 3: was empty,
now 'End'." This is the screen-reader
equivalent of VS Code's
`editor.action.showHover` for multi-cursor
results.

**Copy selection set**
(`selection.copy_selection_set`): bound to
**`Ctrl+Shift+C`** (already
`edit.copy_with_source` in the default
keymap; this is the **disambiguated** form).
Resolution: if the clipboard target is "for
email" (`edit.copy_selection_for_email`,
`Ctrl+Shift+Grave, C`), behavior is
unchanged. Otherwise, copy concatenates the
selected text from every caret in document
order, joined by `\n` (the rule every
multi-cursor editor uses; VS Code, Sublime,
Emacs, IntelliJ all do this). Single-caret
behavior is identical to today. The
announcement is "Copied from N carets. 47
characters." (or "Copied 12 characters."
when N=1).

**Cut, delete, paste** follow the same
rule. Paste places the same text at every
caret (the standard multi-cursor paste
semantic). Indent, outdent, comment toggle,
case transforms, sort, reverse, dedupe,
shuffle, join, hard wrap, number lines —
all operate on the SelectionSet as a unit
with a single undo entry and a single
announcement.

#### 10.7.7 Rectangular (column / box) selection

Rectangular selection is the older feature
(present in Notepad++ via Alt+drag and
Shift+Alt+arrows, in Emacs via `rectangle-mark-mode`,
in Sublime via `editor.action.insertCursorAbove`).
For QUILL, the model is the same SelectionSet,
just sourced differently. There is no
"column" concept in the user-facing
vocabulary; the verb is **"select
rectangle"** and the result is a
SelectionSet of N ranges, one per line in
the rectangle.

**Start rectangle selection**
(`selection.start_rectangle`):
**`Alt+Shift+` `**`** (Alt+Shift+backtick) —
the same chord Word and Visual Studio use
for column-select. Sets the rectangle anchor
at the current caret position. Announces
"Rectangle started at line N, column M.
Move with arrow keys."

**Extend rectangle**
(arrow keys while rectangle mode is on):
**`Shift+Arrow`** keys extend the rectangle
in the obvious direction. The SelectionSet
grows by one range per visual line covered.
Each line gets its own range, clamped to the
rectangle's start and end columns. Lines
shorter than the rectangle's end column
contribute an empty range (a zero-width
caret at the line end). The screen reader
**does not enumerate** ranges as the user
arrows; it says "Rectangle: 5 lines, 4
columns." once and then stays silent until
the rectangle is committed, replaced, or
the user calls `selection.speak_selection_set`.

**Commit rectangle**:
**`Enter`** or **any non-arrow key** (typing,
Escape to cancel, or a command). Enter
collapses the SelectionSet to the current
set of N ranges; further arrows behave
normally. The user can then type, paste,
indent, or transform.

**Cancel rectangle**:
**`Escape`** (priority rule from §10.7.4:
rectangle > multi-caret > extend-selection
> find). The anchor is discarded; the
SelectionSet collapses to a single caret at
the original anchor position.

**Quick column caret** (the Alt+click
equivalent, screen-reader-first):
**`Alt+Shift+C`** then arrow keys. This is a
shortcut for users who do not want to commit
to rectangle mode: the caret moves as a
column-only caret, leaving a trail of
secondary carets in the rectangle shape,
without ever entering "rectangle mode" as a
named state. Announces "Column caret, 4
lines." Each subsequent Alt+Shift+Arrow
moves the focused caret and re-anchors the
others. **`Alt+Shift+0`** (zero) drops the
column and returns to a single caret.

The visual surface of rectangular selection
is intentionally minimal: the existing
selection highlight extends, plus a status
cell "Rectangle: 5 lines, 4 columns." There
is no overlay rectangle, no shaded band, no
"column ruler." The status cell is the only
new chrome, and it is the same cell the
single-caret status bar already shows.

#### 10.7.8 What this changes in the existing code

Files touched in 2.0 (the full list — every
file is `quill/` or `tests/`, no new top-level
modules):

- `quill/core/selection.py` — keep the
  single-range helpers; add `Selection` and
  `SelectionSet` as the new types.
- `quill/core/selection_set.py` (new) —
  `SelectionSet` with merge, sort, primary
  resolution, and `selection_set_scope`.
- `quill/core/feature_command_map.py` —
  add `feature.multi_caret_v2`; gate the
  new command set behind it for the 1.0 →
  2.0 transition.
- `quill/core/keymap.py` — add the 12 new
  bindings (six caret-add / remove / speak,
  four caret-step / speak, one column caret,
  one start-rectangle). All behind the feature
  flag. The 1.0 keymap is unchanged.
- `quill/ui/main_frame.py:945` — replace
  `self._extend_selection_anchor: int | None`
  with `self._selection_set: SelectionSet`.
  Keep `_extend_selection_anchor` as a
  derived property that returns
  `self._selection_set.anchor`. The 7 test
  sites in
  `tests/unit/ui/test_main_frame_navigation.py`
  (lines 1275, 1303, 1316, 1330, 1690, 1704,
  1715) keep passing because the property
  preserves the existing API.
- `quill/ui/main_frame.py:3530–3701` — the
  `_handle_extend_selection_key` /
  `_move_extend_selection_caret` / etc.
  path keeps working for the single-primary
  case. New `MultiCaretMixin` (in
  `quill/ui/multi_caret.py`, new) handles
  the N-caret paths.
- `quill/ui/main_frame_menu.py` — add the
  new menu items under **Edit → Carets** and
  **Edit → Rectangle** submenus (both
  behind the feature flag).
- `quill/ui/main_frame_selection.py` —
  `SelectionMarksMixin` keeps its current
  API; the new verbs live in
  `MultiCaretMixin`.
- `quill/ui/dialog_inventory.py` — the
  multi-caret cheatsheet dialog (if any) is
  classified `native` (a `wx.Dialog` showing
  a `wx.TextCtrl` of the new keymap, per the
  dialog rules).
- `tests/unit/ui/fixtures/main_frame_public_surface.json` —
  regenerated via
  `python -m quill.tools.ui_surface --write`
  to include the new methods.
- `dialogs.md` — the multi-caret cheatsheet
  row is added (one row, one binding).

#### 10.7.9 Test plan for 2.0

The test plan is a direct map of the design
obligations in §10.7.3:

- `tests/unit/core/test_selection_set.py` —
  merge, sort, primary resolution, anchor
  preservation, overlap rejection.
- `tests/unit/core/test_selection_set_scope.py` —
  scope reporting for the announcement
  surface (one caret, N carets, mixed
  scopes).
- `tests/unit/ui/test_multi_caret_add_remove.py` —
  add-below, add-above, add-all-occurrences,
  add-line-ends, remove-focused,
  clear-secondary, Escape priority.
- `tests/unit/ui/test_multi_caret_step.py` —
  next/previous caret, context-aware
  Alt+Down resolution (single vs multi).
- `tests/unit/ui/test_multi_caret_speech.py` —
  `speak_selection_set`,
  `speak_affected`, the "1 of 3" announcement
  shape, the "Copied from N carets"
  announcement shape, status-cell content.
- `tests/unit/ui/test_multi_caret_transform.py` —
  every transform (sort, reverse, dedupe,
  indent, outdent, comment toggle, case
  transforms, join, hard wrap, number lines,
  shuffle, keep-unique) operates on the
  SelectionSet as a unit with one undo entry
  and one announcement.
- `tests/unit/ui/test_multi_caret_paste.py` —
  paste places the same text at every caret;
  paste when clipboard is multi-line does
  not collapse to one caret; undo restores
  every caret's pre-paste text.
- `tests/unit/ui/test_rectangle_selection.py` —
  start, extend, commit, cancel, column-caret
  shortcut, short-line clamping, status-cell
  shape, the Escape priority rule with
  rectangle > multi-caret > extend-selection
  > find.
- `tests/unit/ui/test_escape_priority.py` —
  the unified Escape resolver from §10.7.4.
- `tests/unit/ui/test_multi_caret_announcements.py` —
  the three obligations of §10.7.3 in one
  matrix: silent-other-carets-during-motion,
  single-spoken-announcement-per-action,
  speak_selection_set on demand.
- `tests/unit/ui/test_dialog_inventory.py` —
  the multi-caret cheatsheet dialog is
  registered with classification `native`.

#### 10.7.10 What this does **not** ship in 2.0

- **No multi-cursor in the Document Navigator
  or the Entries panel.** Carets are an
  editor-internal concept; they do not
  appear in the structure surface, the
  filter surface, the sticky-notes surface,
  the Notebook tabs, or the status bar of
  the editor-host window.
- **No multi-cursor across Notebook
  Entries.** Carets are scoped to a single
  document. The "add caret to all
  occurrences" command operates inside the
  active document only. Cross-Entry
  multi-cursor is deferred to a future 2.x
  milestone.
- **No multi-cursor for sticky-note
  captures.** The sticky-note capture buffer
  (`Ctrl+Shift+Grave, N`) remains a
  single-position capture; multi-position
  sticky notes are a separate feature with
  its own dialog contract.
- **No multi-cursor for AI suggestions.**
  The AI ghost-suggestion flow (§8.6) accepts
  one position at a time. Multi-position AI
  is deferred.
- **No multi-cursor in find/replace
  results.** Find-all-matches (`Alt+F3`)
  stays a list of single-position results
  in the Find Results panel; it is not a
  multi-caret launcher.
- **No "primary caret" color, "ghost caret"
  rendering, or "inactive selection"
  highlight.** The screen-reader-first rule
  in §10.7.3 is enforced by the absence of
  these affordances, not just by their
  silence.
- **No clipboard history panel.** A
  multi-cursor + clipboard history combo is
  a 2.x or 3.0 design; this plan keeps the
  two features decoupled.

This subsection is the design the 2.0
milestone will implement. The 1.0 plan
above is **unchanged** by it; the only
1.0 consequence is the selection model
must keep the shim in §10.7.2 so the 2.0
work is a feature-flagged addition, not a
breaking change.

---

## 11. The Magical Layer — proposals for 1.5 and 2.0

Every idea in this section passes the QUILL bar: it
must be operable entirely by keyboard, it must have
a spoken outcome, and it must not break any existing
dialog contract. These are not incremental features.
Each one changes what it *feels like* to use QUILL.
Priority order within each tier is by implementation
cost and likelihood of delight.

### 11.1 Delta narration — speak where you arrived, not the grid

**What.** Replace coordinate-only position announcements
("line 42, column 5") with a context sentence: "Moved
down 3 lines to: 'She looked up slowly.'" The
announcement leads with the fragment of text at the new
caret position (up to 8 words, trimmed at word boundary)
and appends the line number as a secondary hint. The
fragment is sourced from `editor.GetRange(pos, pos + 60)`
narrowed to the next word boundary.

**Why it is magical.** The screen-reader user hears the
document, not a spreadsheet. "Moved to 'The reversal
was unexpected'" is instantly meaningful. "Line 42,
column 1" is not. Every navigation command — Page Down,
next heading, jump to bookmark — becomes a sentence
about the writing instead of a grid coordinate. This
is the single highest-leverage change to QUILL's
announcement layer.

**Where it lives.** An opt-in toggle in Preferences >
Announcements: "Position speech: fragment (default),
coordinates, both." A per-profile setting so a developer
using QUILL for code can stay on coordinates.

**Implementation.** One new function
`announcement_fragment(text, pos, width=60) -> str`
in `quill/core/marks.py`. Replace the coordinate
format string in `_announce_selection_scope` and
`_announce_caret_position`. No other changes.

---

### 11.2 Structural earcons — navigate by sound, not speech

**What.** A set of short, distinct audio icons (non-TTS)
played at structural boundaries:

- Crossing from one heading section to another: a low
  two-note chime.
- Landing on a misspelling: a short, quiet tick.
- Landing on a GLOW annotation: a slightly longer tick
  in a different pitch.
- Entering a heading: a brief rising tone scaled to the
  heading level (H1 is lowest; H6 is highest).
- Opening an AI suggestion: a soft ascending arpeggio.

**Why it is magical.** Earcons complement TTS without
competing with it. A user scanning fast with arrow keys
does not want a full sentence announcement per line; they
want a spatial audio cue that says "something here."
Earcons are to QUILL what visual underlines and colors
are to sighted users: a pre-attentive signal that
narrows attention before the speech channel activates.

**Where it lives.** Tools > Accessibility > Sound Cues
(toggle, plus a "Sound Cue Levels..." dialog). Each cue
type is individually toggle-able. Volume is a percentage
of the system default. All cues respect system mute.
A "Preview" button in the dialog plays all cues in
sequence.

**Implementation.** `quill/platform/windows/earcon.py`
(new, ~80 LOC): wrap `winsound.PlaySound` with a
non-blocking queue. Each earcon is a short WAV bundled
in `quill/resources/earcons/`. The trigger sites are
the same hooks that fire `_announce_caret_position`
and `_announce_selection_scope`.

---

### 11.3 "Ask QUILL" — natural language document query

**What.** QUILL key + Q opens a single-line prompt.
The user types a question about the current document
or Notebook and hears a spoken one-sentence answer:

- "How many words in the introduction?" → "Introduction:
  847 words, reading time 4 minutes."
- "Where did I last write about memory?" → "Last mention
  of 'memory': line 312, section 3.2 'The aftermath'."
- "What headings are in chapter three?" → "Chapter Three
  has 4 sub-headings: 'The setup', 'The reversal'…"
- "What is my goal progress?" → "Goal: 278 of 500
  words today. 44% complete."

The answer is computed from the document index, the
Notebook JSON, and the existing Quick Nav primitives.
The AI layer handles questions the index cannot answer
(and only then, under the existing consent gate).

**Why it is magical.** No other screen-reader-first
editor lets the user ask a question about their document
in plain English and hear the answer in one second. This
is not a chat; there is no back-and-forth. It is a
query oracle with a one-shot answer. The distinction
matters: a chat UI imposes a conversation metaphor; a
query oracle respects the user's time.

**Where it lives.** A new command `tools.ask_quill`
(QUILL+Q) that opens a `wx.TextEntryDialog`
(classified `native`) with a single text field. The
response dialog is a `wx.MessageDialog` that also
copies the answer to the clipboard. Query history is
per-Notebook and accessible via Search > Saved Queries.

---

### 11.4 Notebook vocabulary — the project dictionary

**What.** Every Notebook carries a vocabulary list:
words the user has added as project-specific (character
names, place names, technical terms, invented words).
The spell checker and GLOW respect this list. Three
commands:

- "Add to Notebook Dictionary" (in the spell-check
  context actions and the right-click context menu):
  promotes a word from session scope to Notebook scope.
- "Notebook Vocabulary..." (Tools > Writing & Language):
  opens a `wx.Dialog` with the full project word list,
  add/remove, and import from a text file.
- "Dictionary Status" (already exists) shows the
  count of project words alongside the system and
  session word counts.

**Why it is magical.** A novelist who writes "Astryn"
as a character name should never see it flagged as a
misspelling after the first time they add it. A
technical writer should add acronyms once and forget.
Scrivener has "project replace" for phrases; QUILL has
a cleaner, spell-check-integrated vocabulary that
persists with the Notebook JSON. The first time a user
adds a word to their Notebook dictionary and hears
"Added 'Astryn' to My Novel vocabulary" they
understand immediately that QUILL is managing context,
not just words.

**Implementation.** A `vocabulary: []` list in the
Notebook JSON schema (`quill/core/schemas/notebook.json`).
The `enchant` pipeline in `quill/core/spell_check.py`
gains a `project_words` parameter. The context menu
wiring is the same as "Add to Document Dictionary."

---

### 11.5 Read Aloud proofreading mode — active, not passive

**What.** A new mode activated by "Read Aloud >
Proofread Document" (or Ctrl+Shift+R). In this mode:

1. Read Aloud narrates one sentence at a time at the
   normal voice rate, then pauses.
2. After the pause, QUILL announces the available
   actions: "Space: continue. R: replace. M: mark.
   N: add note. Escape: exit."
3. The user acts or continues.
4. After the full document is read, QUILL announces:
   "Proofread complete. 3 marks, 1 replacement, 47%
   of document reviewed."

A status-bar cell "Proofread: 47%" updates in real
time. Reviewed sentences are tracked in the Notebook
session (not persisted). The "R: replace" path opens
an inline one-line replacement prompt (a
`wx.TextEntryDialog`, classified `native`) pre-filled
with the current sentence.

**Why it is magical.** Read Aloud today is a passive
listener experience. The proofreading mode makes it
an active editing workflow. A blind user hears their
own words read back and can fix them without switching
context, searching for the caret position, or opening
a find/replace dialog. This is how professional
audiobook narrators proof their scripts, adapted for
QUILL's stock-control architecture.

**Implementation.** A new `ProofreadSession` class in
`quill/core/read_aloud.py` that owns the sentence
iterator, the mark list, and the action dispatcher.
The action keys are handled in a modal loop in
`quill/ui/main_frame_read_aloud.py` (new mixin, ~120
LOC). No new dialogs beyond the replacement prompt.

---

### 11.6 AI welcome-back summary on Notebook open

**What.** When AI is enabled and a Notebook has not
been open for more than 4 hours, opening it triggers
a one-sentence spoken summary:

"Last session: Chapter 3, 847 new words. Today's
goal: 500 words. You stopped at: 'She looked up
slowly.'"

The summary is generated from the Notebook JSON (no
network call: last-session word delta, Goal state,
last caret fragment from §11.1). If the AI provider
is available and the user has opted in, a second
sentence adds AI context: "The last section you
worked on discusses grief and memory."

**Why it is magical.** Every morning a novelist opens
QUILL and hears exactly where they left off. No
scrolling, no searching, no "where was I?" The welcome-
back summary is two seconds of audio that re-creates
the context a sighted user gets by scanning the
screen. It is the difference between QUILL being a
tool and QUILL being a working partner.

**Where it lives.** Preferences > AI > "Welcome-back
summary" toggle (default: off). Per-Notebook override
in the Notebook settings dialog.

---

### 11.7 Silent Mode — defer all speech to the OS screen reader

**What.** A status-bar toggle (or QUILL+F12) that
suppresses all QUILL-originated TTS announcements and
custom spoken output. In Silent Mode, QUILL focuses
entirely on providing correct ARIA roles, names,
states, and `wx.Accessible` event notifications so
NVDA, JAWS, or Narrator can narrate everything
natively.

Silent Mode does *not* disable keyboard access,
dialog contracts, or status cells. It only quiets
QUILL's own voice. A user who prefers their screen
reader's voice, grammar, and verbosity level over
QUILL's custom announcements gets a fully accessible
experience without both systems competing for the
audio channel.

**Why it is magical.** Most accessible software
forces users to choose between the app's narration
and the screen reader. QUILL's existing
`platform/windows/prism_bridge.py` already abstracts
the TTS channel; Silent Mode just sets the bridge to
a no-op stub. The screen reader then takes over with
zero integration work. This is the design complement
of the announcement grammar system: QUILL either
speaks beautifully in its own voice, or it steps
aside and lets the screen reader speak in its voice.

**Implementation.** A `silent: bool` flag on
`PrismBridge`. When set, all `announce(...)` calls
in the bridge return immediately without speaking.
`wx.Accessible` events continue to fire. The
status-bar cell changes label to "Silent" when on.
~10 LOC.

---

### 11.8 The QUILL key situation report

**What.** When the user presses the QUILL key and
holds it (or presses QUILL key + Space), QUILL speaks
a situation report:

"Chapter Three: The reversal. 312 words. Goal: 278
of 500 today. 1 nearby misspelling."

The report contains: the current heading and section,
the section word count, the Goal progress (if a Goal
is active), and the nearest annotation within 200
characters (misspelling, GLOW note, or sticky note).
One announcement, everything the user needs to know
about where they are.

**Why it is magical.** A sighted user glances at the
status bar and the outline panel and knows their
context in a fraction of a second. A screen-reader
user currently has to query each piece of information
separately. The situation report collapses that into
a single, predictable spoken phrase. It becomes
muscle memory: "I'm disoriented, QUILL+Space." The
answer is always the same shape, always complete,
always under 3 seconds.

**Where it lives.** A new command
`view.speak_situation_report` (QUILL+Space, or a
configurable QUILL key chord). One line in the QUILL
key dispatch table. Implementation draws on
`line_column_for_position` (marks.py), the Quick Nav
index (navigate.py), and the Goal state (notebook
JSON). ~30 LOC in `main_frame_view.py`.

---

### 11.9 Announcement grammar templates

**What.** The spoken output of every QUILL navigation
and action command is currently hard-coded in the
announcement layer. Exposing the format strings as
user-customizable templates would let power users
define how QUILL speaks to them:

- Default: "Heading 2: Methods — 847 words"
- Custom: "H2 Methods, 847"
- Developer: "§2 Methods [847]"

Template tokens for each announcement type (position,
heading, selection, annotation, goal) are documented
in Help > Announcement Grammar Reference. Templates
are stored in the Notebook JSON under `"announcement_overrides"`.
Edited in a new "Announcement Grammar" dialog in
Tools > Customize & Support.

**Why it is magical.** A legal writer, a novelist,
a programmer, and a student all want QUILL to speak
differently. The template system lets QUILL adapt to
each without requiring a feature flag per niche. It
is the meta-feature that makes every other
announcement customizable by the user, not by the
developer.

---

### 11.10 "Speak what you passed" on fast navigation

**What.** When the user presses Page Down or
Ctrl+Down multiple times in quick succession (within
600ms between keypresses), QUILL accumulates the
moves and, when the user pauses, speaks a summary
instead of enumerating every intermediate position:

"Moved down 8 paragraphs. Passed: 2 headings, 1
sticky note, 3 misspellings. Now at: 'The
investigation concluded.'"

This is the document equivalent of a GPS "in 400
metres, turn right" — a summary of what was passed,
not a coordinate per metre traveled. Single-key
navigation continues to announce as it does today.

**Why it is magical.** Fast navigation currently
floods the screen reader with intermediate
announcements that the user ignores anyway. The
summary mode turns rapid Page Down into a meaningful
report: the user knows what they flew over and where
they landed. The "passed N headings" count is
especially useful for knowing whether it is worth
scrolling back.

**Implementation.** A key-repeat accumulator in
`main_frame.py` that tracks the structural index
delta between the navigation-start position and
the pause position. Uses the same Quick Nav
primitives that drive the 13-element type counts.
The pause threshold (600ms default) is configurable
in Preferences > Navigation.
