# Insert Character (bundled Quillin)

`com.quill.bundled.insert-character` is a **bundled Tier C Quillin** that
ships with QUILL. It adds an **Insert Special Character** command that accepts
any Unicode code point and inserts the corresponding character at the caret.

## What it contributes

| Command | Layer | Capabilities | Surfaced on |
| ------- | ----- | ------------ | ----------- |
| `ext.insert.character` - *Insert Special Character...* | Layer 2 handler | `ui.prompt`, `ui.announce`, `editor.write`, `ui.command` | Insert menu, editor context menu |

## Code point formats accepted

- **Hexadecimal** (default): `41`, `1F600`, `U+0041`, `u+1f600`
- **Decimal** (lowercase `d` prefix): `d65`, `d128512`

Surrogates (U+D800-U+DFFF) and out-of-range values are rejected with a
descriptive error announced to screen readers.

## Files

- `manifest.json` - the `quill.extension/1` manifest.
- `extension.py` - the Layer 2 entry module; `register(api)` wires the handler.
- `codepoints.py` - vendored pure-Python code point parser (no dependencies).
- `README.md` - this file.
- `LICENSE` - MIT license.
