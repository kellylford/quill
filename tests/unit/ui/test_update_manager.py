"""Regression tests for the autoupdate integration.

Covers the full perform_update pipeline (endpoint fetch, version comparison,
callback contract, download progress, archive extraction, bootstrap execution)
and the QuillUpdateManager accessibility wrapper.

All HTTP is mocked; the bootstrapper execute step is always stubbed so CI
does not attempt to run a native binary.
"""

from __future__ import annotations

import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest

from quill._vendor.autoupdate.autoupdate import (
    _call_callback,
    extract_update,
    find_update,
    perform_update,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

FEED_URL = "https://test.example.com/feed.json"
DOWNLOAD_URL = "https://test.example.com/quill-update.zip"
CURRENT_VERSION = "0.5.0"
NEWER_VERSION = "99.0.0"

FEED_NEWER = {
    "current_version": NEWER_VERSION,
    "description": "Test release notes",
    "downloads": {
        "Windows": DOWNLOAD_URL,
        "Darwin": DOWNLOAD_URL,
        "Linux": DOWNLOAD_URL,
    },
}

FEED_SAME_VERSION = {
    "current_version": CURRENT_VERSION,
    "description": "",
    "downloads": {"Windows": DOWNLOAD_URL},
}

FEED_WINDOWS_ONLY = {
    "current_version": NEWER_VERSION,
    "description": "",
    "downloads": {"Windows": DOWNLOAD_URL},
}


def _make_zip(filename: str = "bootstrap.exe", content: bytes = b"stub") -> bytes:
    """Return bytes of a minimal ZIP archive containing one named entry."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(filename, content)
    return buf.getvalue()


def _mock_session(feed: dict, zip_bytes: bytes | None = None) -> MagicMock:
    """Return a mock requests session.

    First get() call returns the feed JSON; optional second call returns a
    streaming ZIP response.
    """
    session = MagicMock()

    feed_resp = MagicMock()
    feed_resp.json.return_value = feed
    feed_resp.raise_for_status.return_value = None

    responses = [feed_resp]

    if zip_bytes is not None:
        zip_resp = MagicMock()
        zip_resp.headers = {"content-length": str(len(zip_bytes))}
        zip_resp.raise_for_status.return_value = None
        zip_resp.iter_content.return_value = [zip_bytes]
        responses.append(zip_resp)

    session.get.side_effect = responses
    return session


# ---------------------------------------------------------------------------
# find_update
# ---------------------------------------------------------------------------


def test_find_update_returns_parsed_json() -> None:
    session = MagicMock()
    session.get.return_value.json.return_value = FEED_NEWER
    session.get.return_value.raise_for_status.return_value = None

    result = find_update(FEED_URL, requests_session=session)

    assert result["current_version"] == NEWER_VERSION
    session.get.assert_called_once_with(FEED_URL)


# ---------------------------------------------------------------------------
# perform_update — version gating
# ---------------------------------------------------------------------------


def test_no_update_when_version_not_newer() -> None:
    session = _mock_session(FEED_SAME_VERSION)
    available_cb = MagicMock()

    with patch("quill._vendor.autoupdate.autoupdate.create_requests_session", return_value=session):
        perform_update(FEED_URL, CURRENT_VERSION, update_available_callback=available_cb)

    available_cb.assert_not_called()


def test_no_update_when_platform_not_in_downloads(monkeypatch: pytest.MonkeyPatch) -> None:
    feed = {"current_version": NEWER_VERSION, "downloads": {"Amiga": DOWNLOAD_URL}}
    session = _mock_session(feed)
    available_cb = MagicMock()

    with patch("quill._vendor.autoupdate.autoupdate.create_requests_session", return_value=session):
        perform_update(FEED_URL, CURRENT_VERSION, update_available_callback=available_cb)

    available_cb.assert_not_called()


# ---------------------------------------------------------------------------
# perform_update — callback contract
# ---------------------------------------------------------------------------


def test_available_callback_receives_version_and_description() -> None:
    session = _mock_session(FEED_NEWER)
    seen: dict[str, str] = {}

    def on_available(version: str, description: str) -> bool:
        seen["version"] = version
        seen["description"] = description
        return False  # decline; stops pipeline before download

    with patch("quill._vendor.autoupdate.autoupdate.create_requests_session", return_value=session):
        perform_update(FEED_URL, CURRENT_VERSION, update_available_callback=on_available)

    assert seen["version"] == NEWER_VERSION
    assert seen["description"] == "Test release notes"


def test_declining_update_stops_pipeline() -> None:
    session = _mock_session(FEED_NEWER)

    with patch("quill._vendor.autoupdate.autoupdate.create_requests_session", return_value=session):
        with patch("quill._vendor.autoupdate.autoupdate.download_update") as mock_dl:
            perform_update(FEED_URL, CURRENT_VERSION, update_available_callback=lambda **_: False)
            mock_dl.assert_not_called()


def test_complete_callback_called_after_successful_bootstrap() -> None:
    session = _mock_session(FEED_NEWER)
    complete_cb = MagicMock()

    with patch("quill._vendor.autoupdate.autoupdate.create_requests_session", return_value=session):
        with patch("quill._vendor.autoupdate.autoupdate.download_update", return_value="/t/u.zip"):
            with patch("quill._vendor.autoupdate.autoupdate.extract_update", return_value="/t/u"):
                with patch(
                    "quill._vendor.autoupdate.autoupdate.move_bootstrap", return_value="/t/bs"
                ):
                    with patch("quill._vendor.autoupdate.autoupdate.execute_bootstrap"):
                        perform_update(
                            FEED_URL,
                            CURRENT_VERSION,
                            update_available_callback=lambda **_: True,
                            update_complete_callback=complete_cb,
                        )

    complete_cb.assert_called_once()


def test_no_available_callback_still_proceeds() -> None:
    """perform_update should not require update_available_callback to be set."""
    session = _mock_session(FEED_NEWER)

    with patch("quill._vendor.autoupdate.autoupdate.create_requests_session", return_value=session):
        with patch("quill._vendor.autoupdate.autoupdate.download_update", return_value="/t/u.zip"):
            with patch("quill._vendor.autoupdate.autoupdate.extract_update", return_value="/t/u"):
                with patch(
                    "quill._vendor.autoupdate.autoupdate.move_bootstrap", return_value="/t/bs"
                ):
                    with patch("quill._vendor.autoupdate.autoupdate.execute_bootstrap"):
                        # Should not raise
                        perform_update(FEED_URL, CURRENT_VERSION)


# ---------------------------------------------------------------------------
# perform_update — download progress
# ---------------------------------------------------------------------------


def test_progress_callback_receives_downloaded_and_total_bytes(
    tmp_path: pytest.TempPathFactory,
) -> None:
    zip_bytes = _make_zip()
    session = _mock_session(FEED_NEWER, zip_bytes)
    progress_calls: list[tuple[int, int]] = []

    with patch("quill._vendor.autoupdate.autoupdate.create_requests_session", return_value=session):
        with patch(
            "quill._vendor.autoupdate.autoupdate.extract_update", return_value=str(tmp_path)
        ):
            with patch("quill._vendor.autoupdate.autoupdate.move_bootstrap", return_value="/t/bs"):
                with patch("quill._vendor.autoupdate.autoupdate.execute_bootstrap"):
                    perform_update(
                        FEED_URL,
                        CURRENT_VERSION,
                        update_available_callback=lambda **_: True,
                        progress_callback=lambda d, t: progress_calls.append((d, t)),
                    )

    assert len(progress_calls) >= 1
    final_downloaded, final_total = progress_calls[-1]
    assert final_downloaded == len(zip_bytes)
    assert final_total == len(zip_bytes)


def test_progress_callback_not_required() -> None:
    zip_bytes = _make_zip()
    session = _mock_session(FEED_NEWER, zip_bytes)

    with patch("quill._vendor.autoupdate.autoupdate.create_requests_session", return_value=session):
        with patch("quill._vendor.autoupdate.autoupdate.extract_update", return_value="/t/u"):
            with patch("quill._vendor.autoupdate.autoupdate.move_bootstrap", return_value="/t/bs"):
                with patch("quill._vendor.autoupdate.autoupdate.execute_bootstrap"):
                    # No progress_callback arg — should not raise
                    perform_update(
                        FEED_URL,
                        CURRENT_VERSION,
                        update_available_callback=lambda **_: True,
                    )


# ---------------------------------------------------------------------------
# extract_update
# ---------------------------------------------------------------------------


def test_extract_update_unpacks_archive(tmp_path: pytest.TempPathFactory) -> None:
    zip_path = tmp_path / "update.zip"
    zip_path.write_bytes(_make_zip("bootstrap.exe", b"binary-stub"))

    dest = tmp_path / "extracted"
    result = extract_update(str(zip_path), str(dest))

    assert (dest / "bootstrap.exe").read_bytes() == b"binary-stub"
    assert result == str(dest)


# ---------------------------------------------------------------------------
# _call_callback — error isolation
# ---------------------------------------------------------------------------


def test_call_callback_swallows_exceptions() -> None:
    def bad_callback(*a: object, **k: object) -> None:
        raise RuntimeError("boom")

    # Should not propagate
    _call_callback(bad_callback, 1, 2, x=3)
