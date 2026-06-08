# Quillin Author Covenant

This Covenant is the **code of conduct for Quillin code** — the technical and
ethical promises every Quillin must keep to be bundled with, or listed for, QUILL.
It complements (and does not replace) the community
[`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md), which governs how people behave;
this document governs how *Quillins* behave.

QUILL is **Quality, Usable, Inclusive, Lightweight, Literate** — a
screen-reader-first editor. A Quillin extends that editor, so it inherits those
values. By submitting a Quillin (see
[`quillin-submission.md`](quillin-submission.md)) you attest that it upholds
every promise below. Verification is partly automated
(`python -m quill.tools.quillin_lint`) and partly human review; both must pass.

## 1. Accessibility is non-negotiable

- **Announce every outcome.** Every command reports its result as text, so a
  screen-reader user knows what happened (NVDA/JAWS/Narrator parity). A silent
  success is a bug.
- **Keyboard-complete.** Everything a Quillin offers is reachable and operable
  from the keyboard alone. No mouse-only affordance, no focus traps.
- **Plain-text first.** Respect the editor's plain-text-first writing surface;
  do not fight the stock controls QUILL relies on for accessibility.
- **No flashing, no surprise focus changes.** Do not move focus unexpectedly or
  produce content that could trigger photosensitive reactions.

## 2. Capability honesty and minimization

- **Declare the minimum.** Request only the capabilities you actually use.
  A snippet-only Quillin declares none.
- **No capability laundering.** Do not request a broad capability to do a narrow
  thing, and never attempt to act beyond what you declared. The sandbox enforces
  this; trying to defeat it is grounds for immediate removal.
- **`fs.*` and `net` are consent-gated.** If you request filesystem or network
  access, expect every use to pass a per-action consent prompt, and design for a
  graceful, announced outcome when the user says no.

## 3. No silent network, no telemetry

- **No silent network calls.** Every outbound request is an explicit, opt-in,
  per-action event with visible progress and an announced outcome. This mirrors
  QUILL's own non-negotiable rule.
- **No telemetry, analytics, tracking, or beaconing** of any kind.
- **No document content leaves the device** without an explicit, per-action
  consent gate the user can decline.

## 4. Privacy and data handling

- **Treat document content as private.** Never log it, never transmit it without
  consent, never persist it outside what the user asked for.
- **No secrets in the manifest or code.** Do not embed credentials, tokens, or
  keys. Do not phone home for "activation".
- **Be transparent about what you store** and where, and keep it inside QUILL's
  sanctioned storage conventions.

## 5. Security and integrity

- **No obfuscation.** Ship readable source. Minified, encoded, or deliberately
  obscured handler code will be rejected.
- **No sandbox escape attempts**, no spawning unsanctioned subprocesses, no
  loading remote code at runtime, no monkey-patching QUILL internals.
- **No malware, ever** — no destructive behaviour, ransomware, cryptominers,
  credential harvesting, or anything that harms the user or their data.
- **Fail safe.** Errors surface as announced, reviewable text — never a silent
  failure and never a crash that takes the editor down.

## 6. Licensing and attribution

- **Declare a license** (manifest `license` field and/or a `LICENSE` file) and
  ship a `README`.
- **Respect copyright.** Only include content and dependencies you have the
  right to distribute, and attribute third-party material correctly.

## 7. Naming and namespace etiquette

- **Use a reverse-DNS `id`** you control (e.g. `com.example.mytool`); do not
  squat on `com.quill.*`, which is reserved for first-party bundled Quillins.
- **Namespace commands under `ext.`** (enforced) and choose clear, honest,
  Title-Case command names. No misleading or impersonating titles.

## 8. Maintenance and good citizenship

- **Version honestly** using `MAJOR.MINOR.PATCH`; bump on every change.
- **Keep it lightweight.** Do only what you describe; no scope creep, no
  bundling unrelated functionality.
- **Be responsive** to security reports and accessibility regressions.

## Enforcement

A Quillin that violates this Covenant may be **rejected, delisted, or unbundled**
without notice, and repeated or malicious violations may bar an author from
future submissions. Security and accessibility violations are treated as the most
serious. Report concerns through the process in
[`SECURITY.md`](../SECURITY.md) (for security) or by opening an issue (for
accessibility or conduct).

Keeping this Covenant is what lets QUILL ship Quillins **seamlessly at the point
of use and transparently where it matters**.
