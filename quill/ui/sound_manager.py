"""QSP sound notification manager for QUILL's UI layer.

Owns the :class:`~quill.platform.sound_player.SoundPlayer` singleton and
exposes :func:`post_sound` as a simple, thread-safe call site that any module
can use without importing wx or caring about the audio backend.

Lifecycle (called by MainFrame)
--------------------------------
1. ``init(settings)``       — load pack and configure player at startup.
2. ``on_settings_changed(settings)`` — reload if pack path or enabled flag changed.
3. ``shutdown()``           — drain and close the player at app exit.

Usage from any module
----------------------
::

    from quill.core.sound_events import SoundEvent
    from quill.ui.sound_manager import post_sound

    post_sound(SoundEvent.ABBREVIATION_EXPANDED)

``post_sound`` is a no-op when the manager is not yet initialised (e.g. in
headless tests or before ``init()`` is called).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quill.core.settings import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton — set by init(), cleared by shutdown()
# ---------------------------------------------------------------------------

_manager: _SoundManager | None = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init(settings: Settings) -> None:
    """Create (or replace) the manager and load the configured pack."""
    global _manager
    if _manager is not None:
        _manager.shutdown()
    _manager = _SoundManager(settings)


def shutdown() -> None:
    """Drain and destroy the manager."""
    global _manager
    if _manager is not None:
        _manager.shutdown()
        _manager = None


def on_settings_changed(settings: Settings) -> None:
    """Reload the pack / reconfigure if relevant settings changed."""
    if _manager is not None:
        _manager.apply_settings(settings)


def post_sound(event_id: str) -> None:
    """Post an earcon for *event_id*.  Returns immediately; never raises.

    Safe to call from any thread and before :func:`init` is called.
    """
    if _manager is not None:
        _manager.play(event_id)


def toggle_mute() -> bool:
    """Flip the mute state.  Returns the new state (True == muted)."""
    if _manager is not None:
        return _manager.player.toggle_mute()
    return False


def is_active() -> bool:
    """Return True when the manager is initialised and sound is enabled."""
    return _manager is not None and _manager.enabled


def register_quillin_sounds(
    quillin_id: str,
    directory: Path,
    sound_pack: str,
    sound_events: tuple[tuple[str, str], ...],
) -> None:
    """Merge a Quillin's QSP contribution into the active pack.

    Called once per Quillin at registration time.  A missing or broken
    sound_pack directory is silently ignored so Quillin load never fails on
    audio issues.
    """
    if _manager is None or not sound_pack:
        return
    _manager.register_quillin_sounds(quillin_id, directory, sound_pack, sound_events)


# ---------------------------------------------------------------------------
# Internal manager class
# ---------------------------------------------------------------------------


class _SoundManager:
    def __init__(self, settings: Settings) -> None:
        from quill.platform.sound_player import SoundPlayer

        self.player = SoundPlayer()
        self.enabled: bool = False
        self._pack_path: str = ""
        self.apply_settings(settings)

    def apply_settings(self, settings: Settings) -> None:
        self.enabled = bool(getattr(settings, "sound_enabled", True))
        new_pack_path = str(getattr(settings, "sound_pack_path", ""))
        volume = int(getattr(settings, "sound_volume", 80))
        events_disabled_raw = str(getattr(settings, "sound_events_disabled", ""))
        disabled = frozenset(e.strip() for e in events_disabled_raw.split(",") if e.strip())

        if not self.enabled:
            self.player.set_muted(True)
            return

        self.player.set_muted(False)

        # Reload pack only when the path actually changed.
        if new_pack_path != self._pack_path:
            self._pack_path = new_pack_path
            self._load_pack(new_pack_path, disabled)
        else:
            self.player.set_disabled(disabled)

        self._apply_volume(volume)

    def play(self, event_id: str) -> None:
        if self.enabled:
            self.player.play(event_id)

    def shutdown(self) -> None:
        self.player.shutdown()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_pack(self, pack_path: str, disabled: frozenset[str]) -> None:
        from quill.core.sound_pack import SoundPack, SoundPackError, load_sound_pack

        path = Path(pack_path) if pack_path else self._bundled_ink_path()
        if path is None:
            logger.debug("SoundManager: no pack path and no bundled pack; earcons silent")
            self.player.load_pack(SoundPack(name="(none)", author="", description="", license=""))
            return
        try:
            pack = load_sound_pack(path)
            self.player.load_pack(pack, disabled=disabled)
        except SoundPackError as exc:
            logger.warning("SoundManager: failed to load pack %s: %s", path, exc)
            self.player.load_pack(SoundPack(name="(error)", author="", description="", license=""))

    def _apply_volume(self, volume: int) -> None:
        # sound_lib backend exposes Output.set_volume(float 0.0-1.0).
        # Access it through the backend if available.
        backend = self.player._backend  # type: ignore[attr-defined]
        output = getattr(backend, "_output", None)
        if output is not None:
            try:
                output.set_volume(volume / 100.0)
            except Exception:  # noqa: BLE001
                pass

    def register_quillin_sounds(
        self,
        quillin_id: str,
        directory: Path,
        sound_pack: str,
        sound_events: tuple[tuple[str, str], ...],
    ) -> None:
        """Merge WAV bytes from a Quillin's sound_pack into the active player pack."""
        pack_dir = directory / sound_pack
        if not pack_dir.is_dir():
            logger.debug(
                "SoundManager: Quillin %s sound_pack dir not found: %s", quillin_id, pack_dir
            )
            return
        for event_id, wav_name in sound_events:
            wav_path = pack_dir / wav_name
            if not wav_path.is_file():
                continue
            try:
                wav_bytes = wav_path.read_bytes()
                self.player.register_event(event_id, wav_bytes)
            except Exception as exc:  # noqa: BLE001
                logger.debug("SoundManager: Quillin %s sound %s: %s", quillin_id, wav_name, exc)

    @staticmethod
    def _bundled_ink_path() -> Path | None:
        """Return the path to the bundled Ink pack, or None if not present."""
        try:
            import quill

            ink = Path(quill.__file__).parent / "assets" / "sound_packs" / "ink"
            return ink if ink.exists() else None
        except Exception:  # noqa: BLE001
            return None
