from __future__ import annotations

import hashlib
import json
import locale
import platform
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from quill.core.document import Document
from quill.core.notifications import Notification
from quill.core.paths import app_data_dir
from quill.core.settings import Settings
from quill.core.storage import read_json, write_json_atomic


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    timestamp: str
    kind: str
    name: str
    detail: str = ""


def diagnostic_events_path() -> Path:
    return app_data_dir() / "diagnostics" / "recent-actions.json"


def load_diagnostic_events(limit: int = 50) -> list[DiagnosticEvent]:
    raw = read_json(diagnostic_events_path(), default=[])
    if not isinstance(raw, list):
        return []
    items: list[DiagnosticEvent] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        timestamp = str(entry.get("timestamp", "")).strip()
        kind = str(entry.get("kind", "")).strip()
        name = str(entry.get("name", "")).strip()
        detail = str(entry.get("detail", "")).strip()
        if not timestamp or not kind or not name:
            continue
        items.append(DiagnosticEvent(timestamp=timestamp, kind=kind, name=name, detail=detail))
    return items[-limit:]


def record_diagnostic_event(kind: str, name: str, detail: str = "", limit: int = 50) -> None:
    events = load_diagnostic_events(limit=limit)
    events.append(
        DiagnosticEvent(
            timestamp=datetime.now(UTC).isoformat(),
            kind=kind.strip(),
            name=name.strip(),
            detail=detail.strip(),
        )
    )
    write_json_atomic(diagnostic_events_path(), [asdict(item) for item in events[-limit:]])


def write_diagnostics_bundle(
    target: Path,
    *,
    settings: Settings,
    keymap: dict[str, str],
    notifications: list[Notification],
    current_document: Document | None,
    include_file_paths: bool = False,
    extra_environment: dict[str, object] | None = None,
) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    metadata = collect_environment_info(extra_environment=extra_environment)
    if current_document is not None:
        metadata["current_document"] = document_snapshot(
            current_document,
            include_file_paths=include_file_paths,
        )
    recent_actions = [asdict(item) for item in load_diagnostic_events()]
    settings_payload = redact_settings(settings)
    notifications_payload = [asdict(entry) for entry in notifications[-50:]]

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
        archive.writestr(
            "recent-actions.json",
            json.dumps(recent_actions, indent=2, ensure_ascii=False) + "\n",
        )
        archive.writestr(
            "settings-redacted.json",
            json.dumps(settings_payload, indent=2, ensure_ascii=False) + "\n",
        )
        archive.writestr("keymap.json", json.dumps(keymap, indent=2, ensure_ascii=False) + "\n")
        archive.writestr(
            "notifications.json",
            json.dumps(notifications_payload, indent=2, ensure_ascii=False) + "\n",
        )
        _write_recent_logs(archive)
    return target


def build_bug_report_payload(
    *,
    current_document: Document | None,
    extra_environment: dict[str, object] | None = None,
) -> dict[str, str]:
    metadata = collect_environment_info(extra_environment=extra_environment)
    document_label = "No document open"
    if current_document is not None:
        snapshot = document_snapshot(current_document, include_file_paths=False)
        name = snapshot.get("name")
        if isinstance(name, str) and name.strip():
            document_label = name
    summary = f"Bug report: {document_label}"
    details = [
        "Please describe what happened and what you expected to happen.",
        "",
        "Environment summary:",
        f"- Quill version: {metadata['quill_version']}",
        f"- Platform: {metadata['platform']}",
        f"- Python: {metadata['python_version']}",
        f"- Locale: {metadata['locale']}",
        f"- Current document: {document_label}",
        "",
        "If possible, attach a diagnostics bundle created from Help -> Save Diagnostics...",
    ]
    return {
        "summary": summary,
        "body": "\n".join(details),
    }


def collect_environment_info(
    extra_environment: dict[str, object] | None = None,
) -> dict[str, object]:
    info: dict[str, object] = {
        "quill_version": _safe_import_version(),
        "platform": platform.platform(),
        "windows_release": platform.release(),
        "python_version": sys.version.splitlines()[0],
        "locale": locale.getlocale(),
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    if extra_environment:
        info.update(extra_environment)
    return info


def redact_settings(settings: Settings) -> dict[str, object]:
    return asdict(settings)


def document_snapshot(document: Document, include_file_paths: bool) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "name": document.name,
        "modified": document.modified,
        "encoding": document.encoding,
        "line_ending": document.line_ending,
        "source_metadata": document.source_metadata,
    }
    if document.path is None:
        snapshot["path"] = None
    elif include_file_paths:
        snapshot["path"] = str(document.path)
    else:
        snapshot["path_hash"] = hashlib.sha256(str(document.path).encode("utf-8")).hexdigest()
    return snapshot


def _write_recent_logs(archive: zipfile.ZipFile) -> None:
    logs_dir = app_data_dir() / "logs"
    if not logs_dir.exists():
        return
    cutoff = datetime.now(UTC) - timedelta(days=7)
    for log_file in sorted(logs_dir.glob("*.log")):
        try:
            modified = datetime.fromtimestamp(log_file.stat().st_mtime, UTC)
        except OSError:
            continue
        if modified < cutoff:
            continue
        archive.write(log_file, arcname=f"logs/{log_file.name}")


def _safe_import_version() -> str:
    try:
        from quill import __version__

        return __version__
    except Exception:  # noqa: BLE001
        return "unknown"
