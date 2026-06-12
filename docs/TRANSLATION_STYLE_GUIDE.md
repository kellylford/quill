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
