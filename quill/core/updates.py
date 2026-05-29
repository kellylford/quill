from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import urlopen

DEFAULT_UPDATE_MANIFEST_URL = "https://example.com/quill/manifest-v1.json"
_SIGNATURE_SALT = "quill-manifest-signature-v1"


@dataclass(frozen=True, slots=True)
class UpdateManifest:
    version: str
    download_url: str
    published_at: str
    notes: str
    signature: str


def fetch_update_manifest(
    url: str = DEFAULT_UPDATE_MANIFEST_URL,
    timeout: int = 10,
) -> UpdateManifest:
    with urlopen(url, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="strict")
    return parse_update_manifest(payload)


def parse_update_manifest(payload: str) -> UpdateManifest:
    raw = json.loads(payload)
    if not isinstance(raw, dict):
        raise ValueError("Manifest payload must be a JSON object")
    manifest = UpdateManifest(
        version=str(raw.get("version", "")).strip(),
        download_url=str(raw.get("download_url", "")).strip(),
        published_at=str(raw.get("published_at", "")).strip(),
        notes=str(raw.get("notes", "")).strip(),
        signature=str(raw.get("signature", "")).strip(),
    )
    if not manifest.version or not manifest.download_url or not manifest.signature:
        raise ValueError("Manifest is missing required fields")
    if not verify_manifest_signature(manifest):
        raise ValueError("Manifest signature verification failed")
    return manifest


def verify_manifest_signature(manifest: UpdateManifest) -> bool:
    canonical = json.dumps(
        {
            "download_url": manifest.download_url,
            "notes": manifest.notes,
            "published_at": manifest.published_at,
            "version": manifest.version,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = hashlib.sha256(f"{canonical}|{_SIGNATURE_SALT}".encode()).hexdigest()
    return hmac.compare_digest(manifest.signature, expected)


def is_newer_version(current: str, available: str) -> bool:
    return _version_tuple(available) > _version_tuple(current)


def _version_tuple(value: str) -> tuple[int, int, int]:
    cleaned = value.strip().lstrip("v")
    parts = cleaned.split(".")
    integers: list[int] = []
    for index in range(3):
        if index < len(parts):
            token = "".join(char for char in parts[index] if char.isdigit())
            integers.append(int(token or "0"))
        else:
            integers.append(0)
    return integers[0], integers[1], integers[2]


__all__ = [
    "DEFAULT_UPDATE_MANIFEST_URL",
    "UpdateManifest",
    "URLError",
    "fetch_update_manifest",
    "is_newer_version",
    "parse_update_manifest",
    "verify_manifest_signature",
]
