"""Update manager integration with app_updater for accessible update UX.

Manages update checks and callbacks with screen-reader announcements.
Integrates AccessibleApps/app_updater for cross-platform incremental updates.

Upstream: https://github.com/accessibleapps/app_updater (MIT License)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from quill._vendor.autoupdate.autoupdate import perform_update
except ImportError:
    perform_update = None


class QuillUpdateManager:
    """Manages update checks and callbacks with accessible announcements."""

    def __init__(self, main_frame: object, endpoint: str, current_version: str) -> None:
        """Initialize update manager.

        Args:
            main_frame: Reference to MainFrame for announcements and dialogs.
            endpoint: URL to the app_updater-compatible JSON endpoint.
            current_version: Current app version (e.g., "1.0.0").
        """
        self.main_frame = main_frame
        self.endpoint = endpoint
        self.current_version = current_version
        self.is_updating = False

    def check_for_updates(self) -> None:
        """Check for updates and show a dialog if one is available.

        This is the public entry point for manual update checks.
        Can be called from Help menu or on startup (if enabled in settings).
        """
        if perform_update is None:
            self._announce("Update checker not installed. Install autoupdate to enable.")
            return

        if self.is_updating:
            self._announce("Update already in progress.")
            return

        self.is_updating = True
        try:
            perform_update(
                endpoint=self.endpoint,
                current_version=self.current_version,
                app_name="Quill",
                update_available_callback=self._on_update_available,
                progress_callback=self._on_download_progress,
                update_complete_callback=self._on_update_complete,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Update check failed: %s", exc)
            self._announce(f"Update check failed: {exc}")
            self.is_updating = False

    def _on_update_available(self, version: str, description: str) -> bool:
        """Callback when a new version is available.

        Args:
            version: New version string.
            description: Release notes or description.

        Returns:
            True to accept and download, False to skip.
        """
        self._announce(f"Quill {version} is available. {description}")
        # In a real implementation, this would show a dialog with Yes/No buttons.
        # For now, return True to proceed (caller can override behavior).
        return True

    def _on_download_progress(self, downloaded: int, total: int) -> None:
        """Callback during download progress.

        Args:
            downloaded: Bytes downloaded so far.
            total: Total bytes to download.
        """
        percent = int((downloaded / total) * 100) if total > 0 else 0
        # Update status bar with progress (will be announced by screen reader).
        self._set_status(f"Downloading update: {percent}%")

    def _on_update_complete(self) -> None:
        """Callback when update is prepared and ready to install.

        The bootstrapper will wait for app exit and apply changes.
        """
        self._announce("Update ready. Quill will restart to apply changes when you exit.")
        self.is_updating = False

    def _announce(self, message: str) -> None:
        """Announce a message through the screen reader."""
        try:
            from quill.platform.windows.prism_bridge import announce

            announce(message)
        except Exception:  # noqa: BLE001
            logger.info("Announcement: %s", message)

    def _set_status(self, message: str) -> None:
        """Update status bar message."""
        try:
            if hasattr(self.main_frame, "set_status_message"):
                self.main_frame.set_status_message(message)
        except Exception:  # noqa: BLE001
            pass
