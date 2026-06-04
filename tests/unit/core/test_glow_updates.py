"""GLOW-8 consented engine updates: manifest, verification, and apply paths."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

import pytest

from quill.core import glow_updates as gu


def _sign(payload: dict) -> str:
    canonical = json.dumps(
        {
            "component": payload["component"],
            "notes": payload["notes"],
            "published_at": payload["published_at"],
            "version": payload["version"],
            "wheels": [
                {"filename": w["filename"], "sha256": w["sha256"], "url": w["url"]}
                for w in sorted(payload["wheels"], key=lambda w: w["filename"])
            ],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    key = os.getenv(gu._GLOW_MANIFEST_KEY_ENV, gu._GLOW_SIGNATURE_SALT).encode("utf-8")
    return hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def _manifest_dict(version: str = "8.1.0") -> dict:
    payload = {
        "version": version,
        "component": "quill-glow-core",
        "published_at": "2026-06-03T00:00:00Z",
        "notes": "Bug fixes",
        "wheels": [
            {
                "filename": "quill_glow_core-8.1.0-py3-none-any.whl",
                "url": "https://community-access.github.io/quill/updates/quill_glow_core-8.1.0-py3-none-any.whl",
                "sha256": "a" * 64,
            }
        ],
    }
    payload["signature"] = _sign(payload)
    return payload


# --- Manifest parsing + signature -------------------------------------------


def test_parse_valid_manifest_round_trips() -> None:
    manifest = gu.parse_glow_manifest(json.dumps(_manifest_dict()))
    assert manifest.version == "8.1.0"
    assert manifest.component == "quill-glow-core"
    assert len(manifest.wheels) == 1
    assert manifest.wheels[0].filename.endswith(".whl")


def test_parse_rejects_tampered_signature() -> None:
    raw = _manifest_dict()
    raw["version"] = "9.9.9"  # change content without re-signing
    with pytest.raises(ValueError, match="signature verification failed"):
        gu.parse_glow_manifest(json.dumps(raw))


def test_parse_rejects_non_https_wheel_url() -> None:
    raw = _manifest_dict()
    raw["wheels"][0]["url"] = "http://example.com/x.whl"
    raw["signature"] = _sign(raw)
    with pytest.raises(ValueError):
        gu.parse_glow_manifest(json.dumps(raw))


def test_parse_rejects_empty_wheels() -> None:
    raw = _manifest_dict()
    raw["wheels"] = []
    raw["signature"] = _sign(raw)
    with pytest.raises(ValueError, match="at least one wheel"):
        gu.parse_glow_manifest(json.dumps(raw))


def test_verify_signature_true_for_signed_manifest() -> None:
    manifest = gu.parse_glow_manifest(json.dumps(_manifest_dict()))
    assert gu.verify_glow_manifest_signature(manifest) is True


# --- Version comparison ------------------------------------------------------


def test_check_reports_update_when_installed_older(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gu, "installed_glow_version", lambda: "8.0.0")
    monkeypatch.setattr(
        gu,
        "fetch_glow_manifest",
        lambda *a, **k: gu.parse_glow_manifest(json.dumps(_manifest_dict("8.1.0"))),
    )
    check = gu.check_for_glow_update()
    assert check.update_available is True
    assert check.available_version == "8.1.0"
    assert check.installed_version == "8.0.0"


def test_check_reports_no_update_when_current(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gu, "installed_glow_version", lambda: "8.1.0")
    monkeypatch.setattr(
        gu,
        "fetch_glow_manifest",
        lambda *a, **k: gu.parse_glow_manifest(json.dumps(_manifest_dict("8.1.0"))),
    )
    check = gu.check_for_glow_update()
    assert check.update_available is False


def test_check_reports_update_when_nothing_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gu, "installed_glow_version", lambda: "")
    monkeypatch.setattr(
        gu,
        "fetch_glow_manifest",
        lambda *a, **k: gu.parse_glow_manifest(json.dumps(_manifest_dict("8.1.0"))),
    )
    check = gu.check_for_glow_update()
    assert check.update_available is True


# --- Download + checksum -----------------------------------------------------


def _write_wheel(tmp_path: Path, name: str, body: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(body)
    return path


def test_download_verifies_checksum(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    body = b"fake wheel bytes"
    digest = hashlib.sha256(body).hexdigest()
    raw = _manifest_dict()
    raw["wheels"][0]["sha256"] = digest
    raw["signature"] = _sign(raw)
    manifest = gu.parse_glow_manifest(json.dumps(raw))

    def fake_download(url: str, destination, timeout: int = 60, progress=None) -> None:
        Path(destination).write_bytes(body)

    monkeypatch.setattr(gu, "download_release_asset", fake_download)
    paths = gu.download_glow_wheels(manifest, tmp_path / "staging")
    assert len(paths) == 1
    assert paths[0].exists()


def test_download_rejects_bad_checksum(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = gu.parse_glow_manifest(json.dumps(_manifest_dict()))  # sha is "aaaa..."

    def fake_download(url: str, destination, timeout: int = 60, progress=None) -> None:
        Path(destination).write_bytes(b"not matching")

    monkeypatch.setattr(gu, "download_release_asset", fake_download)
    with pytest.raises(ValueError, match="checksum verification"):
        gu.download_glow_wheels(manifest, tmp_path / "staging")
    # The partial file is cleaned up.
    assert not (tmp_path / "staging" / manifest.wheels[0].filename).exists()


# --- Install + apply + rollback ---------------------------------------------


def test_install_builds_offline_pip_command(tmp_path: Path) -> None:
    wheel = _write_wheel(tmp_path, "quill_glow_core-8.1.0-py3-none-any.whl", b"x")
    captured: list[list[str]] = []

    def runner(args) -> int:
        captured.append(list(args))
        return 0

    gu.install_glow_wheels([wheel], runner=runner)
    assert captured, "runner was not invoked"
    args = captured[0]
    assert "install" in args
    assert "--no-index" in args  # offline guarantee
    assert "--find-links" in args


def test_install_raises_on_nonzero(tmp_path: Path) -> None:
    wheel = _write_wheel(tmp_path, "quill_glow_core-8.1.0-py3-none-any.whl", b"x")
    with pytest.raises(RuntimeError, match="exit code 1"):
        gu.install_glow_wheels([wheel], runner=lambda args: 1)


def test_apply_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    body = b"good wheel"
    raw = _manifest_dict()
    raw["wheels"][0]["sha256"] = hashlib.sha256(body).hexdigest()
    raw["signature"] = _sign(raw)
    manifest = gu.parse_glow_manifest(json.dumps(raw))

    def fake_download(url: str, destination, timeout: int = 60, progress=None) -> None:
        Path(destination).write_bytes(body)

    monkeypatch.setattr(gu, "download_release_asset", fake_download)
    result = gu.apply_glow_update(manifest, tmp_path / "staging", runner=lambda args: 0)
    assert result.applied is True
    assert result.version == "8.1.0"
    assert "Restart QUILL" in result.message


def test_apply_rolls_back_on_install_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = b"good wheel"
    raw = _manifest_dict()
    raw["wheels"][0]["sha256"] = hashlib.sha256(body).hexdigest()
    raw["signature"] = _sign(raw)
    manifest = gu.parse_glow_manifest(json.dumps(raw))

    def fake_download(url: str, destination, timeout: int = 60, progress=None) -> None:
        Path(destination).write_bytes(body)

    monkeypatch.setattr(gu, "download_release_asset", fake_download)

    # Provide a rollback dir holding a vendored wheel to reinstall.
    rollback = tmp_path / "vendor"
    rollback.mkdir()
    (rollback / "quill_glow_core-8.0.0-py3-none-any.whl").write_bytes(b"old")

    calls: list[list[str]] = []

    def runner(args) -> int:
        calls.append(list(args))
        # Fail the first (update) install, succeed the rollback install.
        return 1 if len(calls) == 1 else 0

    result = gu.apply_glow_update(
        manifest, tmp_path / "staging", rollback_dir=rollback, runner=runner
    )
    assert result.applied is False
    assert result.rolled_back is True
    assert len(calls) == 2  # update attempt + rollback


def test_apply_download_failure_reports_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = gu.parse_glow_manifest(json.dumps(_manifest_dict()))  # sha won't match

    def fake_download(url: str, destination, timeout: int = 60, progress=None) -> None:
        Path(destination).write_bytes(b"mismatch")

    monkeypatch.setattr(gu, "download_release_asset", fake_download)
    result = gu.apply_glow_update(manifest, tmp_path / "staging", runner=lambda args: 0)
    assert result.applied is False
    assert "download failed" in result.message
