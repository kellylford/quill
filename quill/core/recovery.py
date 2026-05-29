from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic


@dataclass(frozen=True, slots=True)
class RecoveryOffer:
    session_id: str
    snapshot: Path


def begin_session(session_id: str) -> list[RecoveryOffer]:
    UUID(session_id)
    state = _load_state()
    offers: list[RecoveryOffer] = []
    previous_session = state.get("last_session_id")
    previous_clean = bool(state.get("clean_exit", True))
    if isinstance(previous_session, str) and previous_session and not previous_clean:
        latest = latest_session_snapshot(previous_session)
        if latest is not None:
            offers.append(RecoveryOffer(session_id=previous_session, snapshot=latest))
    _save_state({"last_session_id": session_id, "clean_exit": False})
    return offers


def mark_clean_exit(session_id: str) -> None:
    UUID(session_id)
    state = _load_state()
    last_session = state.get("last_session_id")
    if last_session != session_id:
        return
    _save_state({"last_session_id": session_id, "clean_exit": True})


def latest_session_snapshot(session_id: str) -> Path | None:
    UUID(session_id)
    root = app_data_dir() / "autosave" / session_id
    if not root.exists():
        return None
    snapshots = sorted(root.glob("*.snap"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not snapshots:
        return None
    return snapshots[0]


def read_recovery_snapshot(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _state_path() -> Path:
    return app_data_dir() / "recovery_state.json"


def _load_state() -> dict[str, object]:
    raw = read_json(_state_path(), default={})
    if not isinstance(raw, dict):
        return {}
    return raw


def _save_state(data: dict[str, object]) -> None:
    write_json_atomic(_state_path(), data)
