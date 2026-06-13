"""First-party contribution facade — the trusted half of the Quillins grammar.

This is the single piece of *new* core surface introduced by the menus-as-data /
Quillin migration (``docs/quillins.md`` Wave 0). It lets QUILL's own
built-in features describe themselves with the **same contribution vocabulary**
that third-party Quillins use — a :class:`~quill.core.quillins.model.ExtensionCommand`
(``id``, ``title``, handler), its placement in a menu, and its hotkey — and feed
them through the **same** merge/conflict engine
(:func:`quill.core.quillins.registry.build_registry`).

The asymmetry between this facade and the third-party ``QuillExtensionApi`` is the
trust boundary, not a second mechanism (migration plan §4):

* First-party command ids keep their existing namespaces (``power.*``, ``lines.*``,
  …); they are **not** forced under ``ext.`` and they may attach under any
  real top-level menu (``Insert``/``Search`` included), because they bypass the
  third-party :mod:`quill.core.quillins.validation` contract while still flowing
  through the shared registry for uniqueness and hotkey-collision detection.
* This module is wx-free and performs no IO. The live ``MainFrame`` wires the
  resulting registry onto real ``wx`` menus; that adapter lives in ``quill/ui``.

Nothing here mutates global state: a :class:`FirstPartyRegistrar` collects
declarations and emits an immutable
:class:`~quill.core.quillins.model.ExtensionManifest`, exactly as if a Quillin had
shipped that manifest on disk.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from quill.core.quillins.model import (
    ContextMenuContribution,
    Contributions,
    ExtensionCommand,
    ExtensionManifest,
    HotkeyContribution,
    MenuContribution,
)
from quill.core.quillins.registry import ContributionRegistry, build_registry


@runtime_checkable
class Host(Protocol):
    """The trusted first-party execution facade (migration plan §3/§4).

    A migrated feature module exposes handlers that take a ``Host`` and reach the
    editor, status line, announcer, and dialogs *only* through it — never by
    importing ``wx`` or reaching into ``MainFrame`` internals. This is the
    superset of the third-party ``QuillExtensionApi``; the breadth gap (settings,
    workers, platform, …) is the trust boundary, added per wave as features move.

    The live implementation lives in ``quill/ui`` (it wraps ``MainFrame``); this
    protocol is wx-free so feature handlers and their tests stay framework-free.
    """

    def get_text(self) -> str:
        """Return the active editor buffer's full text."""

    def get_selection(self) -> tuple[int, int]:
        """Return the ``(start, end)`` selection offsets (equal when none)."""

    def is_read_only(self) -> bool:
        """Return whether the active document blocks edits."""

    def set_status(self, message: str) -> None:
        """Show a transient status-line message (no screen-reader interrupt)."""

    def announce(self, message: str) -> None:
        """Announce ``message`` through the one announcement engine."""

    def prompt(self, title: str, label: str, value: str = "") -> str | None:
        """Ask for one line of text; return ``None`` when cancelled."""

    def transform_block(self, transform: Callable[[str], str], status: str) -> None:
        """Apply ``transform`` to the selection (or whole document) undoably.

        Honours the read-only guard, replaces the affected range through the core
        command/history path, reselects the result, and reports ``status`` — the
        single mutation primitive migrated line/format commands build on.
        """


# The synthetic extension id under which first-party contributions are merged.
# It carries no ``ext.`` prefix and never round-trips through the on-disk loader;
# it exists only so the shared registry can attribute first-party rows.
FIRST_PARTY_EXTENSION_ID = "quill.firstparty"

# The real top-level menus a first-party command may attach under. This is a
# superset of :data:`quill.core.quillins.model.MENU_PARENTS` (which intentionally
# stays narrow for *untrusted* extensions); first-party code owns the whole bar.
FIRST_PARTY_MENU_PARENTS: tuple[str, ...] = (
    "File",
    "Edit",
    "View",
    "Insert",
    "Format",
    "Navigate",
    "Search",
    "Tools",
    "Window",
    "Help",
)


@dataclass(frozen=True, slots=True)
class MenuPlacement:
    """Where and how a first-party command appears on the menu bar.

    ``top_level`` is the conventional top-level menu the registry files the
    command under (the data the menus-as-data endgame keys off). ``group`` and
    ``label`` describe the live submenu wiring: commands sharing a ``group`` are
    appended together, in declaration order, by one data-driven helper, and
    ``separator_before`` reproduces the visual grouping a hand-written builder
    would insert.
    """

    top_level: str
    group: str
    label: str
    separator_before: bool = False


@dataclass(frozen=True, slots=True)
class FirstPartyCommand:
    """A built-in command expressed in the shared contribution grammar."""

    id: str
    title: str
    placement: MenuPlacement
    binding: str = ""
    context_when: str | None = None

    @property
    def handler_name(self) -> str:
        """The mixin method that implements this command.

        First-party handlers follow the convention ``<namespace>.<method>`` →
        ``self.<method>``; e.g. ``power.number_lines`` resolves to
        ``self.number_lines``. The whole-bar wiring relies on this so the
        declarative table never has to repeat the handler reference.
        """

        _, _, tail = self.id.partition(".")
        return tail or self.id


class FirstPartyRegistrar:
    """Collect first-party command declarations and emit a manifest.

    Mirrors the third-party ``register(api)`` shape: a feature module calls
    :meth:`add_command` once per command, and the registrar produces an immutable
    :class:`ExtensionManifest` plus a merged
    :class:`~quill.core.quillins.registry.ContributionRegistry`. This is the
    trusted "registration quartet" half of the host facade (migration plan §4),
    decoupled from any ``wx`` menu construction.
    """

    def __init__(self) -> None:
        self._commands: list[FirstPartyCommand] = []
        self._seen: set[str] = set()

    def add_command(
        self,
        *,
        id: str,
        title: str,
        top_level: str,
        group: str,
        label: str,
        separator_before: bool = False,
        binding: str = "",
        context_when: str | None = None,
    ) -> FirstPartyCommand:
        """Declare one first-party command and return the stored record."""

        if top_level not in FIRST_PARTY_MENU_PARENTS:
            raise ValueError(
                f"unknown top-level menu {top_level!r} for {id!r}; "
                f"expected one of {FIRST_PARTY_MENU_PARENTS}"
            )
        if id in self._seen:
            raise ValueError(f"duplicate first-party command id: {id!r}")
        command = FirstPartyCommand(
            id=id,
            title=title,
            placement=MenuPlacement(
                top_level=top_level,
                group=group,
                label=label,
                separator_before=separator_before,
            ),
            binding=binding,
            context_when=context_when,
        )
        self._commands.append(command)
        self._seen.add(id)
        return command

    @property
    def commands(self) -> tuple[FirstPartyCommand, ...]:
        return tuple(self._commands)

    def commands_in_group(self, group: str) -> tuple[FirstPartyCommand, ...]:
        """Commands declared under ``group``, in declaration order."""

        return tuple(c for c in self._commands if c.placement.group == group)

    def manifest(self, extension_id: str = FIRST_PARTY_EXTENSION_ID) -> ExtensionManifest:
        return build_first_party_manifest(self._commands, extension_id=extension_id)

    def registry(self, *, host_keymap: Mapping[str, str] | None = None) -> ContributionRegistry:
        return build_first_party_registry(self._commands, host_keymap=host_keymap)


def build_first_party_manifest(
    commands: Iterable[FirstPartyCommand],
    *,
    extension_id: str = FIRST_PARTY_EXTENSION_ID,
) -> ExtensionManifest:
    """Express first-party ``commands`` as a Quillins :class:`ExtensionManifest`.

    The handler name is recorded on each :class:`ExtensionCommand` so the live
    adapter can resolve it by convention; menu and hotkey placements become the
    same :class:`MenuContribution` / :class:`HotkeyContribution` rows a Quillin
    would ship.
    """

    extension_commands: list[ExtensionCommand] = []
    menus: list[MenuContribution] = []
    hotkeys: list[HotkeyContribution] = []
    context_menu: list[ContextMenuContribution] = []
    for command in commands:
        extension_commands.append(
            ExtensionCommand(
                id=command.id,
                title=command.title,
                handler=command.handler_name,
            )
        )
        menus.append(MenuContribution(parent=command.placement.top_level, command=command.id))
        if command.binding:
            hotkeys.append(HotkeyContribution(command=command.id, binding=command.binding))
        if command.context_when is not None:
            context_menu.append(
                ContextMenuContribution(command=command.id, when=command.context_when)
            )
    return ExtensionManifest(
        id=extension_id,
        name="QUILL built-ins",
        version="1.0",
        author="QUILL",
        description="First-party commands expressed in the contribution grammar.",
        contributes=Contributions(
            commands=tuple(extension_commands),
            menus=tuple(menus),
            context_menu=tuple(context_menu),
            hotkeys=tuple(hotkeys),
        ),
    )


def build_first_party_registry(
    commands: Iterable[FirstPartyCommand],
    *,
    host_keymap: Mapping[str, str] | None = None,
    extension_id: str = FIRST_PARTY_EXTENSION_ID,
) -> ContributionRegistry:
    """Merge first-party ``commands`` through the shared contribution registry.

    Reuses :func:`quill.core.quillins.registry.build_registry` verbatim, so
    first-party command-id uniqueness and hotkey collisions (against the host
    keymap and any other contribution) are enforced by the same code path that
    guards third-party Quillins.
    """

    manifest = build_first_party_manifest(commands, extension_id=extension_id)
    return build_registry([manifest], host_keymap=host_keymap)
