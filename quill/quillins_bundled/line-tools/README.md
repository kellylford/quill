# Line Tools (bundled Quillin)

`com.quill.bundled.line-tools` is a **bundled Tier C Quillin** that ships with
QUILL. It provides six cursor-aware line operations extracted from QUILL's core
into a genuine sandboxed Quillin, using the `get_cursor_offset()` and
`set_cursor()` capabilities added in the QUILL 1.x capability expansion.

## What it contributes

| Command | Handler | Surfaced on |
| ------- | ------- | ----------- |
| `ext.lines.duplicate` - *Duplicate Line* | `duplicate_line` | Edit menu |
| `ext.lines.delete` - *Delete Line* | `delete_line` | Edit menu |
| `ext.lines.move_up` - *Move Line Up* | `move_line_up` | Edit menu |
| `ext.lines.move_down` - *Move Line Down* | `move_line_down` | Edit menu |
| `ext.lines.join` - *Join Paragraph Lines* | `join_paragraph` | Edit menu |
| `ext.lines.join_next` - *Join with Next Line* | `join_with_next_line` | Edit menu |

## Capabilities

`editor.read` (read text + cursor offset), `editor.write` (replace document +
set cursor), `ui.announce`, `ui.command`. No filesystem, network, clipboard,
or storage access.

## How it works

Each command reads the full document text and integer cursor offset, applies a
pure text transform from `line_ops.py`, writes the result back as a single
undoable edit via `set_text`, and repositions the caret with `set_cursor`.
When a command is a no-op (e.g., move-up on the first line), `set_text` is
skipped and only `set_cursor` is called.

## Files

- `manifest.json` - the `quill.extension/1` manifest.
- `extension.py` - the Layer 2 entry module.
- `line_ops.py` - vendored pure-Python cursor-aware line operations.
- `README.md` - this file.
- `LICENSE` - MIT license.
