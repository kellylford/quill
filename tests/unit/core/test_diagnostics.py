from __future__ import annotations

import json
import zipfile
from pathlib import Path

from quill.core.diagnostics import (
    build_bug_report_payload,
    load_diagnostic_events,
    record_diagnostic_event,
    write_diagnostics_bundle,
)
from quill.core.document import Document
from quill.core.notifications import Notification
from quill.core.settings import Settings


def test_record_diagnostic_event_round_trips(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))

    record_diagnostic_event("command", "tools.pandoc_wizard")
    events = load_diagnostic_events()

    assert events[-1].kind == "command"
    assert events[-1].name == "tools.pandoc_wizard"


def test_write_diagnostics_bundle_writes_expected_members(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path / "data"))
    target = tmp_path / "quill-diagnostics.zip"
    document = Document(text="hello", path=Path("C:/Docs/sample.md"), modified=False)

    write_diagnostics_bundle(
        target,
        settings=Settings(),
        keymap={"file.open": "Ctrl+O"},
        notifications=[
            Notification(
                timestamp="2026-05-29T00:00:00+00:00",
                category="info",
                message="Ready",
            )
        ],
        current_document=document,
        include_file_paths=False,
        extra_environment={"screen_reader": "NVDA"},
    )

    with zipfile.ZipFile(target) as archive:
        names = set(archive.namelist())
        assert "metadata.json" in names
        assert "recent-actions.json" in names
        assert "settings-redacted.json" in names
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["screen_reader"] == "NVDA"
        assert metadata["current_document"]["path_hash"]


def test_build_bug_report_payload_mentions_diagnostics() -> None:
    payload = build_bug_report_payload(current_document=Document(text="x"))

    assert "Bug report:" in payload["summary"]
    assert "Save Diagnostics" in payload["body"]