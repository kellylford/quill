from __future__ import annotations

from collections import defaultdict

from quill.core.commands import Command
from quill.core.features import FeatureManager


def build_welcome_guide(feature_manager: FeatureManager | None = None) -> str:
    profile_block = ""
    if feature_manager is not None:
        profile_block = f"## Current profile\n\n{feature_manager.profile_summary()}\n\n"
    return (
        "# Welcome to Quill\n\n"
        "Quill is a keyboard-first writing editor focused on accessibility.\n\n"
        f"{profile_block}"
        "## Quick start\n\n"
        "1. Open a file with `Ctrl+O` or create one with `Ctrl+N`.\n"
        "2. Use `Ctrl+Shift+P` to open the Command Palette.\n"
        "3. Search with `Ctrl+F`, then `F3` / `Shift+F3` to move through matches.\n"
        "4. Use the Navigate menu for line, page, heading, block, and location jumps.\n\n"
        "## Editing highlights\n\n"
        "- Markdown/HTML formatting shortcuts: `Ctrl+B`, `Ctrl+I`, `Ctrl+Alt+1..6`.\n"
        "- Tag helpers: Insert HTML Tag and Insert Markdown Tag from the Format menu.\n"
        "- Find all matches with `Alt+F3`.\n\n"
        "## Learn shortcuts\n\n"
        "Open **Tools -> Keyboard Reference** to generate the latest keymap reference."
    )


def build_keyboard_reference(
    commands: list[Command], feature_manager: FeatureManager | None = None
) -> str:
    grouped: dict[str, list[Command]] = defaultdict(list)
    if feature_manager is not None:
        commands = feature_manager.visible_commands(commands)
    for command in sorted(commands, key=lambda item: item.id):
        section = command.id.split(".", 1)[0].capitalize()
        grouped[section].append(command)

    lines = ["# Keyboard Reference", "", "Generated from the active command registry.", ""]
    for section in sorted(grouped.keys()):
        lines.append(f"## {section}")
        lines.append("")
        for command in grouped[section]:
            binding = command.keybinding or "(unbound)"
            lines.append(f"- `{binding}` — **{command.title}** (`{command.id}`)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
