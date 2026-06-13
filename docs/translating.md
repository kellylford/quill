# Translating QUILL — Community Contributor Guide

This guide is for anyone who wants to help translate QUILL into their language.
QUILL uses Crowdin for community translation. You do not need any programming
knowledge to contribute.

---

## Joining as a Translator

1. Create a free account at [crowdin.com](https://crowdin.com) if you do not
   already have one.
2. Go to the QUILL project at crowdin.com/project/quill.
3. Click the language you want to translate.
4. Click Join to request access.
5. A Language Coordinator for your language will approve your request, usually
   within a few days.

If no Language Coordinator exists yet for your language, open a GitHub issue
with the label `translation` and express your interest. The Translation
Coordinator will guide you through setting up a new language team.

---

## The Four Roles

| Role | What you do | Accounts needed |
|---|---|---|
| Translator | Suggest translations for strings in Crowdin | Crowdin only |
| Proofreader | Approve or reject translation suggestions for your language | Crowdin only |
| Language Coordinator | Manage proofreaders, own language quality, review GitHub PRs for your language | GitHub and Crowdin |
| Translation Coordinator | Project-level role: run translation calls before each release, onboard new language teams, resolve disputes | GitHub and Crowdin |

To apply for Proofreader or Language Coordinator, open a GitHub issue with the
label `translation`. Describe your language, your qualifications, and whether
you use a screen reader yourself. Existing experience with NVDA, JAWS, or
other assistive technology is a strong plus.

The Translation Coordinator is a named maintainer role listed in `MAINTAINERS.md`.
It is not a casual volunteer position. The Translation Coordinator must be
available before every release.

---

## The Translation Workflow

1. Strings are extracted from QUILL source code using Babel and uploaded to
   Crowdin automatically when a new commit lands on `main`.
2. Translators suggest translations in the Crowdin editor.
3. Proofreaders review suggestions and mark them as approved or rejected.
4. When strings are approved, Crowdin opens an automatic pull request to the
   QUILL GitHub repository.
5. The CI gate (`check_translation.py`) runs on the pull request. It checks
   completeness, mnemonic preservation, and placeholder preservation.
6. A code maintainer merges the pull request. The compiled `.mo` file ships
   in the next QUILL release.

---

## What You Are Translating — The Three Crowdin Components

**Component 1: UI Strings**
All menus, dialog labels, button text, status bar messages, and screen reader
announcement strings. This is the largest component and the highest priority.

Source file: `quill/locale/quill.pot`
Target files: `quill/locale/{lang}/LC_MESSAGES/quill.po`

**Component 2: Context-Sensitive Help**
The 109+ help topics that appear when the user presses F1 on any control.
Each topic has a title and a body paragraph. Translating this component makes
the in-app help accessible in your language.

Source file: `quill/core/help/topics.json`
Target files: `quill/core/help/topics_{lang}.json`

**Component 3: Quillin Manifests**
The name and description of each bundled QUILL extension (Quillin). Short
strings but high visibility, as they appear in the Extensions menu and the
Quillin Manager.

Source files: each bundled `manifest.json`
Target files: `manifest_{lang}.json` alongside each manifest

---

## Translation Calls Before Each Release

Before each QUILL release, the Translation Coordinator sends a translation
call to all Language Coordinators. The call includes:

- The deadline (typically two weeks before the release branch is cut).
- A list of new or changed strings since the last release.
- The current completeness percentage for each language.
- The threshold required to ship: 90% for established languages, 70% for a
  new language in its first release.

Languages that miss the deadline or fall below the threshold are excluded from
that release. The startup wizard's language selector does not show excluded
languages. This protects users from encountering a partially translated
interface.

If your language misses a release, it can catch up and ship in the next one.

---

## Completeness Thresholds

- 90% for an established language (one that has shipped in a previous release).
- 70% for a new language in its very first release.

Languages below the threshold are shown in the language selector with a
warning: "This translation is incomplete — some text will appear in English."
This warning is shown rather than hiding the language entirely, so users who
prefer even a partial translation can still choose it.

---

## Testing Your Translation Locally

You can test your translation before it is merged by following these steps.

1. Clone the QUILL repository:
   `git clone https://github.com/bits-dev/quill.git`

2. Install QUILL in development mode:
   `pip install -e ".[ui,dev]"`

3. If you are working on a `.po` file obtained from Crowdin, place it at:
   `quill/locale/{lang}/LC_MESSAGES/quill.po`

4. Compile the `.po` file to a `.mo` binary:
   `pybabel compile -d quill/locale -D quill`

5. Open QUILL settings and set `language` to your language code, for example
   `fr` for French.

6. Launch QUILL:
   `python -m quill`

7. Navigate the UI and verify that your translations appear correctly. Pay
   particular attention to:
   - Menu mnemonics (the underlined shortcut letters in menus)
   - Announcement strings (what your screen reader says during actions)
   - Plural forms (for example, "1 word" vs. "3 words")

---

## The QUILL Product Glossary

The following terms are QUILL product names. Your Language Coordinator decides
whether to translate them or leave them in English. The Crowdin glossary records
the decision for your language. Once the decision is made, use it consistently.

| Term | Notes |
|---|---|
| Copy Tray | QUILL's multi-slot clipboard feature |
| Ask Quill | The AI assistant dialog |
| Quillin | A QUILL extension |
| Quick Nav | The rapid in-document navigation mode |
| Skill Library | The library of AI-powered writing skill packs |
| Prompt Library | The library of saved AI prompts |
| GLOW | QUILL's guided-learning workflow system |

If you are unsure whether to translate a term, ask your Language Coordinator
or open a GitHub issue with the label `translation`.

---

## Translator Credit

Translator names appear in the QUILL release notes for each release in which
their work ships. If you would prefer to be listed by a username rather than
your real name, set your Crowdin display name accordingly before your
translations are merged.

---

## Where to Ask Questions

- Open a GitHub issue with the label `translation`.
- Post in the QUILL community forums under the Translation category.

The Translation Coordinator monitors both channels and aims to respond within
three business days.


---

# Appendix: Translation style guide

_Folded in from the former docs/TRANSLATION_STYLE_GUIDE.md on 2026-06-13._

# QUILL Translation Style Guide

This document gives rules and guidance for translating QUILL's user interface.
Read it before you begin translating and return to it when you have questions
about a specific type of string.

---

## Tone and Register

QUILL speaks to the user in the second person, directly. Use "your document",
"press this key", not "the user's document" or "one presses this key."

Match the register of the target language's screen reader ecosystem:
- French: use "vous" (formal) unless the French language community explicitly
  votes for "tu". Crowdin glossary records the decision.
- German: use "Sie" (formal) by default.
- For other languages, follow the convention used by NVDA's official translation
  into your language.

If you are uncertain about the appropriate register, ask your Language
Coordinator before translating strings in bulk.

---

## Mnemonic Markers (`&`)

A mnemonic marker is the `&` character that appears before one letter in a
menu item or button label. It creates a keyboard shortcut: Alt plus that
letter activates the menu item or button. Screen reader users rely on
mnemonics to navigate menus without using arrow keys.

Rules:
1. Every menu item and button label in QUILL has exactly one `&`.
2. When you translate a string that contains `&`, your translation must also
   contain exactly one `&`.
3. Place the `&` before a letter that is unique within the same menu or dialog.
   Two items in the same menu must not share the same mnemonic letter.
4. The `&` letter must be a letter that actually appears in your translated
   word, and ideally near the start of the word for discoverability.

If you cannot find a unique letter in the natural word, it is acceptable to
use any letter from the word as the mnemonic, even if it is not the first.
Consult your Language Coordinator if a whole menu has mnemonic conflicts.

The CI gate catches missing or double `&` markers automatically. If your
translation passes CI, the mnemonic count is correct.

---

## Keyboard Shortcuts

Modifier key names are not translated. They appear as printed on the keyboard
in every language:

- Ctrl
- Alt
- Shift
- Enter
- Escape
- Tab
- F1 through F12

A string like `&Open...\tCtrl+O` should become (in French)
`&Ouvrir...\tCtrl+O` — the `\t` accelerator uses the same Ctrl+O shortcut.
The mnemonic `&O` must match the `&` letter in the translated label.

Do not change the key letter in `\t` accelerators. Accelerators are
defined in code and are not affected by translation; only the label's
`&` mnemonic is yours to relocate.

---

## Announcement Strings (Speech Strings)

Announcement strings are the text that QUILL sends to the screen reader
and read-aloud engine. They are marked in the `.pot` file with an extracted
comment:

```
#. SPEECH: announced after copy-to-tray action
msgid "Copied to slot {n}"
```

The `#. SPEECH:` comment is visible in the Crowdin editor as a string note.
Use it to filter speech strings for a dedicated review pass.

Rules for announcement strings:
1. Translate for natural speech, not literal label equivalence. A string that
   makes sense visually may sound unnatural when read aloud. Restructure the
   sentence if needed.
2. Do not abbreviate in speech strings. If the source says "AI", spell it out
   as your language's full term unless the abbreviation is universally
   understood in your language's technology community.
3. Add context if the meaning would be lost without visual UI. "Copied to slot
   3" makes sense visually because the user can see the Copy Tray. In speech,
   "Copied to Copy Tray slot 3" is clearer.
4. Test every announcement string with NVDA set to the target language. Ask a
   native speaker to listen and confirm the announcement sounds natural.

---

## Plural Forms

Follow your language's actual plural rules. Do not guess. Reference the
official gettext plural forms list:
https://www.gnu.org/software/gettext/manual/html_node/Plural-forms.html

The `Plural-Forms` header in your `.po` file must match your language's rules.
If the header is wrong, you will see errors when the CI gate checks your file.

Examples:
- French has two forms: singular for 0 and 1, plural for 2 and above.
  `Plural-Forms: nplurals=2; plural=(n > 1);`
- Russian has four forms.
- English has two forms: singular for 1, plural for everything else.

The CI gate checks that every `msgstr[n]` entry exists for languages with
more than two plural forms.

---

## Placeholders

Placeholders are variable values that QUILL inserts into strings at runtime.
They appear in two forms:

- `{name}` — Python format string: `{count}`, `{filename}`, `{n}`
- `%(name)s` — Old-style format: `%(count)s`, `%(provider)s`

Rules:
1. Never translate a placeholder. `{n}` must remain `{n}` in every language.
2. Never remove a placeholder. If the source has `{count}` words selected`,
   your translation must also have `{count}` in some position.
3. You may reorder placeholders within the sentence to match the grammar of
   your language. `{filename} is open` may become `{filename} est ouvert` or
   `ouvert: {filename}` — the placeholder can move, but it must be present.

The CI gate checks that every placeholder present in the source string is
also present in the translation.

---

## ARIA Roles

ARIA role names (`button`, `dialog`, `listbox`, `menu`, `menuitem`,
`checkbox`, `radiogroup`, `spinbutton`) are technical identifiers used by
assistive technology. Do not translate them, even when they appear inside a
user-visible string.

---

## Technical Identifiers

The following are technical identifiers and must not be translated:

- File extensions: `.qpf`, `.sqp`, `.pqp`, `.po`, `.pot`, `.mo`
- Setting key names: `language`, `setup_wizard_completed`, `feature_flags_ai`
- Command names used in documentation: `open_setup_wizard`, `ask_ai`
- URL paths and domain names

---

## Product Glossary

Refer to the Crowdin project glossary for your language's decisions on product
name translation. See `docs/translating.md` for the full product glossary list.
Once a decision is recorded in the glossary, apply it consistently across all
strings.

---

## Short Example: English to French

**English source string:**

```
msgid "&New document\tCtrl+N"
```

This string:
- Has mnemonic `&N` (N is the first letter of "New").
- Has accelerator `\tCtrl+N`.

**French translation:**

```
msgstr "&Nouveau document\tCtrl+N"
```

- Mnemonic `&N` is placed on "Nouveau" (N is the first letter).
- Accelerator `\tCtrl+N` is unchanged.
- The menu item reads "Nouveau document" with N underlined in the menu.

**A case where the mnemonic must move:**

English: `&Save As...\tCtrl+Shift+S`
French: "Enregistrer sous" — "S" is already used by "Save / Enregistrer".
The Language Coordinator decides to use `Enreg&istrer sous` (mnemonic on `i`)
to avoid a conflict in the File menu. This decision is recorded in the
Crowdin glossary and applied consistently.


---

# Appendix: Translation contributor plan

_Folded in from the former docs/localization/translation-contributor-plan.md on 2026-06-13._

# QUILL Translation Contributor Plan

**QUILL** follows a community-first localization model inspired by NVDA's gettext workflow.

This document is the working plan for contributors who want to help translate QUILL and help maintain translation quality across releases.

## Goals

1. Keep translation contribution easy for first-time contributors.
2. Keep translation quality high enough for daily screen-reader use.
3. Keep release timing predictable with clear string-freeze expectations.
4. Keep translator effort visible and credited in the product and docs.

## Translation model (POT/PO/MO)

QUILL uses GNU gettext catalogs:

- `locale/quill.pot` as the extracted template
- `locale/<lang>/LC_MESSAGES/quill.po` as editable translator source
- `locale/<lang>/LC_MESSAGES/quill.mo` as compiled runtime catalog

Developers write user-facing strings in source code. The extraction step updates `quill.pot`. Translators edit `quill.po`. Build/release compiles `.po` to `.mo`.

## Community contribution workflow

### Phase 1 (current): GitHub pull requests

1. Fork the repository.
2. Create or update `locale/<lang>/LC_MESSAGES/quill.po`.
3. Validate placeholders and syntax locally.
4. Open a pull request with a short summary of updated sections.

This phase is intentionally lightweight so contributors can join immediately.

### Phase 2 (planned): Translation portal

When volume grows, QUILL will add Weblate or Crowdin while keeping gettext catalogs as the source format. The goal is easier review, glossary enforcement, and translator-team coordination without changing runtime architecture.

## Required translator conventions

1. Preserve placeholders exactly (for example `{filename}`, `{count}`).
2. Respect translator comments prefixed with `Translators:`.
3. Translate UI and accessibility announcements, not user-authored document content.
4. Use context-aware strings where supplied (`pgettext`/`npgettext` contexts).

## Release cycle expectations

1. **Development window**: source strings may change.
2. **Beta translation push**: translators update active languages.
3. **String freeze** (before release): only critical wording fixes allowed.
4. **Release candidate checks**: catalog validation, compile checks, pseudo-locale smoke pass.
5. **Credits refresh**: contributor names and language coverage updated.

## Quality gates for maintainers

Maintainers should block release if translation checks fail:

1. POT extraction succeeds and is committed when strings changed.
2. PO syntax validates.
3. MO compilation succeeds.
4. Named placeholders match source strings.
5. Required release languages are not left in fuzzy-only or broken state.

## What gets translated vs not translated

Translate:

- Menus, dialogs, labels, settings, status text
- Accessible names/descriptions and spoken announcements
- Built-in snippet pack names, descriptions, prompts, and categories

Do not auto-translate:

- User-created document text
- User-created snippets
- User-specific content and imports

## Community recognition

QUILL treats translators as product contributors, not post-release afterthoughts.

- Release notes should include localization updates.
- The About and documentation surfaces should credit translation contributors.
- Community review is encouraged for terminology, consistency, and accessibility clarity.

## i18n status in 0.5.0

This section records the honest starting position so translators know what
coverage to expect and maintainers know what work remains.

**What is done:**
- `quill/locale/quill.pot` — extraction template committed and regenerated by
  `babel extract` (see `babel.cfg`).
- `quill/core/i18n.py` — runtime `_()` loader wired; falls through to identity
  when no `.mo` is present, so the app runs without translations.
- Strings in most new 0.5.0 modules are wrapped with `_()`.

**What is not done yet:**
- No language-specific `.po` / `.mo` files are shipped with 0.5.0. The product
  ships English-only with translation infrastructure in place.
- Several 0.5.0 surfaces have unwrapped strings: `github_provider.py` error
  messages, update flow status strings in `main_frame.py`, and assorted
  diagnostic/log strings throughout.
- Legacy modules (predating 0.5.0) are largely unwrapped; a systematic sweep
  is planned for 0.6.0.

**For the first translator:**
Open `quill/locale/quill.pot` and create `quill/locale/<lang>/LC_MESSAGES/quill.po`
following the Phase 1 GitHub pull-request workflow above. The `.pot` covers the
strings that were wrapped as of the 0.5.0 release date.

## Related documentation

- [Announcement: Quill 0.1.2 Beta](announcement.md)
- [Quill User Guide](../userguide.md)
- [QUILL Product Requirements Document](../QUILL-PRD.md)
