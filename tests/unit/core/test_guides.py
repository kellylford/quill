from quill.core.commands import Command
from quill.core.guides import build_keyboard_reference, build_welcome_guide


def test_build_welcome_guide_contains_core_sections() -> None:
    guide = build_welcome_guide()
    assert "# Welcome to Quill" in guide
    assert "## Quick start" in guide
    assert "Keyboard Reference" in guide


def test_build_keyboard_reference_groups_commands() -> None:
    commands = [
        Command("file.open", "Open File", "Ctrl+O", lambda: None, "core.file"),
        Command("edit.find", "Find", "Ctrl+F", lambda: None, "core.search"),
        Command("tools.word_count", "Word Count", None, lambda: None, "core.analysis"),
    ]
    reference = build_keyboard_reference(commands)
    assert "## Edit" in reference
    assert "## File" in reference
    assert "## Tools" in reference
    assert "`Ctrl+O`" in reference
    assert "`(unbound)`" in reference
