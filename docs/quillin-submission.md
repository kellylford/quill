# Submitting a Quillin

This is the end-to-end guide for authoring a Quillin and submitting it to QUILL.
It is the human companion to three machine-enforced pieces:

- the normative manifest **JSON Schema**,
  [`quill/core/schemas/extension.json`](../quill/core/schemas/extension.json),
- the **submission linter**, `python -m quill.tools.quillin_lint`, and
- the automated **verification workflow**,
  [`.github/workflows/quillin-verify.yml`](../.github/workflows/quillin-verify.yml).

Before you start, read the [Quillin Author Covenant](quillin-code-of-conduct.md)
— every submission attests to it — and the authoring reference in
[`scripting.md`](scripting.md) (§13 schema, §14 authoring reference, §15 the
deterministic AI-authoring contract).

## 1. What a Quillin is

A Quillin is a small, sandboxed extension described by a `manifest.json`
(`schema: "quill.extension/1"`). It comes in two layers:

- **Layer 1 — snippet only.** Declarative text insertion with placeholders
  (`${selection}`, `${clipboard}`, `${date}`, `${time}`, `${filename}`,
  `${cursor}`). **No code, no capabilities.** This covers most needs and is the
  safest, fastest path to acceptance.
- **Layer 2 — Python handler.** A `main` entry module registers handler
  functions via `api.register_command`. Requires the `ui.command` capability and
  runs **out-of-process** behind QUILL's capability + consent gate.

## 2. Directory layout

A Quillin is one directory:

```
my-quillin/
  manifest.json     # required — the contract
  extension.py      # required only for Layer 2 (matches manifest "main")
  README.md         # required for submission
  LICENSE           # required (or declare "license" in the manifest)
```

The bundled
[`quill/quillins_bundled/markdown-helpers/`](../quill/quillins_bundled/markdown-helpers/)
is the canonical template — copy it.

## 3. Author the manifest

Minimum fields: `schema`, `id`, `name`, `version`. Strongly recommended for any
submission: `author`, `description`, `license`, `min_quill_version`.

- **`id`** — reverse-DNS you control, e.g. `com.example.mytool`. `com.quill.*`
  is reserved for first-party bundled Quillins.
- **`version`** — `MAJOR.MINOR.PATCH`, bumped on every change.
- **`capabilities`** — declare the **minimum**. Snippet-only Quillins declare
  none. `fs.read`, `fs.write`, and `net` are **consent-gated**: every use prompts
  the user at runtime, so design for a graceful, announced refusal.
- **`contributes`** — `commands` (each `run` has *exactly one* of `snippet` or
  `handler`), plus optional `menus` (parents: File, Edit, Format, Tools,
  Navigate, View, Help), `context_menu` (with an optional `when` guard), and
  `hotkeys` (QUILL binding grammar; conflicts are rejected, never silently
  overridden). Command ids must be namespaced under `ext.`.
- A command using `run.handler` **requires** a top-level `main` module and the
  `ui.command` capability.

## 4. Self-lint before you submit

Run the linter — the same tool CI runs — and fix everything:

```powershell
python -m quill.tools.quillin_lint path\to\my-quillin --strict
```

It applies three independent lenses:

1. **Schema check** — your manifest is validated against the published JSON
   Schema artifact (made executable inside the linter), so your errors match
   what editors and external tools see.
2. **Manifest validation** — the same contract validator the loader enforces,
   catching rules the schema does not encode (e.g. handler ⇒ `main` +
   `ui.command`).
3. **Structure & capability hygiene** — confirms your `main` module exists, a
   README and license are present, and surfaces every consent-gated capability
   for deliberate review.

`--strict` (used by CI) treats warnings as failures. A clean `--strict` run is
the bar for submission.

## 5. Write tests

Mirror the bundled Quillin's test
([`tests/unit/core/test_quillins_bundled_markdown.py`](../tests/unit/core/test_quillins_bundled_markdown.py)):
validate the manifest, build a conflict-free contribution registry, expand any
snippet, and drive any handler. Handler Quillins should also be exercised through
the real out-of-process host (see
[`tests/integration/test_quillins_host_integration.py`](../tests/integration/test_quillins_host_integration.py)).

## 6. Accept the Author Covenant

Read [`quillin-code-of-conduct.md`](quillin-code-of-conduct.md) and confirm your
Quillin keeps every promise: accessibility (announce outcomes, keyboard-complete),
capability minimization and honesty, no silent network or telemetry, privacy,
security (no obfuscation, no sandbox-escape, no malware), licensing, namespace
etiquette, and maintenance.

## 7. Open the submission PR

1. Add your Quillin directory to the submission area and stage **only** your own
   files (never `git add -A`).
2. Open a pull request using the **Quillin submission** PR template and complete
   its checklist.
3. The `Quillin Verify` workflow runs `quillin_lint --strict` over the Quillins
   your PR changes. A red check blocks merge; fix and push again.

## 8. Review and acceptance

A maintainer reviews against this guide and the Covenant. Review focuses on what
machines cannot fully judge:

- **Accessibility in practice** — does every action announce a clear outcome; is
  it fully keyboard-operable?
- **Capability justification** — is each declared capability genuinely needed and
  used transparently? Consent-gated capabilities get the most scrutiny.
- **Security and honesty** — readable source, no obfuscation, no sandbox-escape,
  no silent network, behaviour matches description.
- **Quality** — clear naming, sensible menu/hotkey placement, tests present.

Outcomes: **accepted** (listed and/or bundled), **changes requested**, or
**rejected** with a reason. Security or accessibility violations are
non-negotiable rejections.

## 9. Updates, versioning, and removal

- **Updates** are new PRs that bump `version` and re-pass `--strict` + review.
- **Deprecation** — mark it in your README and bump a MAJOR version for breaking
  changes.
- **Removal** — a Quillin that violates the Covenant (especially security or
  accessibility) may be delisted or unbundled without notice per the Covenant's
  enforcement section.

## Quick checklist

- [ ] `manifest.json` valid: `python -m quill.tools.quillin_lint <dir> --strict` is green
- [ ] Minimum capabilities declared; consent-gated use is justified and announced
- [ ] Every command announces its outcome and is keyboard-operable
- [ ] `README` and license present; `id` is reverse-DNS you control
- [ ] Tests added (manifest + registry + snippet/handler; host round-trip for handlers)
- [ ] Author Covenant upheld and attested in the PR
