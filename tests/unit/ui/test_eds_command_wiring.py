"""Source-contract tests for EdSharp (EDS-1..21) UI wiring in main_frame.py.

These assert that every EdSharp command is registered (palette + Keymap Editor)
and recirculated into its conventional menu, and that the read-only guard and
key/indent event hooks are wired. Live wx construction is impractical for the full
menu tree in CI, so we verify the wiring via the source text and the declarative
manifest — the same strategy used by the A11Y-4 dialog-contract guard and the
menu-contract test.

Phase 5 (menus-as-data): the command table and the menu recirculation are both
derived from the wx-free :data:`quill.ui.main_frame_edsharp_menu.EDSHARP_COMMANDS`
manifest, so these tests read the data directly rather than parsing a literal
table body.
"""

from __future__ import annotations

from pathlib import Path

import quill.ui.main_frame as main_frame_module
import quill.ui.main_frame_edsharp_menu as eds_menu_module
import quill.ui.main_frame_menu as main_frame_menu_module
from quill.ui.main_frame_edsharp_menu import EDSHARP_COMMANDS, EDSHARP_REGISTRAR

_SOURCE = (
    Path(main_frame_module.__file__).read_text(encoding="utf-8")
    + "\n"
    + Path(main_frame_menu_module.__file__).read_text(encoding="utf-8")
)
_MENU_SOURCE = Path(eds_menu_module.__file__).read_text(encoding="utf-8")

# Every EdSharp command id that must be both registered and menu-wired.
_EDS_COMMAND_IDS = [
    "eds.insert_special_character",
    "eds.insert_date_time",
    "eds.calculate_and_insert_date",
    "eds.insert_file_content",
    "eds.new_document_from_clipboard",
    "eds.paste_html_as_markdown",
    "eds.number_lines",
    "eds.hard_wrap_lines",
    "eds.delete_to_line_start",
    "eds.delete_to_line_end",
    "eds.delete_to_document_start",
    "eds.delete_to_document_end",
    "eds.delete_paragraph",
    "eds.set_lines_first_not_second",
    "eds.set_lines_common",
    "eds.count_regex_matches",
    "eds.extract_regex_matches",
    "eds.speak_cursor_address",
    "eds.speak_document_status",
    "eds.speak_selection_length",
    "eds.go_to_percent",
    "eds.move_to_first_non_blank",
    "eds.move_to_last_non_blank",
    "eds.toggle_read_only_guard",
    "eds.toggle_clipboard_collector",
    "eds.collect_clipboard_now",
    "eds.toggle_key_describer",
    "eds.toggle_indent_announce",
    "eds.infer_indent",
    "eds.run_current_file",
    "eds.run_target_at_cursor",
    "eds.rename_current_file",
    "eds.delete_current_file",
]


def test_command_table_lists_every_eds_command() -> None:
    manifest_ids = {command.id for command in EDSHARP_COMMANDS}
    for command_id in _EDS_COMMAND_IDS:
        assert command_id in manifest_ids, f"{command_id} missing from EDSHARP_COMMANDS manifest"


def test_commands_are_registered_and_keymap_assignable() -> None:
    assert "self._register_edsharp_commands()" in _SOURCE
    assert "EdSharpMenuMixin" in _SOURCE.split("class MainFrame(")[1].split(")")[0]
    register = _MENU_SOURCE[_MENU_SOURCE.index("def _register_edsharp_commands") :][:400]
    # Registration goes through the standard command registry (palette + Keymap
    # Editor) and reads any user binding rather than shipping a default.
    assert "self.commands.register(" in register
    assert "self._binding_for(command_id)" in register


def test_every_command_is_menu_wired() -> None:
    # menus.md Phase 4 + 5: the EdSharp monolith is dissolved and the menu
    # recirculation is data-driven. Each command carries a menu placement (group)
    # in the declarative manifest, and the generic group helper appends it.
    valid_groups = {
        "insert",
        "edit",
        "file_create",
        "file_ops",
        "transform_lines",
        "navigate",
        "search",
        "accessibility",
        "power_tools",
    }
    for command in EDSHARP_COMMANDS:
        assert command.placement.group in valid_groups, (
            f"{command.id} has unknown menu group {command.placement.group!r}"
        )
        assert command.placement.label, f"{command.id} has no menu label"
    # Every group is actually wired to a menu (the helpers / Power Tools submenu
    # delegate to the single data-driven primitive).
    assert "self._append_edsharp_group(" in _MENU_SOURCE
    # The cohesive remainder ships as Tools > Power Tools (the foreign "EdSharp"
    # brand name is gone); the recirculated groups are appended to conventional
    # menus from the menu build.
    assert 'AppendSubMenu(self._build_power_tools_menu(), "&Power Tools")' in _SOURCE
    for helper in (
        "_append_edsharp_insert_items",
        "_append_edsharp_edit_items",
        "_append_edsharp_file_create_items",
        "_append_edsharp_file_ops_items",
        "_append_edsharp_transform_line_items",
        "_append_edsharp_navigate_items",
        "_append_edsharp_search_items",
        "_append_edsharp_accessibility_items",
    ):
        assert f"self.{helper}(" in _SOURCE, f"{helper} is not called from the menu build"


def test_menu_items_are_bound() -> None:
    # The shared _eds_menu_item helper appends and binds every entry in one step.
    assert "self.frame.Bind(wx.EVT_MENU, lambda _e, run=handler: run(), id=item_id)" in _MENU_SOURCE


def test_read_only_guard_protects_edit_helpers() -> None:
    guard = (
        "if self._document_is_read_only():\n"
        '            self._set_status("Document is read-only")\n'
        "            return"
    )
    assert _SOURCE.count(guard) >= 3, "read-only guard missing from one of the _apply_* helpers"


def test_event_hooks_are_wired() -> None:
    char_hook = _SOURCE[_SOURCE.index("def _on_editor_char_hook") :][:200]
    assert "if self._maybe_describe_key(event):" in char_hook
    caret = _SOURCE[_SOURCE.index("def _on_editor_caret_activity") :][:200]
    assert "self._maybe_announce_indent()" in caret


def test_read_only_state_refreshes_on_tab_switch() -> None:
    activate = _SOURCE[_SOURCE.index("def _activate_tab") :][:1200]
    assert "self._refresh_read_only_state()" in activate


def test_read_only_state_refreshes_on_open() -> None:
    # Newly opened/selected tabs must re-apply a persisted read-only guard.
    create_tab = _SOURCE[_SOURCE.index("def _create_document_tab") :][:1400]
    assert "self._refresh_read_only_state()" in create_tab


def test_command_table_is_exactly_the_expected_ids_with_no_duplicates() -> None:
    ids = [command.id for command in EDSHARP_COMMANDS]
    assert len(ids) == len(_EDS_COMMAND_IDS)
    assert len(set(ids)) == len(ids), "duplicate command id in manifest"
    assert set(ids) == set(_EDS_COMMAND_IDS)


def test_every_table_handler_exists_on_the_actions_mixin() -> None:
    from quill.ui.main_frame_edsharp import EdSharpActionsMixin
    from quill.ui.main_frame_edsharp_menu import _MIGRATED_HANDLERS

    for command in EDSHARP_COMMANDS:
        if command.id in _MIGRATED_HANDLERS:
            # Migrated onto the contribution grammar: handler lives in a feature
            # module and runs through the Host facade, not on the mixin.
            assert callable(_MIGRATED_HANDLERS[command.id])
            continue
        name = command.handler_name
        assert hasattr(EdSharpActionsMixin, name), (
            f"missing handler {name} on EdSharpActionsMixin for {command.id}"
        )


def test_line_transforms_are_migrated_off_the_mixin() -> None:
    # Wave 2 / §9: number_lines + hard_wrap_lines no longer live on the mixin;
    # they are resolved from the line_transforms feature module instead.
    from quill.ui.main_frame_edsharp import EdSharpActionsMixin
    from quill.ui.main_frame_edsharp_menu import _MIGRATED_HANDLERS

    assert set(_MIGRATED_HANDLERS) >= {"eds.number_lines", "eds.hard_wrap_lines"}
    assert not hasattr(EdSharpActionsMixin, "number_lines")
    assert not hasattr(EdSharpActionsMixin, "hard_wrap_lines")


def test_menu_recirculation_preserves_shipped_group_order() -> None:
    # The data-driven group helper appends commands in declaration order; verify
    # each conventional menu's EdSharp group is in the exact shipped sequence.
    expected = {
        "insert": [
            "eds.insert_special_character",
            "eds.insert_date_time",
            "eds.calculate_and_insert_date",
            "eds.insert_file_content",
        ],
        "edit": [
            "eds.paste_html_as_markdown",
            "eds.delete_to_line_start",
            "eds.delete_to_line_end",
            "eds.delete_to_document_start",
            "eds.delete_to_document_end",
            "eds.delete_paragraph",
        ],
        "search": [
            "eds.count_regex_matches",
            "eds.extract_regex_matches",
            "eds.set_lines_first_not_second",
            "eds.set_lines_common",
        ],
        "power_tools": [
            "eds.toggle_read_only_guard",
            "eds.toggle_clipboard_collector",
            "eds.collect_clipboard_now",
            "eds.toggle_key_describer",
            "eds.toggle_indent_announce",
            "eds.infer_indent",
        ],
    }
    for group, ids in expected.items():
        actual = [c.id for c in EDSHARP_REGISTRAR.commands_in_group(group)]
        assert actual == ids, f"group {group} order drifted: {actual}"
