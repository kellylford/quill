"""Tests for the translation infrastructure CI gate."""

from __future__ import annotations

from quill.tools.check_translation import check_babel_cfg, check_pot_exists


def test_babel_cfg_exists() -> None:
    """babel.cfg must exist at the project root."""
    errors = check_babel_cfg()
    assert not errors, "\n".join(errors)


def test_pot_file_present_or_friendly_error() -> None:
    """check_pot_exists returns a helpful message if the .pot is absent.

    We do not fail the test when the .pot is absent (it is generated, not
    checked in), but we do verify that the error message includes a usable
    pybabel command.
    """
    errors = check_pot_exists()
    for err in errors:
        assert "pybabel" in err, f"Error message missing pybabel hint: {err!r}"
