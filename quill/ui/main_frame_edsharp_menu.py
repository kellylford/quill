"""EdSharp command registration and menu wiring for :class:`MainFrame`.

Extracted from ``main_frame.py`` to keep the monolith under its GATE-11 budget.
This mixin owns the single source of truth for the EdSharp (EDS-1..21) commands,
registers them with the palette/Keymap Editor, and recirculates them into their
conventional menus (menus.md Phase 4): the former ``Tools > EdSharp Tools``
monolith is dissolved so its commands live where users expect them (Insert, Edit,
File, Format, Navigate, Search, Tools > Accessibility) and the cohesive remainder
ships as ``Tools > Power Tools``.

Phase 5 (menus-as-data) turns that source of truth into a **declarative manifest**:
:data:`EDSHARP_COMMANDS` expresses every command in the shared contribution
grammar (:mod:`quill.core.contributions`) — id, title, top-level home, in-menu
label, and grouping — and both the palette registration table and the menu
recirculation are *derived* from it. The handlers still live on
:class:`~quill.ui.main_frame_edsharp.EdSharpActionsMixin` and resolve by
convention (``eds.number_lines`` -> ``self.number_lines``), so the data and the
behavior can never drift.
"""

from __future__ import annotations

from collections.abc import Callable

from quill.core.contributions import FirstPartyCommand, FirstPartyRegistrar
from quill.ui.features import line_transforms

# Command ids whose handler has been migrated off the EdSharp mixin onto the
# contribution grammar (migration plan Wave 2). For these, the registration table
# resolves the id to ``lambda: handler(host)`` against the live first-party Host
# facade instead of a ``self.<method>`` mixin attribute; everything else still
# resolves by convention. As more groups migrate, they register here.
_MIGRATED_HANDLERS: dict[str, Callable[[object], None]] = dict(line_transforms.HANDLERS)


def _build_edsharp_registrar() -> FirstPartyRegistrar:
    """Declare the EdSharp parity commands (EDS-1..21) as first-party data.

    Commands are declared grouped by their recirculated menu home (menus.md
    Phase 4). Within each ``group`` the declaration order is the live menu order,
    and ``separator_before`` reproduces the visual grouping; one data-driven
    helper appends each group. None carry a default keybinding — EdSharp's own
    shortcuts collide with QUILL's curated keymap, so users bind them from the
    Keymap Editor instead.
    """

    registrar = FirstPartyRegistrar()
    add = registrar.add_command

    # Insert menu --------------------------------------------------------
    add(
        id="eds.insert_special_character",
        title="EdSharp: Insert Special Character",
        top_level="Insert",
        group="insert",
        label="Special &Character...",
        separator_before=True,
    )
    add(
        id="eds.insert_date_time",
        title="EdSharp: Insert Date and Time",
        top_level="Insert",
        group="insert",
        label="Date and &Time",
    )
    add(
        id="eds.calculate_and_insert_date",
        title="EdSharp: Insert Calculated Date",
        top_level="Insert",
        group="insert",
        label="C&alculated Date...",
    )
    add(
        id="eds.insert_file_content",
        title="EdSharp: Insert File Content",
        top_level="Insert",
        group="insert",
        label="File &Content...",
    )

    # Edit menu ----------------------------------------------------------
    add(
        id="eds.paste_html_as_markdown",
        title="EdSharp: Paste HTML as Markdown",
        top_level="Edit",
        group="edit",
        label="Paste &HTML as Markdown",
        separator_before=True,
    )
    add(
        id="eds.delete_to_line_start",
        title="EdSharp: Delete to Line Start",
        top_level="Edit",
        group="edit",
        label="Delete to Line &Start",
        separator_before=True,
    )
    add(
        id="eds.delete_to_line_end",
        title="EdSharp: Delete to Line End",
        top_level="Edit",
        group="edit",
        label="Delete to Line E&nd",
    )
    add(
        id="eds.delete_to_document_start",
        title="EdSharp: Delete to Document Start",
        top_level="Edit",
        group="edit",
        label="Delete to Document &Top",
    )
    add(
        id="eds.delete_to_document_end",
        title="EdSharp: Delete to Document End",
        top_level="Edit",
        group="edit",
        label="Delete to Document Botto&m",
    )
    add(
        id="eds.delete_paragraph",
        title="EdSharp: Delete Paragraph",
        top_level="Edit",
        group="edit",
        label="Delete Paragrap&h",
    )

    # File menu ----------------------------------------------------------
    add(
        id="eds.new_document_from_clipboard",
        title="EdSharp: New Document from Clipboard",
        top_level="File",
        group="file_create",
        label="New from Cli&pboard",
    )
    add(
        id="eds.run_current_file",
        title="EdSharp: Run Current File",
        top_level="File",
        group="file_ops",
        label="R&un Current File",
    )
    add(
        id="eds.run_target_at_cursor",
        title="EdSharp: Open Target at Cursor",
        top_level="File",
        group="file_ops",
        label="Open &Target at Cursor",
    )
    add(
        id="eds.rename_current_file",
        title="EdSharp: Rename Current File",
        top_level="File",
        group="file_ops",
        label="Re&name Current File...",
    )
    add(
        id="eds.delete_current_file",
        title="EdSharp: Delete Current File",
        top_level="File",
        group="file_ops",
        label="Dele&te Current File...",
    )

    # Format > Transform Lines ------------------------------------------
    add(
        id="eds.number_lines",
        title="EdSharp: Number Lines",
        top_level="Format",
        group="transform_lines",
        label="&Number Lines...",
    )
    add(
        id="eds.hard_wrap_lines",
        title="EdSharp: Hard-Wrap Lines",
        top_level="Format",
        group="transform_lines",
        label="&Hard-Wrap Lines...",
    )

    # Navigate menu ------------------------------------------------------
    add(
        id="eds.go_to_percent",
        title="EdSharp: Go to Percent",
        top_level="Navigate",
        group="navigate",
        label="Go to &Percent...",
        separator_before=True,
    )
    add(
        id="eds.move_to_first_non_blank",
        title="EdSharp: Move to First Non-Blank",
        top_level="Navigate",
        group="navigate",
        label="First &Non-Blank",
    )
    add(
        id="eds.move_to_last_non_blank",
        title="EdSharp: Move to Last Non-Blank",
        top_level="Navigate",
        group="navigate",
        label="&Last Non-Blank",
    )

    # Search menu --------------------------------------------------------
    add(
        id="eds.count_regex_matches",
        title="EdSharp: Count Regex Matches",
        top_level="Search",
        group="search",
        label="&Count Regex Matches...",
        separator_before=True,
    )
    add(
        id="eds.extract_regex_matches",
        title="EdSharp: Extract Regex Matches",
        top_level="Search",
        group="search",
        label="E&xtract Regex Matches...",
    )
    add(
        id="eds.set_lines_first_not_second",
        title="EdSharp: Lines in First Block Only",
        top_level="Search",
        group="search",
        label="Lines in First &Block Only",
        separator_before=True,
    )
    add(
        id="eds.set_lines_common",
        title="EdSharp: Lines Common to Both Blocks",
        top_level="Search",
        group="search",
        label="Lines Co&mmon to Both Blocks",
    )

    # Tools > Accessibility ---------------------------------------------
    add(
        id="eds.speak_cursor_address",
        title="EdSharp: Speak Cursor Address",
        top_level="Tools",
        group="accessibility",
        label="Speak Cursor &Address",
        separator_before=True,
    )
    add(
        id="eds.speak_document_status",
        title="EdSharp: Speak Document Status",
        top_level="Tools",
        group="accessibility",
        label="Speak Document Stat&us",
    )
    add(
        id="eds.speak_selection_length",
        title="EdSharp: Speak Selection Length",
        top_level="Tools",
        group="accessibility",
        label="Speak Selection &Length",
    )

    # Tools > Power Tools (the cohesive EdSharp remainder) --------------
    add(
        id="eds.toggle_read_only_guard",
        title="EdSharp: Toggle Read-Only Guard",
        top_level="Tools",
        group="power_tools",
        label="Toggle &Read-Only Guard",
    )
    add(
        id="eds.toggle_clipboard_collector",
        title="EdSharp: Toggle Clipboard Collector",
        top_level="Tools",
        group="power_tools",
        label="Toggle Clipboard Co&llector",
    )
    add(
        id="eds.collect_clipboard_now",
        title="EdSharp: Collect Clipboard Now",
        top_level="Tools",
        group="power_tools",
        label="Collect Clipboard No&w",
    )
    add(
        id="eds.toggle_key_describer",
        title="EdSharp: Toggle Key Describer",
        top_level="Tools",
        group="power_tools",
        label="Toggle &Key Describer",
    )
    add(
        id="eds.toggle_indent_announce",
        title="EdSharp: Toggle Indentation Announcements",
        top_level="Tools",
        group="power_tools",
        label="Toggle Indentation &Announcements",
    )
    add(
        id="eds.infer_indent",
        title="EdSharp: Infer Indentation",
        top_level="Tools",
        group="power_tools",
        label="I&nfer Indentation...",
    )
    return registrar


# The declarative EdSharp manifest. Both the palette registration table and the
# menu recirculation derive from this single data structure (menus.md Phase 5).
EDSHARP_REGISTRAR: FirstPartyRegistrar = _build_edsharp_registrar()
EDSHARP_COMMANDS: tuple[FirstPartyCommand, ...] = EDSHARP_REGISTRAR.commands


class EdSharpMenuMixin:
    """Palette + menu wiring for the EdSharp parity commands."""

    def _contribution_host(self) -> object:
        """Return the cached live first-party :class:`Host` adapter.

        Lazily built so it is available wherever the EdSharp table resolves a
        migrated handler. The adapter reads ``self.editor`` dynamically, so a
        single instance stays correct across tab switches.
        """
        host = getattr(self, "_first_party_host_obj", None)
        if host is None:
            from quill.ui.contribution_host import MainFrameHost

            host = MainFrameHost(self)
            self._first_party_host_obj = host
        return host

    def _resolve_edsharp_handler(self, command_id: str) -> Callable[[], None]:
        """Resolve a command id to its zero-arg handler.

        Migrated ids (``_MIGRATED_HANDLERS``) bind to a feature-module handler
        invoked with the live ``Host`` facade; all others resolve by convention
        to the matching ``EdSharpActionsMixin`` method (``eds.number_lines`` ->
        ``self.number_lines``).
        """
        migrated = _MIGRATED_HANDLERS.get(command_id)
        if migrated is not None:
            host = self._contribution_host()
            return lambda: migrated(host)
        _, _, method = command_id.partition(".")
        return getattr(self, method or command_id)

    def _edsharp_command_table(self) -> list[tuple[str, str, Callable[[], None]]]:
        """EdSharp parity commands as ``(id, label, handler)`` rows.

        Derived from the declarative :data:`EDSHARP_COMMANDS` manifest; each
        handler is resolved via :meth:`_resolve_edsharp_handler` (migrated feature
        module or mixin method by convention) so the data and behavior stay in
        lock-step. Shared by command registration (palette + Keymap Editor) and
        the menu recirculation so the two never drift.
        """
        return [
            (command.id, command.title, self._resolve_edsharp_handler(command.id))
            for command in EDSHARP_COMMANDS
        ]

    def _register_edsharp_commands(self) -> None:
        for command_id, label, handler in self._edsharp_command_table():
            self.commands.register(command_id, label, handler, self._binding_for(command_id))

    def _edsharp_handlers(self) -> dict[str, Callable[[], None]]:
        return {
            command_id: handler for command_id, _label, handler in self._edsharp_command_table()
        }

    def _eds_menu_item(self, menu: object, command_id: str, label: str) -> None:
        """Append one EdSharp command to ``menu`` and bind its handler.

        Shared by the data-driven group helper and the Power Tools submenu so the
        menu surface and the command palette stay in lock-step. The label shows
        any user-assigned keybinding via ``_menu_label``.
        """
        wx = self._wx
        item_id = wx.NewIdRef()
        menu.Append(item_id, self._menu_label(label, command_id))
        handler = self._edsharp_handlers()[command_id]
        self.frame.Bind(wx.EVT_MENU, lambda _e, run=handler: run(), id=item_id)

    def _append_edsharp_group(self, menu: object, group: str) -> None:
        """Append every command in ``group`` to ``menu`` in declaration order.

        The single data-driven recirculation primitive (menus.md Phase 5): it
        reads :data:`EDSHARP_COMMANDS`, emits each command's separator and label
        from the manifest, and binds it — replacing the eight hand-written
        per-group helpers with one loop over the declarative data.
        """
        for command in EDSHARP_REGISTRAR.commands_in_group(group):
            if command.placement.separator_before:
                menu.AppendSeparator()
            self._eds_menu_item(menu, command.id, command.placement.label)

    # --- Recirculation helpers (menus.md Phase 4) --------------------------
    # Thin, data-driven wrappers kept as named seams for the menu builder. Each
    # delegates to _append_edsharp_group so the placement lives in the manifest.

    def _append_edsharp_insert_items(self, insert_menu: object) -> None:
        self._append_edsharp_group(insert_menu, "insert")

    def _append_edsharp_edit_items(self, edit_menu: object) -> None:
        self._append_edsharp_group(edit_menu, "edit")

    def _append_edsharp_file_create_items(self, file_menu: object) -> None:
        self._append_edsharp_group(file_menu, "file_create")

    def _append_edsharp_file_ops_items(self, file_menu: object) -> None:
        self._append_edsharp_group(file_menu, "file_ops")

    def _append_edsharp_transform_line_items(self, transform_menu: object) -> None:
        self._append_edsharp_group(transform_menu, "transform_lines")

    def _append_edsharp_navigate_items(self, navigate_menu: object) -> None:
        self._append_edsharp_group(navigate_menu, "navigate")

    def _append_edsharp_search_items(self, search_menu: object) -> None:
        self._append_edsharp_group(search_menu, "search")

    def _append_edsharp_accessibility_items(self, accessibility_menu: object) -> None:
        self._append_edsharp_group(accessibility_menu, "accessibility")

    def _build_power_tools_menu(self) -> object:
        """Build the Tools > Power Tools submenu (the cohesive EdSharp remainder).

        These commands have no conventional menu home — they are editor-power
        utilities (read-only guard, clipboard collector, key describer, indent
        helpers) that belong together rather than scattered. The foreign
        "EdSharp" brand name is dropped (menus.md Phase 4 / §3.7).
        """
        wx = self._wx
        menu = wx.Menu()
        self._append_edsharp_group(menu, "power_tools")
        return menu
