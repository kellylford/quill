# Text Tools (bundled Quillin)

A first-party, **bundled** Quillin (Tier C) that ships enabled inside QUILL. It
re-expresses six on-demand text transforms as a genuine sandboxed Quillin,
proving the extension platform can carry real features (see
`docs/quillins.md`, Wave 1).

## Commands

| Command | Home | What it does |
| --- | --- | --- |
| Number Lines | Format > Transform Lines | Prefix each non-blank line with a running number (you pick the start). |
| Hard-Wrap Lines | Format > Transform Lines | Re-flow paragraphs so no line exceeds a width you choose. |
| Count Regular Expression Matches | Search | Count matches of a pattern in the selection or document. |
| Extract Regular Expression Matches | Search | Collect every match into a new buffer. |
| Lines in First Block Only | Search | Lines above the cursor that do not appear below it. |
| Lines Common to Both Blocks | Search | Lines above the cursor that also appear below it. |

## Capabilities

`editor.read`, `editor.write`, `ui.announce`, `ui.prompt`, `ui.command`. No
filesystem, network, or clipboard access, so the Quillin never raises a consent
prompt.

## Layout

- `manifest.json` - the `quill.extension/1` manifest.
- `extension.py` - the Layer 2 entry module (`register(api)` + handlers).
- `algorithms.py` - the vendored, dependency-free text algorithms the handlers
  call (moved out of `quill/core` so the feature is self-contained).
