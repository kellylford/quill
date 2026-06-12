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
