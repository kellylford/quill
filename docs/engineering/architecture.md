# Architecture

Quill follows a layered desktop architecture with strict boundaries to preserve accessibility behavior and testability.

## Layers

1. **`quill.core`**  
   Pure domain logic: documents, command registry, settings, keymap, recent files, metrics, storage primitives.  
   No wx imports and no direct UI ownership.

2. **`quill.io`**  
   Format adapters and detection. Current implementation includes plain-text read/write and text-format detection.

3. **`quill.ui`**  
   wxPython shell, editor surface, menus, status bar, and command palette. UI composes `core` + `io` and owns widget lifecycle.

4. **`quill.platform.windows`**  
   Windows-specific bridges. Current implementation includes speech announcement integration surface.

5. **`quill.plugins`**  
   Plugin-facing API surfaces and manifest model. Runtime loading is intentionally minimal in this phase.

6. **`quill.tools`**  
   Internal tooling namespace reserved for diagnostics/generators described in the PRD.

## Primary flow

- User action enters through `ui.main_frame.MainFrame`.
- Action dispatches to `core.commands.CommandRegistry`.
- Command reads/writes `core.document.Document` and persists through `io` or `core.storage`.
- Result is surfaced through status updates and `platform.windows.sr_announce.announce`.

## Boundary rules

- `core` does not import `wx`.
- `ui` does not perform raw persistence logic directly; it calls `core` helpers for settings/keymap/recent and `io` for document I/O.
- Persistent writes are atomic via `core.storage.write_json_atomic`.
