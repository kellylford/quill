# Quillin Tutorial — build your first Quillin

This is a hands-on, build-it-from-scratch tutorial for Quillin contributors. By
the end you will have authored, linted, tested, and prepared a real Quillin for
submission — starting from a zero-capability snippet and growing into a
sandboxed Python handler.

It pairs with three references you'll reach for along the way:

- [`scripting.md`](scripting.md) — the full design + authoring reference (§13
  schema, §14 API, §15 the deterministic generation contract).
- [`quillin-submission.md`](quillin-submission.md) — the submission process.
- [`quillin-code-of-conduct.md`](quillin-code-of-conduct.md) — the Author
  Covenant every Quillin must keep.

> **Prerequisite:** a working QUILL dev checkout (`pip install -e ".[ui,dev]"`,
> Python 3.12). The linter itself is `wx`-free, so `pip install -e .` is enough
> to lint.

---

## 1. What you're building

A Quillin called **Word Count Tools** (`com.example.wordcount`). It will:

1. start as a **Layer 1** snippet that inserts a heading (no code, no
   capabilities), then
2. grow a **Layer 2** Python handler that counts the words in the selection and
   **announces** the result.

Along the way you'll see the two ideas that make Quillins safe: **declare the
minimum** and **announce every outcome**.

---

## 2. Anatomy of a Quillin

A Quillin is one directory:

```
word-count-tools/
  manifest.json     # the contract — required
  extension.py      # Python entry module — only for Layer 2
  README.md         # required for submission
  LICENSE           # required (or a "license" field in the manifest)
```

The `manifest.json` always starts with the schema discriminator and an identity:

```json
{
  "schema": "quill.extension/1",
  "id": "com.example.wordcount",
  "name": "Word Count Tools",
  "version": "0.1.0"
}
```

- **`schema`** is always `"quill.extension/1"`.
- **`id`** is reverse-DNS *you control*. `com.quill.*` is reserved for
  first-party bundled Quillins.
- **`version`** is `MAJOR.MINOR.PATCH` and you bump it on every change.

---

## 3. Step 1 — a Layer 1 snippet (no capabilities)

Create the directory and a manifest that contributes one snippet command.
Snippets are declarative text with placeholders — **no code runs**, so a
snippet-only Quillin needs **no capabilities** at all.

`manifest.json`:

```json
{
  "schema": "quill.extension/1",
  "id": "com.example.wordcount",
  "name": "Word Count Tools",
  "version": "0.1.0",
  "author": "Your Name",
  "description": "Insert a word-count heading and count words in the selection.",
  "license": "MIT",
  "min_quill_version": "1.0.0",
  "contributes": {
    "commands": [
      {
        "id": "ext.wordcount.heading",
        "title": "Insert Word Count Heading",
        "run": { "snippet": "## Word count for ${filename}\n\n${cursor}" }
      }
    ],
    "menus": [
      { "parent": "Format", "command": "ext.wordcount.heading" }
    ]
  }
}
```

Two rules you just used:

- **Command ids are namespaced under `ext.`** so they can never collide with a
  built-in QUILL command.
- **Menu parents** are a fixed set: `File`, `Edit`, `Format`, `Tools`,
  `Navigate`, `View`, `Help`.

### Snippet placeholders

| Placeholder | Expands to |
| ----------- | ---------- |
| `${selection}` | the current selection (empty if none) |
| `${clipboard}` | the clipboard text |
| `${date}` / `${time}` | today's date / current time |
| `${filename}` | the current document's file name |
| `${cursor}` | where the caret lands after insertion |

### Lint it

```powershell
python -m quill.tools.quillin_lint path\to\word-count-tools --strict
```

You'll get a couple of warnings (no README, no LICENSE). Add a `README.md` and a
`LICENSE` file (or keep the manifest `license` field) and re-run until it's
green. **That clean `--strict` run is your submission bar for Layer 1.**

You now have a complete, useful Quillin with zero code and zero capabilities.
Most Quillins never need more than this.

---

## 4. Step 2 — a Layer 2 Python handler

Now add real logic: count the words in the selection and announce the count.
Handlers run **out-of-process**, in a sandbox, behind QUILL's capability +
consent gate.

### 4a. Declare what you need

A handler command requires two things in the manifest: a top-level `main` module
and the `ui.command` capability. To read the selection and announce a result you
also need `editor.read` and `ui.announce`. **That's the minimum — declare
nothing more.**

Add to `manifest.json`:

```json
  "capabilities": ["editor.read", "ui.announce", "ui.command"],
  "main": "extension.py",
```

and a second command in `contributes.commands`:

```json
      {
        "id": "ext.wordcount.count",
        "title": "Count Words In Selection",
        "run": { "handler": "count_words" }
      }
```

Wire it to a context-menu entry (only when there's a selection) and a hotkey:

```json
    "context_menu": [
      { "command": "ext.wordcount.count", "when": "editor.hasSelection" }
    ],
    "hotkeys": [
      { "command": "ext.wordcount.count", "binding": "Ctrl+Shift+W" }
    ]
```

`when` guards accept `always`, `editor.hasSelection`, `editor.hasText`, or
`editor.empty`. Hotkey conflicts are **rejected**, never silently overridden.

### 4b. Write the handler

`extension.py`:

```python
"""Word Count Tools — a Layer 2 Quillin handler."""

from __future__ import annotations


def register(api):
    """Entry point: QUILL calls this once to register handlers."""
    api.register_command("count_words", count_words)


def count_words(api):
    """Count words in the selection and announce the result."""
    selection = api.get_selection()
    if not selection.strip():
        api.announce("Nothing selected.")
        return
    count = len(selection.split())
    api.announce(f"{count} word{'s' if count != 1 else ''} selected.")
```

What to notice:

- **`register(api)`** is the single entry point. It binds the handler name used
  in the manifest (`"count_words"`) to a Python function.
- The handler receives the **`QuillExtensionApi`** (`api`). It can only do what
  your declared capabilities allow — calling something you didn't declare is
  blocked by the sandbox, not by politeness.
- **It announces its outcome in every path** — success *and* the empty-selection
  case. A silent success is a bug under the Author Covenant.

### 4c. The capability surface (Layer 2)

The API you can call maps directly onto declared capabilities:

| You call | Capability required | Notes |
| -------- | ------------------- | ----- |
| `api.get_text()` / `api.get_selection()` / `api.get_cursor()` | `editor.read` | |
| `api.insert_text(...)` / `api.replace_selection(...)` | `editor.write` | edits join normal undo |
| `api.announce(...)` | `ui.announce` | the spoken/braille outcome |
| `api.get_clipboard()` / `api.set_clipboard(...)` | `clipboard.read` / `clipboard.write` | |
| `api.read_file(...)` / `api.write_file(...)` | `fs.read` / `fs.write` | **consent-gated** at runtime |
| `api.fetch(...)` | `net` | **consent-gated** at runtime |
| `api.log(...)` | none | never reaches announcements |

`fs.*` and `net` prompt the user on **every** use. Design for a graceful,
announced refusal — never assume access is granted.

---

## 5. Test your Quillin

Mirror the bundled Quillin's test
([`tests/unit/core/test_quillins_bundled_markdown.py`](../tests/unit/core/test_quillins_bundled_markdown.py)).
A good Layer 2 test validates the manifest, builds a conflict-free contribution
registry, and drives the handler against a fake API:

```python
import json
from pathlib import Path

from quill.core.quillins.validation import parse_manifest
from quill.core.quillins.registry import build_registry


def _manifest():
    path = Path("path/to/word-count-tools/manifest.json")
    return parse_manifest(json.loads(path.read_text(encoding="utf-8")))


def test_manifest_is_valid_and_registry_has_no_conflicts():
    manifest = _manifest()
    registry = build_registry([manifest])
    assert "ext.wordcount.count" in registry.commands


class _FakeApi:
    def __init__(self, selection):
        self._selection = selection
        self.announced = []

    def get_selection(self):
        return self._selection

    def announce(self, message):
        self.announced.append(message)


def test_handler_counts_and_announces():
    from importlib import import_module  # or exec the extension module directly

    api = _FakeApi("one two three")
    # call your count_words(api) here and assert:
    # assert api.announced == ["3 words selected."]
```

For real confidence, also drive the handler through the **out-of-process host**
(see [`tests/integration/test_quillins_host_integration.py`](../tests/integration/test_quillins_host_integration.py)),
which exercises the actual sandbox, capability gate, and consent flow.

---

## 6. Lint, then check everything

```powershell
python -m quill.tools.quillin_lint path\to\word-count-tools --strict
pytest -q path\to\your\test_word_count.py
```

The linter applies three independent lenses, so a mistake is caught by whichever
sees it first:

1. **Schema check** — your manifest validated against the published JSON Schema
   (`quill/core/schemas/extension.json`), made executable inside the linter.
2. **Manifest validation** — the same contract validator the loader enforces
   (this is what flags "a handler command requires `main` + `ui.command`").
3. **Structure & capability hygiene** — your `main` exists, README + license are
   present, and every consent-gated capability is surfaced for review.

---

## 7. Submit

1. Open the **Quillin submission** issue — its form scaffolds the
   `manifest.json` and records your Author Covenant acknowledgement.
2. Open a PR using the **Quillin submission** PR template and complete its
   checklist.
3. The `Quillin Verify` workflow re-runs the linter in `--strict` mode on your
   Quillin. Green check → ready for human review; red → fix and push.

Review focuses on what machines can't fully judge: real accessibility (does
every action announce a clear outcome; is it keyboard-complete?), capability
justification (is each one necessary and transparent?), and honesty (readable
source, no silent network, behaviour matches description).

The full process, review criteria, and acceptance checklist live in
[`quillin-submission.md`](quillin-submission.md).

---

## 8. Recap — the rules that matter

- **Start at Layer 1.** Snippets cover most needs with zero code and zero
  capabilities.
- **Declare the minimum.** A handler needs `main` + `ui.command`; add `editor.*`,
  `clipboard.*`, `fs.*`, or `net` only when you actually use them.
- **Announce every outcome.** Success and failure both speak.
- **`fs.*` and `net` are consent-gated.** Handle refusal gracefully.
- **Namespace ids under `ext.`**, use a reverse-DNS `id` you control, and
  version honestly.
- **Lint `--strict`, test, then submit.** A clean linter run is the bar.

Welcome aboard — your first Quillin is exactly how QUILL stays *Quality, Usable,
Inclusive, Lightweight, Literate.*
