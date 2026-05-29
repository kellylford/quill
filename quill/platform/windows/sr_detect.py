from __future__ import annotations

import csv
import io
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScreenReaderDetection:
    detected: bool
    name: str
    source: str


_KNOWN_SCREEN_READERS = {
    "nvda.exe": "NVDA",
    "narrator.exe": "Narrator",
    "jfw.exe": "JAWS",
}


def detect_screen_reader(process_snapshot: str | None = None) -> ScreenReaderDetection:
    rows = _parse_tasklist_csv(process_snapshot or _tasklist_snapshot())
    for image_name in rows:
        lowered = image_name.lower()
        if lowered in _KNOWN_SCREEN_READERS:
            return ScreenReaderDetection(
                detected=True,
                name=_KNOWN_SCREEN_READERS[lowered],
                source=image_name,
            )
    return ScreenReaderDetection(detected=False, name="none", source="")


def _tasklist_snapshot() -> str:
    try:
        completed = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return ""
    return completed.stdout


def _parse_tasklist_csv(text: str) -> list[str]:
    rows: list[str] = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if not row:
            continue
        rows.append(row[0].strip())
    return rows
