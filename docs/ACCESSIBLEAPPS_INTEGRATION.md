# AccessibleApps Integration Strategy for Quill

## Overview

Quill now integrates multiple libraries from AccessibleApps (MIT-licensed) to accelerate accessibility improvements, enable incremental updates, and provide battle-tested UI components across Windows, macOS, and Linux.

## Components Integrated

### 1. **app_updater** (Incremental Updates)
**Status**: Implemented (production-ready)  
**Files**: 
- `scripts/generate_app_updater_feed.py` — generates JSON feed in autoupdate format
- `quill/ui/update_manager.py` — callback integration with screen-reader announcements
- `pyproject.toml` — autoupdate dependency added to core

**What it enables**:
- Micro-updates: Ship patches as small ZIPs containing only changed files, not full reinstalls.
- Automatic bootstrapper: Platform-specific scripts (`bootstrap.exe`, `bootstrap-mac.sh`, `bootstrap-lin.sh`) apply updates atomically after app exit and restart.
- Accessible UX: Update checks and progress announced via screen reader with explicit user consent.
- Security: Feeds can be cryptographically signed (Ed25519/RSA) and verified client-side.

**Developer notes**:
- Call `UpdateManager.check_for_updates()` from Help menu or startup checks.
- Callbacks route through `prism_bridge.announce()` for screen-reader compatibility.
- CI must produce ZIP update packages in release pipeline (full installer flow unchanged).
- Test bootstrapper atomicity on Windows (NVDA/Narrator) and macOS (VoiceOver).

---

### 2. **smart_list** (Virtual Lists)
**Status**: Optional (integration in progress)  
**Files**: 
- `pyproject.toml` — smart_list added to `[project.optional-dependencies.ui]`
- Prototype: `quill/ui/smartlist_adapter.py` (to be created)

- Virtual scrolling for large outlines/lists (millions of items without memory blowup).
- Accessible DataView on macOS, ListView on Windows/Linux — unified API across platforms.
- Model-based columns via attribute, dict key, or callable — maps naturally to Quill document models.
- Windows IAT hook bypass for UIA enumeration delays on virtual lists >100K items.

**Developer notes**:
- Keep smart_list use confined to `quill/ui` (it imports `wx`).
- Prototype: wrap SmartList/VirtualSmartList in an adapter that matches Quill's existing list interface.
- Test with NVDA/Narrator (Windows) and VoiceOver (macOS) for focus and announcement behavior.
- Intended for outline navigator and large-document list views.

---

### 3.5. **html_to_text** (HTML Paste Cleaning)
**Status**: Fully integrated (production-ready)  
**Files**: 
- `quill/ui/html_paste_cleaner.py` — HTML detection and cleaning logic
- `quill/ui/main_frame.py` — integrated into magic_paste() function
- `tests/unit/ui/test_html_paste_cleaner.py` — 21 comprehensive tests
- `quill/core/settings.py` — `auto_clean_html_paste` setting (currently defaults to `False`)
- `pyproject.toml` — html_to_text added to `[project.optional-dependencies.ui]`

**What it enables**:
- Automatic HTML detection from web browser pastes (blog posts, emails, articles).
- One-click conversion to clean plain text while preserving structure (headings, links, lists).
- Optional auto-clean mode via Settings → Paste (currently opt-in for user safety).
- Fallback regex-based cleaning if html_to_text library is unavailable.
- No silent stripping; user controls every paste action via Magic Paste picker.

**Workflow**:
1. User copies HTML from web browser or email client.
2. User presses Ctrl+Shift+V (Magic Paste).
3. Quill detects HTML and shows picker:
   - "Paste HTML as clean text" (recommended)
   - "Paste HTML as-is" (original raw HTML)
   - "Paste as plain text" (fallback)
4. User chooses; clean version is inserted immediately.

**Developer notes**:
- `analyze_paste(text) → HtmlPasteContext`: Fast heuristic detection (doesn't require html_to_text import to detect).
- `clean_html(html) → str`: Uses html_to_text if available; falls back to regex stripping.
- Heuristic detects HTML tags but avoids false positives (code samples, email footers).
- All 21 tests passing: detection, cleaning, fallback, edge cases, integration scenarios.
- Screen-reader integration: Status bar announces cleanup (e.g., "Pasted cleaned HTML (350 chars)").

---

### 4. **accessible_output2** (Braille + Speech Fallback)
**Status**: Optional (recommended for later)  
**Files**: None yet — planned as fallback in `quill/platform/windows/prism_bridge.py`

**What it enables**:
- Braille output when Prism backend doesn't support it.
- Fallback speech when Prism runtime is unavailable (graceful degradation).
- Mature support for NVDA, JAWS, Narrator via multiple speech backends.

**Developer notes**:
- Do NOT add as a hard dependency; keep Prism as the primary backend.
- Create an optional adapter `quill/platform/windows/accessible_output_adapter.py` that:
  - Detects accessible_output2 availability at import time.
  - Exposes `speak(message, interrupt)` matching Prism's interface.
  - Falls back to `accessible_output2` if Prism probe fails or braille is needed.
- This is a future enhancement after Prism stabilizes and user demand for braille surfaces.

---

### 4. **app_elements** (Common Dialogs)
**Status**: Candidate for selective adoption  
**Files**: None yet — audit and wrap per-component

**What it enables**:
- Pre-built about boxes, standard dialogs, and reusable UI elements.
- Reduces boilerplate for non-editor UI.

**Developer notes**:
- Do NOT wholesale-import; audit each component for Quill's dialog contracts (default buttons, focus return, accessible names).
- Create wrappers in `quill/ui/app_elements_compat.py` that enforce Quill dialog rules.
- Use selectively for About dialog, license viewer, and settings panels.

---

### 5. **platform_utils** (Clipboard, Paths, Stdout)
**Status**: Candidate for later  
**Files**: None yet

**What it enables**:
- Cross-platform clipboard, path normalization, stdout capture — small utilities to reduce boilerplate.

**Developer notes**:
- Low-risk adoption for small utilities.
- Can be integrated incrementally if Quill's platform layer needs it.

---

## Update Process: How It Works

### 1. **Release Pipeline**
```
quill/version.py → scripts/generate_app_updater_feed.py
                  ↓
                  Produces: docs/site/updates/.quill-app-updater-v1.json
                  Format: { "current_version", "description", "downloads": { "Windows": "...", "Darwin": "...", "Linux": "..." } }
```

### 2. **User Workflow (Automatic or Manual)**
```
User: Help → Check for Updates
       ↓
quill/ui/update_manager.py: UpdateManager.check_for_updates()
       ↓
autoupdate library:
  - Downloads update ZIP to staging directory
  - Announces progress via quill.platform.windows.prism_bridge.announce()
  - Calls update_complete_callback() when ready
       ↓
Platform bootstrapper (after app exit):
  - Waits for Quill process to exit
  - Replaces old files with new files from ZIP
  - Restarts Quill
```

### 3. **Micro-Update Example**
```
Release 1.0.0: Full installer (30 MB)
Release 1.0.1: Micro-update ZIP (2 MB)
  - One file changed (bug fix in core)
  - User downloads 2 MB instead of 30 MB
  - Update applied atomically on next startup
```

---

## Attribution & Licensing

All AccessibleApps libraries are **MIT-licensed**. Attribution is documented in:
- `CONTRIBUTING.md` — "Acknowledgments and Attribution" section
- Individual module docstrings (e.g., `quill/ui/update_manager.py`)
- Release notes (when a library is integrated into a shipped version)

---

## Next Steps

### Immediate (v1.0)
1. ✅ Integrate `app_updater` feed generator and update callbacks.
2. ✅ Document update process in user guide and PRD.
3. ✅ Add AccessibleApps attribution to CONTRIBUTING.md.
4. ✅ Fully integrate `html_to_text` with Magic Paste HTML detection and cleaning (21 tests passing).
5. Test app_updater flow locally on Windows (bootstrapper atomicity).
6. Set up CI to produce ZIP update packages alongside full installers.

### Short-term (v1.1 – v1.5)
1. Wire html_to_text auto-clean setting into UI (Settings → Paste → Auto-clean HTML).
2. Prototype and integrate `smart_list` for outlines and large lists.
3. Test `smart_list` on macOS (DataView) and Windows (ListView) with screen readers.
4. Consider selective `app_elements` adoption for dialogs.
5. Evaluate `accessible_output2` braille support if user demand arises.

### Future
- Optional: Add `platform_utils` for clipboard and cross-platform utilities.
- Optional: Integrate `html_to_text` for import/export workflows.
- Optional: Evaluate `opml_lib` if Quill adds outline import/export.

---

## Testing Checklist

Before shipping any AccessibleApps-integrated feature:

- [ ] Source license and README verified (MIT, no unforeseen restrictions).
- [ ] Dependency audit (no heavy transitive deps added).
- [ ] Platform testing: Windows (NVDA, Narrator), macOS (VoiceOver), Linux (Orca).
- [ ] Accessibility: No double-talk; focus management correct; braille (if applicable).
- [ ] Threading: UI updates via `wx.CallAfter` (if applicable); no blocking on main thread.
- [ ] Packaging: New dependencies added to `pyproject.toml` with version pins and platform guards.
- [ ] Docs: User guide updated; CONTRIBUTING.md updated; module docstrings reference upstream.

---

## Contact & Contributions

Questions about AccessibleApps libraries? Open an issue or discussion in this repo. Pull requests that improve integration, fix bugs, or add tests are welcome.

Links:
- AccessibleApps: https://github.com/accessibleapps/
- app_updater: https://github.com/accessibleapps/app_updater (MIT)
- smart_list: https://github.com/accessibleapps/smart_list (MIT)
- accessible_output2: https://github.com/accessibleapps/accessible_output2 (MIT)
