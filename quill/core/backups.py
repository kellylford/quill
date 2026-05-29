from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha1
from pathlib import Path

from quill.core.document import Document
from quill.core.paths import app_data_dir


def backup_document(document: Document) -> Path:
    backup_root = app_data_dir() / "backups" / _document_key(document)
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = backup_root / f"{stamp}.bak"
    with backup_path.open("w", encoding=document.encoding, newline="") as file_handle:
        file_handle.write(document.text)
    return backup_path


def list_backups(document_path: Path) -> list[Path]:
    doc = Document(path=document_path)
    backup_root = app_data_dir() / "backups" / _document_key(doc)
    if not backup_root.exists():
        return []
    return sorted(backup_root.glob("*.bak"), reverse=True)


def _document_key(document: Document) -> str:
    seed = str(document.path.resolve()) if document.path else "untitled"
    return sha1(seed.encode("utf-8")).hexdigest()
