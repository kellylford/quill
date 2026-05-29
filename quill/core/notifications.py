from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic


@dataclass(frozen=True, slots=True)
class Notification:
    timestamp: str
    category: str
    message: str

    @classmethod
    def create(cls, message: str, category: str = "info") -> Notification:
        return cls(
            timestamp=datetime.now(UTC).isoformat(),
            category=category,
            message=message.strip(),
        )


def notifications_path() -> Path:
    return app_data_dir() / "notifications.json"


def load_notifications() -> list[Notification]:
    raw = read_json(notifications_path(), default=[])
    if not isinstance(raw, list):
        return []
    entries: list[Notification] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        timestamp = str(item.get("timestamp", "")).strip()
        category = str(item.get("category", "info")).strip() or "info"
        message = str(item.get("message", "")).strip()
        if not timestamp or not message:
            continue
        entries.append(Notification(timestamp=timestamp, category=category, message=message))
    return entries


def save_notifications(entries: list[Notification], limit: int = 200) -> None:
    trimmed = entries[-limit:]
    write_json_atomic(notifications_path(), [asdict(entry) for entry in trimmed])


def add_notification(message: str, category: str = "info", limit: int = 200) -> list[Notification]:
    entries = load_notifications()
    entries.append(Notification.create(message, category))
    save_notifications(entries, limit=limit)
    return entries[-limit:]


def clear_notifications() -> None:
    write_json_atomic(notifications_path(), [])
