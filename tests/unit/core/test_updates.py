from __future__ import annotations

import hashlib
import json

from quill.core.updates import is_newer_version, parse_update_manifest


def _signed_payload(version: str, download_url: str, published_at: str, notes: str) -> str:
    canonical = json.dumps(
        {
            "download_url": download_url,
            "notes": notes,
            "published_at": published_at,
            "version": version,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    signature = hashlib.sha256(f"{canonical}|quill-manifest-signature-v1".encode()).hexdigest()
    return json.dumps(
        {
            "version": version,
            "download_url": download_url,
            "published_at": published_at,
            "notes": notes,
            "signature": signature,
        }
    )


def test_parse_update_manifest_accepts_valid_signature() -> None:
    payload = _signed_payload("1.2.3", "https://example.com/download", "2026-05-01", "Fixes.")
    manifest = parse_update_manifest(payload)
    assert manifest.version == "1.2.3"
    assert manifest.download_url == "https://example.com/download"


def test_parse_update_manifest_rejects_bad_signature() -> None:
    payload = json.dumps(
        {
            "version": "1.2.3",
            "download_url": "https://example.com/download",
            "published_at": "2026-05-01",
            "notes": "Fixes.",
            "signature": "bad",
        }
    )
    try:
        parse_update_manifest(payload)
    except ValueError as exc:
        assert "signature verification failed" in str(exc)
    else:
        raise AssertionError("Expected signature verification failure")


def test_is_newer_version_compares_semver_triplets() -> None:
    assert is_newer_version("0.1.0", "0.2.0") is True
    assert is_newer_version("1.2.3", "1.2.3") is False
