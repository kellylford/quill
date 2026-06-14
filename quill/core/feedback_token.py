"""Resolve the GitHub token used for issue submission (#210 follow-up).

Both the Report a Bug dialog and the crash reporter need a GitHub token to
create an issue. This unifies the sources: QUILL's OS-encrypted token store is
the single source of truth, with a one-time import of whatever ``feedback_hub``
resolves from the environment so a token configured for one path is reliably
available to the other. No token is ever bundled or written to the repo; the
store is per-user and encrypted (Windows Credential Manager / macOS Keychain).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def effective_github_token(*, import_from_env: bool = True) -> str:
    """Return the GitHub token to use, or an empty string when none is available.

    Order of preference:

    1. QUILL's secure token store (``token_store.load_github_token``).
    2. The token ``feedback_hub.resolve_token()`` finds in the environment.

    When a token is found only in the environment and the secure store is empty,
    it is copied into the store (best effort) so subsequent calls — and the
    other reporting path — resolve it reliably without depending on env vars.
    """
    from quill.core.github.token_store import load_github_token, save_github_token

    stored = load_github_token()
    if stored:
        return stored

    env_token = ""
    try:
        from feedback_hub import resolve_token

        env_token = (resolve_token() or "").strip()
    except Exception:  # noqa: BLE001 - a missing/broken feedback_hub is non-fatal
        env_token = ""

    if env_token and import_from_env:
        try:
            save_github_token(env_token)
        except Exception:  # noqa: BLE001 - persisting is a convenience, not required
            logger.warning("Could not persist resolved GitHub token", exc_info=True)
    return env_token


def github_token_present() -> bool:
    """Return True when a token is available without importing it into the store."""
    return bool(effective_github_token(import_from_env=False))
