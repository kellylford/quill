# Announcing Quill Beta

## A screen-reader-first writing environment for Windows

Quill Beta is here.

Quill is a writing, reading, review, and document-intelligence environment for Windows built around a simple idea: powerful tools should feel calm, predictable, and welcoming from the keyboard. The editor is local-first, screen-reader-first, and designed to make serious text work feel steady instead of fragile.

Quill is not only a place to type notes. It is a place to open and write plain text, Markdown, and HTML; inspect structure; compare revisions; navigate EPUB content; review extraction quality; run accessibility checks; work with spelling and thesaurus tools; use golden keyboard packs; and move through real documents with confidence.

It is also a place to grow. Quill now includes guided onboarding for optional external tools, so users can see exactly what helpers such as Pandoc, Tesseract OCR, LibreOffice, and Ghostscript would unlock before they install anything. When Pandoc is present, Quill can open a native conversion wizard and turn supported source files into Markdown, HTML, or plain text surfaces ready for reading, editing, or GLOW-oriented downstream workflows.

## What makes Quill special

Quill Beta already includes a broad set of everyday and specialist features:

- a keyboard-first editor shell with command palette, tabs, rich navigation, and an interactive status bar
- plain text, Markdown, and HTML workflows that stay readable and structured
- spell check, thesaurus, word count, link insertion, and source-aware copy
- heading, list, table, code block, and markup insertion tools
- compare workflows for file-to-file and document-to-document review
- EPUB navigation, OCR image intake, and extraction-quality review
- feature profiles that keep the interface calm without taking power away
- golden keyboard packs inspired by Windows Notepad, Notepad++, VS Code, Microsoft Word, and Quill-native workflows
- the first native GLOW workflows for deterministic audit and fix work inside the editor itself
- external tool onboarding with wizard-like guidance for Pandoc and other optional format helpers
- accessibility-focused support such as region cycling, keyboard-trap inspection, contrast validation, and discoverable help surfaces
- backups, autosave, recovery, persistent undo, trusted locations, notifications, diagnostics export, and signed update checks

## The new GLOW experience inside Quill

One of the most exciting additions in this beta is the first native GLOW workflow inside Quill.

GLOW stands for guided layout and output workflow. In Quill Beta, GLOW makes accessibility-aware review feel like part of writing rather than a separate compliance chore. You can audit the current document, audit the current selection, fix the current document into a preview tab, compare original and fixed output, or apply deterministic fixes directly to the current selection.

This first slice focuses on plain text, Markdown, and HTML. It already helps with heading spacing, heading-level jumps, generic link text, missing HTML language metadata, missing image alt attributes, dense paragraphs, and plain-language friction.

Quill also now has the start of a broader format-bridge story. With Pandoc available, users can bring in supported text-centric source formats through a guided wizard instead of a command line, then continue the work inside Quill with structure-aware editing, compare, spell, and GLOW flows. That matters because accessible document work often begins in an awkward format and only becomes productive after it is translated into a surface that is stable, readable, and reviewable.

That same spirit applies to the learning surface. Quill now has a cleaner documentation ladder: the welcome guide for a first orientation, the keyboard reference for exact current bindings, the full user guide for day-to-day depth, the beta announcement for the big-picture feature story, and the beta feedback plan for support expectations. The goal is not to bury users in docs. The goal is to make sure there is always one clear next document when a user asks, "What do I do now?"

## Why this beta matters

Quill is being built for people who need an editor that feels trustworthy.

That includes:

- screen-reader users who want a native Windows experience
- writers and editors who work heavily in plain text, Markdown, or HTML
- accessibility-minded teams reviewing structure and readability
- people opening difficult or imperfect source documents and trying to decide whether the extracted text is good enough to trust
- people who need one Windows editor that can stay simple for daily writing while expanding into optional conversion and ingestion workflows when needed
- users who want a serious editor that still teaches them what it can do

This beta is not just a preview. It is the moment when Quill starts learning from real work.

## This is a beta

Quill Beta is already useful, but it is still a beta.

That means:

- bugs may be found
- some features are deeper than others
- some workflows are still maturing toward the full v1.1 vision
- parts of the support and feedback experience still need polishing before the broadest public rollout

If something feels rough, that feedback is valuable. If something delights you, that is valuable too. Both help shape what Quill becomes next.

## Feedback and bug reports

We want the beta feedback path to be inclusive and low-friction.

GitHub issues are useful for testers who already use GitHub, but they should not be the only way people can report problems. Before the broadest public beta push, Quill should have a secure no-login feedback route with optional diagnostics upload.

In the meantime, Quill is moving toward a more humane support story: diagnostics can be packaged locally, support information can be reviewed before it leaves the machine, and the broader Community Access support-hub model can give the project a better route than forcing every tester into a raw GitHub issue workflow.

Even before the final support route lands, Quill now ships a stronger intermediate experience: local diagnostics packaging, a support-oriented bug-report launch point, and clearer documentation about what each feedback path is for.

Until that path is fully published, treat GitHub as the optional technical route rather than the only official route.

## Thank you for trying Quill

Trying a beta takes generosity. You are trusting unfinished software with real work, real attention, and real patience.

Thank you for that.

If Quill helps you write more confidently, review more carefully, or simply feel more at home in a Windows editor, then the beta is already doing something important. And if you help point out what still needs work, you are helping build the version that will be even stronger.

Quill Beta is ready to be explored. Open a file, press `Ctrl+Shift+P`, and start.
