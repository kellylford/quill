# Data layout

Quill persistent state is rooted under:

- `%APPDATA%\Quill\...` on Windows (default)
- `QUILL_DATA_DIR` when set (test/dev override)

## Files currently implemented

- `settings.json` — theme/soft-wrap/recent-file-limit
- `keymap.json` — user keybinding overrides
- `recent.json` — MRU file list
- `search-history.json` — recent find/replace query history
- `autosave\...` — autosave snapshots
- `backups\...` — save-triggered backup snapshots
- `logs\` and `diagnostics\` directories reserved

## Write guarantees

- JSON stores use atomic replacement (`.tmp` file + replace).
- Backup/autosave snapshots are append-style timestamped files.
- Path hashing is used for per-document backup/autosave directories.
