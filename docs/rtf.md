# QUILL: Native RTF Editing and a Ulysses Competitive Study

Two forward-looking proposals in one place. Part One asks what it would take for
QUILL to host a real rich-text editing surface so a writer can choose between
plain-text-first writing and live rich editing. Part Two studies Ulysses, the
Apple Design Award winning writing app for Mac, iPad, and iPhone, and recommends
which of its ideas QUILL should adopt without compromising its accessibility-first
soul.

Both parts are written to be ambitious. They are also written honestly: where an
idea collides with a non-negotiable QUILL principle, the collision is named and a
safer path is offered.

---

## Part One: Native RTF Editing as an Optional Surface

### The idea in one sentence

Let a writer open Preferences and choose their editing surface: keep the current
plain-text-first editor (a `wx.TextCtrl` over Markdown-style markup), or switch to
a native rich-text surface (a hosted `wx.RichTextCtrl`) where bold, italic,
headings, lists, and links are shown as formatted text rather than as markup
characters, and `.rtf` files open and save with no markup translation at all.

### Why this is different from what exists today

QUILL already supports RTF as a *file format*. The io-layer round-trip delivered
under EDS-21 reads RTF into Markdown-style markup and writes that markup back out
to valid RTF. See [quill/io/rtf.py](quill/io/rtf.py). That work is real and it
stays valuable. What it deliberately does not do is change the editing surface:
when you open an `.rtf` today, you edit markup in a plain-text control, and the
formatting is a translation, not a live object.

This proposal is about the surface itself. It introduces a second, opt-in editor
control where formatting is native and visible, and where RTF is the document's
true in-memory representation rather than a serialized export of markup.

### The headline tension, stated plainly

QUILL's founding principle is screen-reader-first, plain-text-first writing on
stock controls. The PRD and the repository conventions are explicit that the
writing path should use `wx.TextCtrl` and avoid custom-drawn or heavily
rich-formatted editor controls, because plain stock controls give the most
predictable, best-tested screen-reader experience across NVDA, JAWS, and
Narrator.

A `wx.RichTextCtrl` is a richer, more complex control. On Windows its
accessibility exposure is good but not identical to a plain edit control, and on
macOS and Linux the wx rich-text implementation behaves differently again. So the
core design question is not "can we host an RTF control" (we can) but "can we host
it without weakening the accessibility guarantee that defines QUILL." The answer
this proposal defends: yes, but only as an explicit, clearly-announced,
non-default choice, with the plain-text surface remaining the supported default
and the rich surface treated as a power-user mode with its own honest
accessibility disclosure.

### What "magical" looks like here

The magic is not the formatting. Every word processor has formatting. The magic
is making a rich surface feel as calm, legible, and screen-reader-honest as the
plain surface, and letting a writer move between the two without ever losing a
word.

- One document, two lenses. The same file can be viewed as markup or as live
  formatting, and switching lenses is a single command with a spoken summary of
  what changed and what, if anything, cannot survive the switch.
- A spoken formatting model. When the caret enters bold text, QUILL says "bold"
  the way it already announces actions, so formatting is something you hear, not
  only something sighted users see. This is the feature Microsoft Word and
  Ulysses never built for screen-reader users, and it is where QUILL can lead.
- Honest fidelity. Before any potentially lossy conversion, QUILL tells you in
  plain language what will be preserved and what will be flattened, and offers to
  keep a sidecar copy. No silent data loss, ever.

### Architecture: where this lives

QUILL's layering rules are strict. `quill/core` and `quill/io` must stay free of
`wx`. All widget code lives in `quill/ui` and `quill/platform`. This proposal
respects that boundary completely.

- A new editor-surface abstraction in `quill/ui` (for example
  `quill/ui/editor_surface.py`) defines a small protocol that both the plain-text
  surface and the rich surface implement: get and set the document text, get and
  set selection, apply and query inline formatting, report the caret context, and
  emit change and caret events. The rest of `quill/ui/main_frame.py` talks to the
  surface through this protocol instead of touching `self.editor` directly.
- The plain-text surface wraps today's `wx.TextCtrl` and is the default.
- The rich surface wraps a `wx.RichTextCtrl` and is selected only when the writer
  opts in.
- A pure, `wx`-free RTF formatting model can live in `quill/io` (extending the
  existing `quill/io/rtf.py`) so that conversion logic stays testable on Linux CI
  where `wx` cannot be imported. The control reads and writes through that model.

This is the single most important design decision: introduce a surface protocol
so the two controls are interchangeable from the application's point of view. Without
it, every one of the command surfaces below would need a branch for "is this the
rich control or the plain control." With it, each command asks the surface to do
the work and the surface knows how.

### Impact across every command surface

This is the heart of the proposal. The instruction to "keep in mind all command
surfaces that could be impacted" is taken literally. The table below inventories
the real call sites discovered in the codebase and rates the work each one needs
to support a rich surface. The plain-text surface keeps working unchanged in every
row; the rating describes the rich-surface effort.

Effort key: Low means the existing logic works through the surface protocol with
little change. Medium means the command needs a rich-aware path. High means the
command needs genuine new design because formatting changes its meaning.

| Command surface | Representative call sites | Rich-surface effort | Why |
| --- | --- | --- | --- |
| Editor creation and event binding | `_create_document_tab`, `_bind_editor_events`, `_on_editor_char_hook` in [quill/ui/main_frame.py](quill/ui/main_frame.py) | High | The control is constructed here; this is where the surface protocol and the two implementations plug in. Smart-quote and dash autoformat must be re-expressed against the rich surface. |
| Dirty-state and document buffer | `_on_text_changed`, `document.set_text(...)`, [quill/core/document.py](quill/core/document.py) | Medium | The buffer is no longer just a string. The Document model needs a representation that can hold formatting (or a paired markup-plus-format view) without `core` importing `wx`. |
| Selection (expand, shrink, select all) | selection helpers in [quill/ui/main_frame.py](quill/ui/main_frame.py), [quill/core/selection.py](quill/core/selection.py), [quill/core/set_ops.py](quill/core/set_ops.py) | Medium | Offsets differ between a markup string and a formatted run model; selection math must move behind the surface protocol. |
| Clipboard (cut, copy, paste) and context menu | editor context-menu wiring, `_copy_text_to_clipboard`, `copy_with_source`, [quill/platform/windows/clipboard.py](quill/platform/windows/clipboard.py), [quill/ui/main_frame_power_tools.py](quill/ui/main_frame_power_tools.py) | High | Rich paste must decide between formatted paste and paste-as-plain, and copy should offer RTF and plain flavors. This is also a security surface: pasted RTF must be sanitized. |
| Navigation (go to line, bookmarks, headings, outline) | `go_to_line`, `_navigate_heading`, `open_heading_organizer`, bookmark commands, [quill/core/outline.py](quill/core/outline.py), [quill/core/structure_nav.py](quill/core/structure_nav.py) | Medium | Headings are styles in a rich document, not `#` prefixes. Outline and heading navigation must read paragraph styles instead of scanning markup. |
| Find and replace | `find_text`, `_open_find_replace`, replace-all and replace-in-files, [quill/core/search.py](quill/core/search.py), [quill/core/regex_ops.py](quill/core/regex_ops.py) | Medium | Search runs over plain text extracted from the rich model; match offsets map back to formatted runs. Replace must preserve surrounding formatting. |
| Spellcheck | `open_spell_check_dialog`, as-you-type toggle, [quill/core/spellcheck.py](quill/core/spellcheck.py) | Medium | Word extraction and squiggle placement work on runs rather than a flat string; correction must not drop a run's formatting. |
| Markup and formatting commands | `format_bold`, `format_italic`, `format_heading`, heading-level commands, [quill/core/format_ops.py](quill/core/format_ops.py), [quill/core/autoformat.py](quill/core/autoformat.py) | High | On the plain surface these insert characters; on the rich surface they toggle native attributes. This is the clearest case for the surface protocol to own two implementations of one command. |
| Autosave | `_maybe_autosave`, [quill/core/autosave.py](quill/core/autosave.py) | Low | Autosave serializes the document; it needs the rich serializer but the trigger logic is unchanged. |
| Backups and recovery | `restore_backup`, [quill/core/backups.py](quill/core/backups.py), [quill/core/recovery.py](quill/core/recovery.py) | Medium | Backups must store enough to restore formatting; recovery must round-trip the rich representation atomically. |
| Undo and redo, including persistent undo | `undo`, `redo`, persistent-undo load and flush, [quill/core/undo_store.py](quill/core/undo_store.py) | High | The rich control has its own undo stack. Reconciling it with QUILL's persistent, cross-session undo is the subtlest engineering problem in the whole proposal. |
| Word count and statistics | `show_word_count`, [quill/core/metrics.py](quill/core/metrics.py) | Low | Metrics run on extracted plain text. |
| Read-aloud and text-to-speech | read-aloud commands and progress handlers, [quill/core/read_aloud.py](quill/core/read_aloud.py) | Medium | Read-aloud reads plain text; an opportunity is to announce formatting boundaries (entering and leaving bold) as a spoken cue. |
| Dictation | dictation commands and handlers, [quill/core/dictation.py](quill/core/dictation.py), [quill/platform/windows/dictation.py](quill/platform/windows/dictation.py) | Medium | Inserted dictated text must land in the rich model with the caret's current formatting. |
| Screen-reader announcements | [quill/core/announcements.py](quill/core/announcements.py), [quill/core/a11y_regions.py](quill/core/a11y_regions.py), [quill/platform/sr_announce.py](quill/platform/sr_announce.py) | High | The defining work. The announcement grammar must grow a vocabulary for formatting so the rich surface is as legible by ear as the plain surface. |
| Soft wrap | soft-wrap toggle and apply, [quill/core/wrap_ops.py](quill/core/wrap_ops.py) | Low | The rich control wraps natively; the toggle maps to a control style. |
| QUILL-key command system | [quill/ui/main_frame_quill_key.py](quill/ui/main_frame_quill_key.py), [quill/core/commands.py](quill/core/commands.py), [quill/core/keymap.py](quill/core/keymap.py) | Medium | Every editor command dispatched through the QUILL key must resolve against the active surface; the dispatch indirection already exists, so this is wiring, not redesign. |
| Dialog estate | Preferences hub, the new surface picker, [dialogs.md](dialogs.md), [tests/unit/ui/fixtures/dialog_inventory.json](tests/unit/ui/fixtures/dialog_inventory.json) | Medium | A surface-choice control and any fidelity-warning dialogs must be registered and classified under the DLG-3 dialog inventory gate. |

### Cross-cutting impacts beyond individual commands

- Settings and the Preferences hub. A new setting, for example
  `editor_surface` with values `plain` and `rich`, registered in
  [quill/core/settings_registry.py](quill/core/settings_registry.py) and surfaced
  as a category in the new Preferences hub. Switching surfaces should be possible
  per document and as a default.
- The Document model. Today the buffer is text. A rich surface needs a
  representation that carries formatting. The least invasive design keeps markup
  as the canonical text and attaches a formatting overlay, so plain-text features
  keep working on the canonical text and the rich control renders the overlay.
- Security. RTF is a historically dangerous format (object packager and embedded
  object abuse, remote image fetches). Any native RTF surface must parse defensively,
  refuse embedded executables and OLE objects, and honor QUILL's no-silent-network
  rule by never fetching a remote resource referenced in an RTF without explicit
  consent. This aligns with the existing egress-audit posture.
- Testing and CI. Because `wx` cannot be imported on Linux CI, the conversion and
  formatting model must live in `quill/io` with pure unit tests, and the control
  itself must be covered by the existing source-contract testing style plus the
  dialog-inventory and public-surface gates. The wx-freedom of `core` and `io`
  must not regress.
- Performance. The PRD sets latency budgets for the editor. A rich control over a
  large document has different performance characteristics; large-file behavior
  must be measured against the existing performance gates before this ships.

### A staged, honest delivery plan

1. Surface protocol first. Refactor `main_frame` so all editor access goes
   through an editor-surface protocol, with the existing `wx.TextCtrl` as the only
   implementation. No user-visible change. This de-risks everything that follows
   and is independently valuable.
2. Rich model in `quill/io`. Extend the RTF model so a formatted document can be
   represented, converted, and tested without `wx`.
3. Read-only rich preview. Ship a rich *view* of a document before a rich
   *editor*. Lower risk, immediately useful, and it exercises the announcement
   grammar for formatting.
4. Opt-in rich editor. Introduce the `wx.RichTextCtrl` surface behind a feature
   flag and the new setting, defaulting off, with a frank accessibility note in
   the picker.
5. Fidelity and safety polish. Lossy-conversion warnings, sidecar preservation,
   RTF sanitization, and the spoken formatting vocabulary.

### Opening files: the moment the design lives or dies

Everything above is plumbing. The place a writer actually meets this design is the
instant they open a file. If that moment is confusing ("why is this file showing
markup characters?" or "why did my headings turn into hash marks?"), the feature
fails no matter how elegant the internals are. So the open and save experience
deserves its own design, and it can be genuinely magical.

#### The one principle that prevents all confusion

The file chooses the surface, the writer can override, and QUILL always says which
lens you are in. Stated as three promises:

- A file opens in the surface that fits its nature, automatically.
- The writer can flip to the other lens at any time with one command, on a
  per-document basis, without losing a word.
- QUILL announces the active surface on open and on every switch, so a
  screen-reader user is never guessing.

That last promise is the accessibility heart of it. The status bar shows the lens
("Plain" or "Rich"), and the announcement grammar speaks it: "Opened report.rtf,
Rich text lens."

#### How each kind of file behaves on open

There is no separate "open as plain" versus "open as rich" file picker. There is
one Open command. QUILL inspects what you opened and does the obvious right thing,
then tells you what it did.

| You open | Default surface | What QUILL says and offers |
| --- | --- | --- |
| A plain text file (`.txt`, `.md`, `.markdown`, code) | Plain | Opens exactly as today. No change whatsoever for existing users. |
| An `.rtf` file, with the rich surface available | Rich | "Opened in Rich text lens." A single command flips to Plain to see or edit the underlying markup. |
| An `.rtf` file, with the rich surface turned off | Plain (markup) | Behaves like today's EDS-21 round-trip, and offers a one-key "Open in Rich text lens" if the writer wants formatting. |
| A rich format QUILL can import (`.docx`, `.odt`, `.pages`) | Plain by default, Rich if opted in | QUILL says how it imported and whether formatting was simplified, with a link to view details. |
| A non-text file (`.pdf`, image for OCR, spreadsheet) | Plain (extracted text) | Unchanged; these are read or extracted into text and never pretend to be rich documents. |

The key insight: the writer's default-surface preference is a *fallback*, not a
mandate. An `.rtf` is inherently a rich document, so it opens rich when rich is
available, even if the writer's default is plain, because that is the least
surprising thing. The preference only decides the ambiguous cases.

#### Making the choice effortless, not a chore

A few touches turn a potential annoyance into something that feels considerate:

- Remember per file. If you opened `journal.rtf` in Plain last time, QUILL
  reopens it in Plain and says so. The decision is sticky per document, stored in
  the same schema-validated JSON used for other per-document state, so you only
  ever decide once.
- One command to flip lenses. A single QUILL-key command, "Switch editing lens,"
  toggles Plain and Rich for the current document, announces the new lens, and
  keeps the caret on the same word. No dialog, no reload.
- No dead ends. Every flip is reversible and lossless within a session, because
  the canonical markup-plus-overlay model holds both views at once. You can move
  back and forth freely while you decide which you prefer for this file.
- Speak the consequence before a lossy save, never after. If saving the current
  lens to the chosen file type would drop something (for example, saving a richly
  formatted document down to `.txt`), QUILL says exactly what will be flattened and
  offers to keep a sidecar copy in a faithful format. This reuses the no-silent-loss
  promise from the fidelity stage.

#### Saving: the mirror image, equally calm

Saving follows the same "least surprise, always announced" rule.

- Save keeps the file's own format. An `.rtf` saves as RTF, a `.md` saves as
  Markdown, regardless of which lens you were editing in, because the lens is a
  *view*, not the file's identity.
- Save As is where format genuinely changes, and that is the right place for a
  clear, accessible format picker with a spoken fidelity note ("Saving as plain
  text will remove bold, italic, and headings. Keep a Rich copy too?").
- The dirty-state, autosave, and backup machinery all operate on the canonical
  model, so switching lenses never marks a document dirty by itself and never
  risks a recovery that loses formatting.

#### Why this is magical and not just tolerable

The ordinary version of this feature forces a mode decision on the user and then
punishes wrong guesses with lost formatting. The QUILL version removes the
decision in the common cases, makes it one reversible keystroke in the rare cases,
keeps both views of the document alive at once so nothing is ever lost, and speaks
every state and consequence aloud so a blind writer navigates it with exactly the
same confidence as a sighted one. A writer opens their file and it simply looks
right, sounds right, and saves right. That is the magic: the two surfaces feel like
one calm editor that happens to know when to show formatting.

### Recommendation

Pursue it, but as a protocol-first refactor that delivers value at every stage,
and keep the plain-text surface the default and the fully-supported path. The
rich surface should be a celebrated power-user choice, not a replacement, and its
accessibility story should be told honestly at the moment of opt-in. Done this
way, QUILL becomes the rare app that offers live rich editing and still treats
plain-text, screen-reader-first writing as first class. That is the magic: not
catching up to word processors, but giving blind and low-vision writers a rich
surface that finally speaks formatting out loud.

---

## Part Two: Competitive Study, Ulysses

### Why Ulysses is the right mirror for QUILL

Ulysses is a mature, respected, markup-first writing app for Mac, iPad, and
iPhone, in active development since 2003 and an Apple Design Award winner. Like
QUILL, it bets on markup rather than visual rich editing, keeps the writer's
hands on the keyboard, and produces clean text as output. That shared philosophy
makes it the most instructive comparison: where Ulysses is strong, it validates
QUILL's direction; where QUILL is strong, it shows QUILL's distinct advantage.

The comparison below reflects Ulysses as described on its official site and
feature pages.

### Side-by-side at a glance

| Dimension | Ulysses | QUILL |
| --- | --- | --- |
| Core philosophy | Markup-first, distraction-free, keyboard-driven | Markup-first, screen-reader-first, keyboard-driven |
| Platforms | Mac, iPad, iPhone (Apple only) | Windows first, with a macOS path |
| Accessibility stance | General Apple platform accessibility | Accessibility is the product thesis: NVDA, JAWS, Narrator parity |
| Library and organization | Unified library, groups, filters, keywords | Tabs, profiles, bookmarks, headings outline, quick navigation |
| Writing goals | Deadlines, daily goals, character and word targets | Word count and statistics |
| Proofreading | Built-in grammar and style check, 20-plus languages | Spellcheck, with AI assistance as explicit opt-in |
| Export and publishing | PDF, Word, ebook, plus WordPress, Ghost, Medium, Micro.blog | Pandoc-backed multi-format export and conversion |
| Sync | Seamless first-party cloud sync across Apple devices | Local-first storage, privacy-first |
| Privacy posture | Cloud library by design | No silent network calls, explicit consent per action |
| AI | Limited | Opt-in assistant, branchable sessions, local-first options |

### What Ulysses does that QUILL can learn from

These are the ideas worth bringing into QUILL, each reframed through QUILL's
accessibility-first, privacy-first, plain-text-first lens so it arrives as a QUILL
feature rather than a transplant.

#### Writing goals you can hear

Ulysses lets a writer set a deadline and a daily or per-document target and watch
progress fill toward it. QUILL has word count and statistics but not goals as a
first-class, motivating object. The magical QUILL version is a *spoken,
glanceable* goal: set a target by voice or command, and QUILL announces progress
on demand and at milestones ("halfway to your 800 words", "goal met") through the
existing announcement grammar, with an optional status-bar field. This turns a
visual progress bar into something a blind writer experiences exactly as richly as
a sighted one.

#### Keywords as a navigation and filtering layer

Ulysses attaches keywords to sheets and filters the library by them. QUILL has
headings, bookmarks, and profiles, but not lightweight, user-defined tags that cut
across documents. A QUILL keyword system, stored in schema-validated JSON and fully
keyboard and screen-reader navigable, would let a writer mark passages or files
("research", "todo", "chapter-3") and then jump or filter by tag through the quick
navigation surface. The magic is making tags audible and command-driven rather
than a mouse-driven sidebar.

#### A unified, navigable library

Ulysses keeps every text in one searchable library that syncs everywhere. QUILL is
file-and-tab oriented. Without abandoning local-first files, QUILL could offer an
optional library *view*: a single accessible list or tree across a writer's
project folders, with type-ahead, keywords, and goals visible, built from the same
stock-control, first-letter-navigable patterns QUILL already favors. It is the
Edge-style list pattern QUILL just adopted for Preferences, applied to a writer's
whole corpus.

#### Built-in style and grammar assistance, on QUILL's terms

Ulysses ships an integrated proofreader across many languages. QUILL has
spellcheck and an opt-in AI assistant. The recommendation is not to bolt on a
cloud grammar service; it is to make style and grammar suggestions a *local-first,
consent-gated* capability that announces each suggestion and never sends text
anywhere without explicit per-action consent, consistent with QUILL's egress rules.
Ulysses proves writers want this; QUILL can offer it without surrendering privacy.

#### Frictionless, beautiful export with live preview

Ulysses turns text into polished PDF, Word, and ebooks with on-the-fly style
switching and live preview. QUILL already has strong Pandoc-backed export. The
borrowable idea is the *experience*: a single command that previews the chosen
output format and lets the writer switch styles before exporting, with the preview
itself accessible. QUILL's advantage is that its preview can be screen-reader
legible, which a purely visual preview is not.

#### Distraction-free focus as an announced mode

Ulysses is built around a calm, distraction-free interface. QUILL can offer a
focus mode that does more than hide chrome: it can announce entry and exit, mute
non-essential notifications, and optionally narrow read-aloud to the current
paragraph, making focus a multi-sensory state rather than a visual one.

### What QUILL should deliberately not copy

- Apple-only reach. Ulysses is Apple-exclusive. QUILL's Windows-first,
  screen-reader-first mission is its differentiation; that should not change to
  chase Ulysses' aesthetic.
- Cloud-library-by-default. Ulysses assumes a synced cloud library. QUILL's
  local-first, no-silent-network posture is a feature, not a gap. Any library or
  sync work must stay opt-in and consent-gated.
- Subscription-shaped feature gating. Pricing strategy is out of scope here, but
  QUILL should not let a feature's design be distorted by a paywall the way some
  Ulysses capabilities are.

### Where QUILL already beats Ulysses

It is worth naming QUILL's lead so the roadmap protects it.

- Screen-reader-first design. Ulysses inherits platform accessibility; QUILL is
  engineered around it, with a shared announcement grammar and parity across NVDA,
  JAWS, and Narrator.
- Privacy by architecture. No silent network calls and explicit per-action
  consent are guarantees Ulysses does not make.
- Branchable AI writing sessions. QUILL's resumable, forkable session tree is a
  genuinely novel capability with no Ulysses equivalent.
- Windows reach. QUILL serves a platform and an audience Ulysses does not.

### Recommended priorities from this study

In rough order of value-to-effort for QUILL's audience:

1. Spoken writing goals, building on the existing metrics and announcement
   surfaces. High value, modest effort, distinctly QUILL.
2. Keyword tags with audible navigation and filtering, reusing the quick
   navigation and schema-validated JSON storage patterns.
3. An optional accessible library view across project folders, reusing the
   first-letter-navigable list pattern.
4. Consent-gated, local-first style and grammar suggestions that announce each
   finding.
5. An accessible export preview with on-the-fly style switching.
6. An announced, multi-sensory focus mode.

Each of these takes a proven Ulysses idea and re-expresses it as something a blind
or low-vision writer experiences fully, which is exactly the territory where QUILL
should aim to be not just competitive but singular.

---

## Part Three: Compose Mode, a Workshop for Assembling Documents

### The idea in one sentence

Add an optional Compose mode where a document is built from a list of parts (call
them segments, QUILL's answer to Ulysses sheets), each part holding a chunk of
writing or a pulled-in source, where the writer reorders parts, promotes and
demotes their heading levels, and merges them into one finished document, while a
live HTML preview shows the assembled whole in real time, and the parts can be
written in Markdown, RTF, or HTML.

This is the writing-as-architecture idea that David Hewson praised in Ulysses
("shuffle around the many different parts and scenes"), rebuilt so a screen-reader
user can architect a document by ear with exactly the same fluency as by eye.

### What a writer actually does in Compose mode

Picture a long piece: a report, a thesis chapter, a book section. Instead of one
unbroken file, the writer sees an accessible list of parts:

- Introduction
- Background (pulled from `research-notes.md`)
- Method
- A quoted source (pulled from an `.rtf` a colleague sent)
- Findings
- Conclusion

Each part is a real, editable unit. The writer can:

- Reorder parts. Move "Method" above "Background" and the whole document
  reflows, the preview updates, and QUILL announces "Moved Method to position 3 of
  6."
- Re-level headings. Promote a part so its heading becomes a top-level section,
  or demote it so it nests under the part above. QUILL announces "Background is
  now heading level 2, nested under Introduction."
- Pull sources together. Add a part that references another file (Markdown, RTF,
  or HTML) so material from many places is gathered into one outline without
  copy-paste drift. The source can be embedded (frozen copy) or linked (kept in
  sync), and QUILL says which.
- Mix formats per part. One part can be Markdown, the next RTF, the next HTML.
  Compose mode normalizes them through QUILL's existing conversion layer so the
  assembled document is coherent.
- Merge to a single document. When the architecture is right, "Flatten to
  document" produces one ordinary file in the writer's chosen format, with heading
  levels already correct.

### The structure tree: the document as a navigable outline

A flat list of parts is good; a tree is magical, and it is the natural fit for
QUILL because the codebase already proves the pattern. QUILL ships an accessible
tree-navigator (`_NavigatorNode` and `_show_tree_navigator` in
[quill/ui/main_frame.py](quill/ui/main_frame.py)) used today for the heading
outline, EPUB chapters, and the misspelling list, and a tree-based *structure
editor* (the YAML editor) that already performs add-child, add-sibling, rename,
and delete on a `wx.TreeCtrl` with a live preview beside it. Compose mode should
reuse this exact, battle-tested pattern rather than invent a new surface.

Represented as a tree, the part list becomes the document's true shape:

- Introduction
- Method
  - Participants
  - Materials
- Background
- Findings
  - Quantitative
  - Quoted source (from a colleague's RTF)
- Conclusion

A `wx.TreeCtrl` is a first-class accessible control (it sits in the dialog
contract's preferred-focus list), and on Windows, macOS, and Linux it gives blind
writers what sighted writers get from an indented outline: nesting they can feel.

- Arrow keys walk the structure. Up and down move between parts, right expands a
  part to hear its children, left collapses to hear just the section. Screen
  readers announce level and position natively ("Method, level 1, expanded, 2 of
  6; Participants, level 2, 1 of 2").
- Collapsing a branch hides a whole sub-section so a writer can think at the
  chapter level, then expand to drop into detail, the outliner's core joy.
- The tree is the document. Reordering a node reorders the prose; promoting a node
  re-levels its heading; moving a parent carries its children. There is no
  separate outline to drift out of sync.
- Each node speaks its essentials on focus: title, heading level, child count,
  word count, format (Markdown, RTF, or HTML), and link-or-embedded state, all in
  the shared announcement grammar.

The rich context menu described next hangs directly off this tree, and the live
HTML preview sits beside it exactly as the YAML editor places a preview beside its
structure tree, so moving a node and hearing the reflowed result is one gesture.

### The live HTML preview, made accessible

A real-time HTML preview is the visual half of the magic. The accessible half is
making that preview meaningful without sight.

- The preview renders the assembled document as HTML and updates as parts move or
  change, reusing QUILL's existing HTML preview path.
- Crucially, the preview is screen-reader legible: it is presented as structured,
  navigable text (headings, lists, links exposed as real semantics), not as an
  opaque image of a page, so a screen-reader user can read the assembled result by
  heading and by element just like the final document.
- A spoken structure summary is one keystroke away: "6 parts, 4 top-level
  headings, estimated 2,300 words, reading order: Introduction, Method,
  Background..." so the writer hears the shape of the whole before diving in.
- Preview and parts stay in sync both ways: jumping to a heading in the preview
  offers to jump to the part that produced it, closing the loop between the
  architecture view and the reading view.

### Why this is delightful, not just powerful

- Nothing is lost while you experiment. Reordering and re-leveling operate on the
  part list, never by destructively cutting and pasting text, so every arrangement
  is reversible and the writer can try three structures in a minute.
- The outline is the document. There is no separate, drifting outline pane to
  maintain; the part list *is* the outline, and editing the outline edits the
  document.
- It speaks architecture. Every structural action has a spoken outcome in the
  shared announcement grammar, so "move this section earlier" is a confident,
  audible act rather than a fragile drag.
- It meets writers where their material is. Markdown notes, an RTF from a
  colleague, an HTML snippet from the web can all become parts without first being
  converted by hand.

### The right-click that builds a document: a rich, spoken context menu

Reordering and re-leveling should not require remembering commands. The fastest,
most direct way to architect a document is to act on the part you are standing on,
and the context menu is where that lives. In Compose mode, invoking the context
menu on a part (by right-click, by the keyboard context-menu key, or by QUILL's
own context command) opens a structure menu that is the command center for the
whole assembly. Every item is keyboard reachable, every item announces its
outcome, and destructive items confirm.

The menu is organized so the most common architectural moves are at the top:

| Menu item | What it does | What QUILL announces |
| --- | --- | --- |
| Move Up / Move Down | Swaps this part with its neighbor | "Moved Method up to position 2 of 6." |
| Move to Top / Move to Bottom | Jumps this part to the start or end | "Moved Conclusion to the end, position 6 of 6." |
| Move to Position... | Accessible entry to type or pick an exact slot | "Moved Background to position 3 of 6." |
| Promote (heading level up) | Raises this part's heading one level, outdenting it | "Background is now heading level 1, a top-level section." |
| Demote (heading level down) | Lowers this part's heading one level, nesting it | "Background is now heading level 3, nested under Method." |
| Make Top-Level Section | Sets this part to heading level 1 in one step | "Introduction is now a top-level section." |
| Group Under Previous | Nests this part (and re-levels it) beneath the part above | "Grouped Findings under Method." |
| Promote With Children / Demote With Children | Re-levels this part and everything nested under it together | "Promoted Method and its 3 sub-parts." |
| Change Format... | Switches this part between Markdown, RTF, and HTML | "Changed Background to HTML." |
| Convert Link to Embedded Copy | Freezes a linked source so it stops tracking the original | "Background is now an embedded copy." |
| Refresh Linked Source | Re-pulls a linked source's latest content | "Refreshed Background from research-notes.md." |
| Split Part Here / Merge With Previous | Breaks one part into two at the caret, or fuses two | "Split into Method and Method, part 2." |
| Duplicate Part | Copies the part as a new sibling | "Duplicated Findings." |
| Rename Part | Accessible text entry for the part's outline label | "Renamed to Literature Review." |
| Add Keyword to Part... | Tags this part (see Part Four) | "Added keyword research to this part." |
| Preview This Part | Jumps the live HTML preview to this part | "Previewing Findings." |
| Flatten From Here... | Merges this part and those after it into a document | spoken summary of the flattened result |
| Remove Part | Deletes the part (with confirm) | "Removed Background. 5 parts remain." |

#### What makes this context menu magical rather than ordinary

- It speaks position and consequence, always. Every move and re-level reports the
  new position out of the total and the resulting heading relationship, so a
  screen-reader user never has to re-read the list to discover what happened. The
  menu is a place where you act and immediately *hear* the new shape.
- It re-levels structurally, not cosmetically. Promote and Demote understand
  nesting: "Promote With Children" lifts an entire subtree so a writer can move a
  whole sub-section up a level in one act, and QUILL announces how many parts moved
  with it. This is the difference between editing an outline and merely nudging
  text.
- It is context-aware. Items that cannot apply are absent or clearly disabled with
  a spoken reason: "Move Up unavailable, Introduction is already first." "Refresh
  Linked Source unavailable, this part is an embedded copy." No dead clicks, no
  silent no-ops.
- It mirrors keyboard commands exactly. Every menu item has a QUILL-key binding so
  power users never need the menu, and the menu never hides a capability the
  keyboard lacks. The context menu and the command system are two doors to one
  room.
- It keeps focus sane. After a move, focus stays on the part that moved (now in its
  new position) so repeated presses of "Move Up" walk a part smoothly toward the
  top, each step announced, exactly the predictable behavior the repository's
  dialog and focus rules require.
- It confirms only what is destructive. Reordering and re-leveling are instantly
  reversible and never prompt; Remove Part and a flatten that would overwrite a
  file confirm through a native accessible dialog. Friction lands only where loss
  is possible.

#### Beyond the single part: acting on a selection

The magic compounds when the writer selects several parts in the list. The same
context menu then operates on the whole set, spoken as a set: "Move 3 parts up,"
"Demote 3 parts," "Group 3 parts under Introduction," "Add keyword research to 3
parts." A scattered draft becomes a structured manuscript in a handful of audible,
reversible gestures, all from the one context menu every editor estate already
makes feel familiar.

This context menu must, like all QUILL dialogs and menus, be registered and
classified under the DLG-3 dialog and menu estate, with no menu items mutated while
the menu is open (deferring label and enable updates until close), per the
repository's dialog and menu lessons.

### How Compose mode fits QUILL's architecture

This respects the same boundaries as the rest of this document.

- The part-list model, reordering, heading-level math, and the flatten-to-document
  logic are pure and live in `quill/core` and `quill/io`, free of `wx` and fully
  unit-testable on Linux CI. They build directly on the existing outline, heading,
  and conversion modules ([quill/core/outline.py](quill/core/outline.py),
  [quill/core/heading_styles.py](quill/core/heading_styles.py),
  [quill/io/pandoc.py](quill/io/pandoc.py), and the RTF and HTML io paths).
- The Compose surface itself (the accessible part list, the editor for the
  selected part, and the live preview) lives in `quill/ui`, built from stock,
  first-letter-navigable list controls, the same patterns QUILL already favors.
- It honors FeatureManager as an opt-in mode, the dialog-inventory gate for any
  new dialogs, and the no-silent-network rule for any linked remote source.
- A composition is persisted as schema-validated JSON (the ordered part list with
  each part's source, format, embed-or-link choice, and heading level), with atomic
  writes and backup or recovery parity, so an assembly is as robust as any other
  QUILL document.

### Honest constraints

- Mixed-format flattening is only as faithful as the conversions beneath it; the
  same no-silent-loss warnings from Part One apply when a part's formatting cannot
  survive the chosen output format.
- A real-time preview of a large multi-part document must respect QUILL's
  performance budgets; the preview should update incrementally rather than
  re-rendering the world on every keystroke.
- Linked (live) sources introduce freshness and trust questions; linked external
  content must follow the existing untrusted-location and egress-consent rules.

---

## Part Four: Accessible Keywords for Screen-Reader Users

Keywords (tags) recur through this document as a borrowed Ulysses strength. They
are only worth building if they are fully usable by ear, so they deserve their own
design. The goal: tagging and tag-navigation that a screen-reader user performs as
fluently as a sighted user clicks a colored label.

### What a keyword is in QUILL

A keyword is a short, user-defined label ("research", "todo", "chapter-3",
"verify") attached to a whole document or to a specific part or passage. Keywords
are stored in schema-validated JSON alongside other per-document state, never
embedded invisibly in the prose, so they never pollute the text a screen reader
reads.

### Assigning keywords by ear

- A single command, "Add keyword," opens an accessible entry with type-ahead over
  existing keywords, so the writer reuses "research" rather than inventing
  "reserach". The field announces matches as they narrow.
- Assigning announces the outcome: "Added keyword research to this section. This
  section now has two keywords: research, verify." The writer always hears the
  resulting state, not just the action.
- Removing is symmetric and equally spoken: "Removed todo. One keyword remains:
  research."
- Keywords on a passage are anchored to that passage's position, and QUILL speaks
  where they live ("keyword verify spans the selected sentence") so they are never
  invisible floating state.

### Hearing which keywords are present

The hardest part of tags for a screen-reader user is usually discovery: sighted
users see colored chips at a glance. QUILL replaces the glance with sound and
structure.

- On entering a tagged document or part, QUILL can announce its keywords as part
  of the context, configurably, for example "Findings, keywords: research,
  verify."
- A "Read keywords here" command speaks the keywords at the caret on demand,
  so the information is available the instant it is wanted and silent when it is
  not.
- A status-bar field can carry the current location's keyword count, and reading
  that field aloud is already a supported QUILL action.

### Navigating by keyword

This is where keywords become a navigation superpower rather than mere labels.

- "Go to keyword" opens an accessible, first-letter-navigable list of all
  keywords with their occurrence counts ("research, 7; todo, 3; verify, 2").
  Choosing one lists every place it appears, each entry spoken with its document,
  section, and a short context snippet.
- "Next keyword" and "Previous keyword" jump between occurrences of a chosen tag
  the way heading navigation jumps between headings, each landing announced with
  its surrounding context.
- A keyword filter can scope the accessible library view and Compose mode part
  list to just the tagged items ("showing 7 parts tagged research"), turning a
  sprawling project into a focused working set, entirely by keyboard and entirely
  spoken.

### Why this is the accessible version Ulysses never built

Ulysses keywords are fundamentally visual: chips you scan and click. QUILL's
keywords are spoken objects you can add, hear, filter, and jump through without
ever seeing them. Every keyword action has an audible outcome, every keyword
location is announced rather than implied, and discovery is a command away instead
of a visual scan. That is the through-line of this entire document applied once
more: take a feature the industry built for the eye and make QUILL the place where
it finally speaks.

---

## Part Five: Embedded Grammar Checking, and How It Understands Language

Grammar checking is the most technically ambitious idea in this document, and the
honest framing matters: spelling asks "is this token a word?" while grammar asks
"is this sentence well-formed, and why?" The second question requires the software
to understand the *structure* of language, not just a wordlist. This part explains
how QUILL would gain that understanding, how it would surface findings through the
same accessible machinery QUILL already uses for spelling, and where the real
complexity and the honest limits lie.

### Spelling is the proven template to build on

QUILL already has the right shape. [quill/core/spellcheck.py](quill/core/spellcheck.py)
is a pure, `wx`-free pipeline: `list_misspellings` returns typed `Misspelling`
records with `start` and `end` offsets, `next_misspelling` and
`previous_misspelling` walk them efficiently from the caret, `misspelling_at_position`
identifies the issue under the cursor, and `suggest_words` offers fixes. The UI
layer turns those records into navigation, a context menu, and the misspelling tree
navigator. Grammar checking should mirror this contract exactly: a pure core engine
that returns typed issue records with offsets, a category, an explanation, and
suggested rewrites, and a UI that reuses QUILL's existing navigation, dialog, and
announcement surfaces. If grammar issues look like richer misspellings to the rest
of the app, the integration cost collapses.

### How a computer understands grammar and parts of speech

This is the core of your question. There is no single trick; there is a pipeline,
and QUILL can choose how far down it to go based on cost and accuracy. Each stage
turns raw text into more structure than the last.

1. Tokenization and sentence segmentation. Split text into sentences and words,
   handling abbreviations, decimals, and punctuation. QUILL already has word and
   line tokenizing patterns to build on.
2. Part-of-speech tagging. Label each token with its grammatical category: noun,
   verb, adjective, determiner, preposition, and finer tags (singular noun, past
   tense verb, comparative adjective). This is how the software knows that in
   "the dog runs," "dog" is a singular noun and "runs" is a singular present-tense
   verb, which is what lets it judge subject-verb agreement. POS tagging is a
   solved, well-understood task: a tagger is trained on large hand-labeled corpora
   and learns the probability of each tag given the word and its neighbors.
3. Morphological analysis. Determine number (singular or plural), tense, and
   person from word forms, so the checker can compare "dog/dogs" or "run/runs/ran."
4. Shallow or full parsing. Group tagged words into phrases (noun phrase, verb
   phrase) and, in fuller form, build a dependency tree linking each word to the
   word it modifies or agrees with. The dependency link between subject and verb is
   precisely what an agreement rule inspects.
5. Rule and model checking. With tags and structure in hand, the checker applies
   rules ("a singular subject takes a singular verb"; "this preposition does not
   fit this verb") and statistical signals (this n-gram is improbable) to flag
   likely errors and propose fixes.

The crucial idea: parts of speech are the bridge. Once every word carries an
accurate grammatical tag and the words are linked into phrases, most common grammar
checks become tractable rules over that tagged structure rather than guesses over
raw characters.

### Don't build the engine, adopt one: the open-source options

The first instinct, a hand-written ruleset, is a trap. Real grammar checking is
years of linguistic work, and several mature open-source engines already exist.
The honest job is to pick the one whose language understanding, license, runtime,
and privacy posture fit QUILL, then wrap it. The survey below reflects each
project as of mid-2026.

| Engine | Language stack | License | Offline and private | Coverage | Honest fit for QUILL |
| --- | --- | --- | --- | --- | --- |
| Harper (Automattic) | Rust core, callable from Python via a PyO3 binding | Apache-2.0 | Yes, fully local by design | English only today; real POS tagging (its `harper-brill` tagger) and many rules | Strongest fit. No Java, no VM, milliseconds per lint, roughly one-fiftieth of LanguageTool's memory. Cost: a compiled native dependency to bundle and sign per platform, and English-only for now. |
| LanguageTool | Java engine, driven from Python by `language_tool_python` | Engine LGPL 2.1+; Python wrapper GPL-3.0 | Yes, but only via a bundled local Java server; the public-API mode sends text off device and must never be used in QUILL | 25-plus languages, thousands of rules, optional large n-gram data | Most complete and multilingual, but requires bundling a Java 17+ runtime and managing a local server subprocess, a heavy footprint for a Python and wxPython app. The GPL-3.0 wrapper and remote-API default are both cautions. |
| spaCy | Pure Python and Cython | MIT | Yes, fully local | Excellent POS tagging and dependency parsing, many languages | Not a grammar checker; it is the structural toolkit you would build rules on top of. Useful if QUILL ever wants its own multilingual structural layer, but it is a build-it-yourself path, not a finished checker. |
| proselint | Pure Python | BSD | Yes, fully local | Style and usage advice, not true grammar | Lightweight and trivially embeddable, but it lints style, not subject-verb agreement; a complement, not the engine. |
| Consent-gated AI | QUILL's existing AI path | n/a | No, sends text off device | Broadest coverage and fluent rewrites | Best raw coverage and style help, but it must be strictly opt-in per QUILL's no-silent-network rule; latency, cost, and non-determinism apply. |

A note on what each actually understands. Harper, LanguageTool, and spaCy all do
genuine part-of-speech tagging and some structural analysis, which is what lets
them catch agreement and tense errors rather than just typos. proselint does not;
it pattern-matches style. A hand-rolled QUILL ruleset would sit below all of them
and is not worth building when Harper exists.

### The recommended path: Harper first, with honest caveats

For QUILL specifically, the leading candidate is Harper. It is open source
(Apache-2.0), offline and privacy-first by design, fast and light enough to run
live in an editor, and it does real POS tagging, which is exactly the
parts-of-speech understanding the checker needs. Crucially for QUILL, it needs no
Java and no virtual machine.

The caveats must be stated plainly, because they drive the engineering:

- Harper is written in Rust, not Python. It is callable from Python through a
  PyO3 binding (`harper-python`, published on crates.io under Apache-2.0), but
  under the hood QUILL would load a compiled native extension and ship a
  per-platform wheel or binary that has to be built and code-signed alongside the
  app. This is the same class of work as any native dependency, just without a
  JVM.
- At the time of writing, the `harper-python` crate is confirmed, but a prebuilt
  PyPI wheel under that name could not be verified; QUILL should confirm the exact
  Python distribution, its API, and platform wheel availability before depending on
  it, and be ready to build the binding from the Rust crate if needed.
- Harper is English-only today. Writers needing other languages would fall back to
  the (heavier, multilingual) LanguageTool engine or to consent-gated AI.

The staged recommendation, then, is engine-led rather than rule-led: wrap Harper
as the default local, private grammar engine behind a feature flag; offer
LanguageTool as an opt-in heavyweight for writers who need its breadth of
languages and rules, bundling its Java server only when enabled; and expose deep,
fluent AI grammar only through QUILL's existing consent gate. spaCy stays in
reserve as the toolkit if QUILL ever wants to grow its own multilingual structural
checks.

### Why this is genuinely complex, stated plainly

You called grammar complex, and that is correct. The honest difficulties:

- Ambiguity is everywhere. "Time flies" can be a noun and verb or an adjective and
  noun; many words are several parts of speech, and the tagger must use context.
- Real grammar needs structure, not just words. Subject-verb agreement can span a
  long clause ("The list of items *is* on the desk," not "are"), so a checker that
  ignores phrase structure gets it wrong.
- False positives erode trust fast. A grammar checker that nags about correct
  sentences is worse than none; tuning for precision over recall matters more than
  raw coverage.
- Language and dialect specificity. Rules and models are per-language, and even
  within English the conventions differ; QUILL must let the writer set the variety.
- Performance under live editing. Re-checking a large document on every keystroke
  is infeasible; the engine must check incrementally around edits, exactly as the
  spelling scanner already works outward from the caret.

### Surfacing grammar through QUILL's existing accessible machinery

Here the earlier request for "keyboard commands, a dialog, and more to help with
all of the document interaction" is answered directly. Grammar reuses every
spelling surface, so a screen-reader user already knows how to drive it.

- Keyboard commands. "Next grammar issue" and "Previous grammar issue" walk
  findings from the caret, each landing spoken with its category and a short
  explanation ("subject-verb agreement, line 12: the subject *list* is singular,
  so use *is*"). "Explain grammar issue here" speaks the full rationale on demand.
  "Apply suggested fix" and "Apply fix and continue" accept a rewrite and move on.
  "Ignore once" and "Ignore this rule" tune the noise. All bind through the
  QUILL-key system and appear in the command palette.
- A grammar dialog. A dedicated, accessible review dialog (native or QUILL's web
  surface, registered under the DLG-3 dialog estate) walks issues one at a time
  with the sentence in context, the category, the plain-language explanation, the
  parts of speech it is reasoning about ("*list*: singular noun; *are*: plural
  verb"), and a list of suggested rewrites the writer can choose from, with Apply,
  Skip, Ignore, and Ignore Rule. This mirrors the existing spell-check dialog so it
  is instantly familiar.
- A grammar tree navigator. The same `_NavigatorNode` tree that lists misspellings
  lists grammar findings grouped by category (Agreement, Tense, Punctuation, Word
  choice), each node spoken with its location and an excerpt, each Enter jumping to
  the occurrence. A writer can survey every structural concern in the document by
  ear, then fix them in order.
- As-you-type, like spelling. An optional live mode flags issues incrementally
  around edits and announces them with the restraint QUILL already applies to
  spelling, never interrupting flow, always available on demand.
- The context menu. Right-clicking a flagged span offers the suggested fixes,
  Explain, Ignore, and Ignore Rule inline, exactly as spelling suggestions appear
  in the editor context menu today.
- Honest, spoken explanations. The defining QUILL difference: every finding is
  explained in plain language and, when useful, names the parts of speech it
  reasoned about, so a writer does not just hear *that* something is wrong but
  *why*, and learns from it. That is grammar checking that teaches, by ear.

### Architecture and where it lives

- The grammar layer is wrapped behind a pure, `wx`-free adapter in `quill/core`
  (for example `quill/core/grammar.py`) that returns typed issue records exactly as
  `spellcheck.py` returns `Misspelling` records, so the rest of the app never sees
  which engine produced a finding. Swapping Harper for LanguageTool or AI is an
  adapter change, not an app change.
- The engine itself (the Harper native binding, or an optional bundled
  LanguageTool server) lives at the platform boundary, loaded lazily with the same
  cache-locking discipline the spelling wordlist uses and with background preload
  so the first check never stalls the editor. Because the engine is native and
  cannot be imported on Linux CI, the adapter is tested against a fake engine, and
  the record-shaping logic stays pure and fully unit-tested, mirroring how QUILL
  already keeps wx and other heavy dependencies out of `core` tests.
- All UI (commands, dialog, tree navigator, context menu, announcements) lives in
  `quill/ui` and reuses existing surfaces, so the new code is mostly the adapter
  plus thin wiring.
- The optional AI engine routes only through the existing consent-gated AI path and
  the egress audit; no grammar engine may make a silent outbound call, which also
  means LanguageTool's public-API mode is forbidden and only its bundled local
  server is permitted.
- Feature-flagged through FeatureManager so grammar (and each engine) can be
  enabled per profile.

### Recommendation

Do not hand-roll a grammar checker; adopt a real engine and treat grammar as
"spelling, with structure." The leading choice for QUILL is Harper: open source
(Apache-2.0), offline, privacy-first, fast enough to run live, real POS tagging,
and no Java. Accept its honest costs (a Rust native binding to package per
platform, English-only for now, and a Python distribution to verify) and wrap it
behind a pure `quill/core` adapter that emits the same typed records as
spellcheck. Offer LanguageTool as an opt-in multilingual heavyweight (bundled
local Java server only, never its remote API), keep spaCy in reserve as a
structural toolkit, and expose fluent AI grammar only through QUILL's existing
consent gate. Whichever engine answers, make the finding *speak its reasoning*,
parts of speech included, so QUILL becomes not just a grammar checker but the rare
one a blind writer can fully hear, interrogate, and learn from.

---

## Closing note

Part One argues QUILL can host a rich surface without betraying its plain-text,
screen-reader-first heart, provided it refactors to an editor-surface protocol
first and keeps the rich control an honest, opt-in power mode. Part Two argues the
best ideas in the category's most admired markup app, Ulysses, can each be brought
into QUILL in a form that is more accessible than the original. Part Three proposes
Compose mode, a workshop that assembles a document from reorderable, re-levelable
parts across Markdown, RTF, and HTML with a live, screen-reader-legible HTML
preview and a rich spoken context menu for architecting structure by ear. Part
Four designs keywords as spoken objects a writer can add, hear, filter, and jump
through without ever seeing a chip. Part Five shows how grammar checking can
understand parts of speech and sentence structure, in tiers from a private local
ruleset to opt-in AI, and surface every finding, reasoning included, through the
same accessible commands, dialog, and tree QUILL already uses for spelling.

The throughline of all five is one ambition: take features the rest of the
industry built for the eye, and make QUILL the place where they finally speak.
