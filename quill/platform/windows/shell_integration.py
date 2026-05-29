from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

try:  # pragma: no cover - Windows-only module
    import winreg
except ImportError:  # pragma: no cover - non-Windows fallback
    winreg = None

APP_DISPLAY_NAME = "Quill"
APPLICATION_NAME = "quill"
APPLICATION_KEY = rf"Software\Classes\Applications\{APPLICATION_NAME}.exe"
PROGID_TEXT = "Quill.Text"
PROGID_MARKUP = "Quill.Markup"
PROGID_HTML = "Quill.HTML"

TEXT_EXTENSIONS = (".txt",)
MARKUP_EXTENSIONS = (".md", ".markdown", ".mdx")
HTML_EXTENSIONS = (".html", ".htm", ".xhtml")


@dataclass(frozen=True, slots=True)
class RegistryValue:
    name: str
    value: object
    kind: int


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    path: str
    values: tuple[RegistryValue, ...]


def launcher_command() -> str:
    executable = Path(sys.executable)
    return f'"{executable}" -m quill "%1"'


def build_shell_integration_plan(command: str | None = None) -> list[RegistryEntry]:
    command = command or launcher_command()
    entries: list[RegistryEntry] = [
        RegistryEntry(
            path=APPLICATION_KEY,
            values=(
                RegistryValue("", APP_DISPLAY_NAME, _reg_kind("sz")),
                RegistryValue("FriendlyAppName", APP_DISPLAY_NAME, _reg_kind("sz")),
                RegistryValue(
                    "FriendlyAppUserModelID",
                    f"GitHub.{APP_DISPLAY_NAME}",
                    _reg_kind("sz"),
                ),
            ),
        ),
        RegistryEntry(
            path=rf"{APPLICATION_KEY}\shell\open\command",
            values=(RegistryValue("", command, _reg_kind("sz")),),
        ),
        RegistryEntry(
            path=rf"{APPLICATION_KEY}\SupportedTypes",
            values=tuple(
                RegistryValue(extension, "", _reg_kind("sz"))
                for extension in TEXT_EXTENSIONS + MARKUP_EXTENSIONS + HTML_EXTENSIONS
            ),
        ),
    ]

    entries.extend(
        _association_entries(
            PROGID_TEXT,
            "Plain Text Document",
            TEXT_EXTENSIONS,
            command,
        )
    )
    entries.extend(
        _association_entries(
            PROGID_MARKUP,
            "Markdown Document",
            MARKUP_EXTENSIONS,
            command,
        )
    )
    entries.extend(
        _association_entries(
            PROGID_HTML,
            "HTML Document",
            HTML_EXTENSIONS,
            command,
        )
    )
    return entries


def install_shell_integration(command: str | None = None) -> None:
    if winreg is None:  # pragma: no cover - non-Windows fallback
        raise RuntimeError("Windows registry access is unavailable")
    for entry in build_shell_integration_plan(command):
        _write_entry(entry)


def remove_shell_integration() -> None:
    if winreg is None:  # pragma: no cover - non-Windows fallback
        raise RuntimeError("Windows registry access is unavailable")
    for path in [
        APPLICATION_KEY,
        rf"{APPLICATION_KEY}\shell\open\command",
        rf"{APPLICATION_KEY}\SupportedTypes",
        rf"Software\Classes\{PROGID_TEXT}",
        rf"Software\Classes\{PROGID_TEXT}\shell\open\command",
        rf"Software\Classes\{PROGID_TEXT}\SupportedTypes",
        rf"Software\Classes\{PROGID_MARKUP}",
        rf"Software\Classes\{PROGID_MARKUP}\shell\open\command",
        rf"Software\Classes\{PROGID_MARKUP}\SupportedTypes",
        rf"Software\Classes\{PROGID_HTML}",
        rf"Software\Classes\{PROGID_HTML}\shell\open\command",
        rf"Software\Classes\{PROGID_HTML}\SupportedTypes",
    ]:
        _delete_tree(winreg.HKEY_CURRENT_USER, path)


def _association_entries(
    progid: str,
    friendly_name: str,
    extensions: tuple[str, ...],
    command: str,
) -> list[RegistryEntry]:
    entries = [
        RegistryEntry(
            path=rf"Software\Classes\{progid}",
            values=(
                RegistryValue("", friendly_name, _reg_kind("sz")),
                RegistryValue("FriendlyTypeName", friendly_name, _reg_kind("sz")),
            ),
        ),
        RegistryEntry(
            path=rf"Software\Classes\{progid}\shell\open\command",
            values=(RegistryValue("", command, _reg_kind("sz")),),
        ),
        RegistryEntry(
            path=rf"Software\Classes\{progid}\SupportedTypes",
            values=tuple(RegistryValue(extension, "", _reg_kind("sz")) for extension in extensions),
        ),
    ]
    for extension in extensions:
        entries.append(
            RegistryEntry(
                path=rf"Software\Classes\{extension}\OpenWithProgids",
                values=(RegistryValue(progid, "", _reg_kind("none")),),
            )
        )
    return entries


def _write_entry(entry: RegistryEntry) -> None:
    key = _create_key(winreg.HKEY_CURRENT_USER, entry.path)
    try:
        for value in entry.values:
            winreg.SetValueEx(key, value.name, 0, value.kind, value.value)
    finally:
        winreg.CloseKey(key)


def _create_key(root: object, path: str):
    assert winreg is not None
    key = root
    for part in path.split("\\"):
        key = winreg.CreateKeyEx(key, part, 0, winreg.KEY_WRITE)
    return key


def _delete_tree(root: object, path: str) -> None:
    assert winreg is not None
    try:
        key = winreg.OpenKey(root, path, 0, winreg.KEY_READ | winreg.KEY_WRITE)
    except FileNotFoundError:
        return
    try:
        while True:
            try:
                child = winreg.EnumKey(key, 0)
            except OSError:
                break
            _delete_tree(key, child)
        winreg.CloseKey(key)
        winreg.DeleteKey(root, path)
    except OSError:
        winreg.CloseKey(key)


def _reg_kind(kind: str) -> int:
    assert winreg is not None
    return {
        "sz": winreg.REG_SZ,
        "none": winreg.REG_NONE,
    }[kind]
