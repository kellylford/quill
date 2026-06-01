from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from quill.core.safe_archive import (
    DecompressionBombError,
    check_zip_safety,
    open_zip,
)


def _make_zip(path: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def test_open_zip_allows_normal_archive(tmp_path: Path) -> None:
    target = tmp_path / "ok.zip"
    _make_zip(target, {"a.txt": b"hello world", "b.txt": b"more text"})
    with open_zip(target) as archive:
        assert archive.read("a.txt") == b"hello world"


def test_total_size_cap_rejects_large_archive(tmp_path: Path) -> None:
    target = tmp_path / "big.zip"
    # Highly compressible payload: small on disk, large uncompressed.
    _make_zip(target, {"big.txt": b"\0" * (4 * 1024 * 1024)})
    with zipfile.ZipFile(target) as archive:
        with pytest.raises(DecompressionBombError):
            check_zip_safety(archive, max_total=1024)


def test_compression_ratio_cap_rejects_bomb(tmp_path: Path) -> None:
    target = tmp_path / "bomb.zip"
    # 2 MiB of zeros compresses to a few KiB: ratio far above the limit.
    _make_zip(target, {"bomb.txt": b"\0" * (2 * 1024 * 1024)})
    with zipfile.ZipFile(target) as archive:
        with pytest.raises(DecompressionBombError):
            check_zip_safety(archive, max_ratio=50)


def test_open_zip_enforces_limits(tmp_path: Path) -> None:
    target = tmp_path / "bomb.zip"
    _make_zip(target, {"bomb.txt": b"\0" * (2 * 1024 * 1024)})
    with pytest.raises(DecompressionBombError):
        with open_zip(target, max_total=1024):
            pass
