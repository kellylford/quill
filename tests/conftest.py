"""Root test configuration.

Activates the ``_DEV_BUILD`` flag in :mod:`quill.core.paths` for the entire
test suite so that ``QUILL_DATA_DIR`` overrides (used by almost every test
fixture for isolation) are honoured.  Without this flag the guard added by
H-1-core silently ignores ``QUILL_DATA_DIR`` in non-dev builds, causing tests
to write to the real ``%APPDATA%\\Quill`` path and fail with stale state.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True, scope="session")
def _enable_dev_build_for_tests() -> None:
    """Patch paths._DEV_BUILD=True for the whole test session."""
    import quill.core.paths as paths_mod

    paths_mod._DEV_BUILD = True
