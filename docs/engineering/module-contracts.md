# Module contracts

This file defines implementation contracts currently enforced in code and tests.

## `quill.core.document`

- `Document` owns the active text buffer metadata (`path`, `encoding`, `line_ending`, `modified`, `revision`).
- `set_text()` marks the document modified and increments revision only on actual content change.
- `mark_saved()` clears modified state and optionally updates path.

## `quill.core.commands`

- Command IDs are unique.
- Unknown command execution raises `KeyError`.
- Registry listing is stable and sorted by title.
- Keybinding lookup is queryable by command id.

## `quill.io.text`

- `read_text_document(path)` returns an unmodified `Document` snapshot from disk.
- `write_text_document(document, path?)` requires an explicit or existing path.
- Writes preserve configured line-ending policy and update document saved state.

## `quill.core.storage`

- JSON writes are atomic (`*.tmp` then replace).
- Reads are tolerant to missing files via caller-provided defaults.

## `quill.core.settings`

- Settings are loaded from `%APPDATA%\Quill\settings.json` or `QUILL_DATA_DIR`.
- `recent_files_limit` is clamped to `[1, 50]`.

## `quill.core.keymap`

- Default keymap is always present.
- Persisted overrides merge over defaults and must be string-to-string entries.

## `quill.core.recent`

- Recent file updates are deduplicated (most recent first) and limit-bounded.

## `quill.core.search`

- Search supports literal and regex modes.
- Case sensitivity and whole-word matching are explicit options.
- Replace operations return both updated text and replacement count.

## `quill.core.tagging`

- HTML insertion supports picked tags with optional attribute parsing (`key=value; key2=value2`).
- Void HTML tags are emitted as self-closing snippets.
- Markdown tagging emits structured snippets (headings, lists, links/images, code, table, footnotes).

## `quill.ui.main_frame`

- Title reflects document name and modified status.
- Status bar channel 0 is action/result announcements; channel 1 is path.
- Menu labels reflect current keymap bindings.
- `File > Open Recent` is rebuilt from persisted recent-file state.
