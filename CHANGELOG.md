# Changelog

## Quill 0.1 Beta

Quill 0.1 Beta is the first broad, coherent release of Quill as a screen-reader-first writing, reading, review, and document-intelligence environment for Windows from Blind Information Technology Solutions (BITS) and Community Access.

### Highlights

- Native wxPython editor shell with command palette, tabs, menus, and interactive status bar
- Plain text, Markdown, HTML, EPUB, PDF, DOCX, ODT, RTF, JSON, XML, TOML, CSV, TSV, notebook, and SQLite reading surfaces
- Deterministic GLOW audit and fix workflows inside Quill for plain text, Markdown, and HTML
- Guided optional-tool onboarding for Pandoc, Tesseract OCR, LibreOffice, Ghostscript, HTML Tidy, XML Lint, and PyMarkdown
- Pandoc Conversion Wizard for opening supported source files as Markdown, HTML, or plain text tabs
- In-app diagnostics review before export and in-app bug-report review before launching the Community Access support form
- Autosave, backups, recovery, persistent undo, trusted locations, notifications, and signed update checks
- Windows packaging flow with embedded Python, portable bundle generation, and Inno Setup installer compilation

### What feels new in this release

The Help menu now acts like a real support surface instead of a dead end. Users can review diagnostics before Quill writes a zip, review a bug report before Quill opens the browser, and route support feedback into the shared Community Access support flow with more confidence and less guesswork.

Quill also now has a more practical format-bridge story. With Pandoc available, documents can move into stable text-centric workflows without pushing users into command-line tooling. The external-tools dialog explains what each helper unlocks and keeps the setup story transparent.

### Packaging and release quality

- Embedded Python runtime verification with pinned SHA-256 validation
- Runtime dependency bundling derived from project metadata for UI and spell-check support
- Compiled Windows installer output: `Quill-Setup-0.1.exe`
- Release provenance and SBOM generation support via `scripts/generate_release_artifacts.py`

### Support and feedback

Quill 0.1 Beta uses the Help menu as its primary guided feedback route. `Help -> Save Diagnostics...` prepares a reviewable bundle, and `Help -> Report a Bug...` prepares the report in-app before opening the Community Access support form for user review and submission.

### Notes

This is a beta release. The product direction is aligned with the Quill 1.0 PRD, while some workflows are still evolving toward that fuller 1.0 target.