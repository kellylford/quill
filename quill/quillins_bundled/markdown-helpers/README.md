# Markdown Helpers (bundled Quillin)

`com.quill.bundled.markdown-helpers` is a **bundled Tier C Quillin** that ships
with QUILL and is the canonical template for authoring a new Quillin. It
demonstrates both authoring layers in one small, audited package.

## What it contributes

| Command | Layer | Capability | Surfaced on |
| ------- | ----- | ---------- | ----------- |
| `ext.mdh.frontmatter` — *Insert Markdown Front Matter* | Layer 1 snippet (no code) | none | Format menu |
| `ext.mdh.bold` — *Wrap Selection in Bold* | Layer 2 handler (`extension.py`) | `editor.read`, `editor.write`, `ui.announce`, `ui.command` | Format menu, editor context menu (when there is a selection), `Ctrl+Shift+B` |

## Files

- `manifest.json` — the `quill.extension/1` manifest (the contract).
- `extension.py` — the Layer 2 entry module. Its `register(api)` wires the
  `wrap_bold` handler to the `ext.mdh.bold` command.
- `README.md` — this file.

## How it runs

As a bundled Quillin it ships **enabled**, gated by the on-by-default
`core.bundled_quillins` feature flag — wholly independent of the SEC-8
third-party lock. Its handler still runs in the sandboxed out-of-process host
through the same capability + consent gate as any third-party Quillin: the
non-consent capabilities it declares are pre-granted (so a trusted shipped
feature does not nag on first use), while `fs.*`/`net` — which it does **not**
request — would still pass the per-action consent gate at runtime.

## Authoring your own

1. Copy this directory as a starting point.
2. Edit `manifest.json`: pick a reverse-DNS `id`, declare the **minimum**
   capabilities, and contribute your commands.
3. Lint it: `python -m quill.tools.quillin_lint path\to\your-quillin --strict`.
4. Read the submission guide: [`docs/quillin-submission.md`](../../../docs/quillin-submission.md)
   and the [Quillin Author Covenant](../../../docs/quillin-code-of-conduct.md).
