from __future__ import annotations

import json
import os
from pathlib import Path

from quill.core.paths import app_data_dir


def try_claim_primary_instance() -> bool:
    lock_path = _lock_file_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        pid = _read_pid(lock_path)
        if pid is not None and _pid_is_running(pid):
            return False
        lock_path.unlink(missing_ok=True)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    return True


def release_primary_instance() -> None:
    lock_path = _lock_file_path()
    pid = _read_pid(lock_path)
    if pid == os.getpid():
        lock_path.unlink(missing_ok=True)


def enqueue_open_request(path: Path) -> None:
    queue_path = _queue_file_path()
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8", newline="\n") as handle:
        payload = {"path": str(path)}
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def drain_open_requests() -> list[Path]:
    queue_path = _queue_file_path()
    if not queue_path.exists():
        return []
    lines = queue_path.read_text(encoding="utf-8").splitlines()
    queue_path.unlink(missing_ok=True)
    requests: list[Path] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(raw, dict) and isinstance(raw.get("path"), str):
            requests.append(Path(raw["path"]))
    return requests


def _lock_file_path() -> Path:
    return app_data_dir() / "ipc" / "instance.lock"


def _queue_file_path() -> Path:
    return app_data_dir() / "ipc" / "open-requests.jsonl"


def _read_pid(lock_path: Path) -> int | None:
    if not lock_path.exists():
        return None
    raw = lock_path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        process_query_limited_information = 0x1000
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True
