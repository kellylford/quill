from __future__ import annotations

from quill.core.a11y_regions import (
    RegionTracker,
    build_accessibility_audit_report,
    render_snapshot,
)


def test_region_tracker_records_tab_order_without_duplicates() -> None:
    tracker = RegionTracker()
    tracker.enter("Editor")
    tracker.enter("Editor")
    tracker.enter("Find")
    tracker.exit("Find")
    snapshot = tracker.snapshot()
    assert snapshot.tab_order == ("Editor", "Find")
    assert snapshot.active_regions == ("Editor", "Editor")
    assert snapshot.has_keyboard_trap is True


def test_region_tracker_reports_exit_mismatch_anomaly() -> None:
    tracker = RegionTracker()
    tracker.enter("Editor")
    tracker.enter("Open")
    tracker.exit("Find")
    snapshot = tracker.snapshot()
    assert "Exited Find while Open was active" in snapshot.anomalies
    assert snapshot.active_regions == ("Editor", "Open")


def test_render_snapshot_includes_trap_status() -> None:
    tracker = RegionTracker()
    tracker.enter("Editor")
    tracker.enter("Open")
    snapshot = tracker.snapshot()
    rendered = render_snapshot(snapshot)
    assert "Potential keyboard trap: yes" in rendered
    assert "1. Editor" in rendered


def test_build_accessibility_audit_report_contains_core_metrics() -> None:
    tracker = RegionTracker()
    tracker.enter("Editor")
    tracker.enter("Open")
    report = build_accessibility_audit_report(tracker.snapshot(), "NVDA")
    assert "Screen reader detected: NVDA" in report
    assert "Keyboard trap status: potential trap detected" in report
    assert "Tab-order transition count: 2" in report


def test_region_labels_are_normalized_for_audit_output() -> None:
    tracker = RegionTracker()
    tracker.enter("Read Aloud\nVoice")
    tracker.enter(" Spell   Check ")
    report = build_accessibility_audit_report(tracker.snapshot(), "JAWS")
    assert "Recent regions: Read Aloud Voice -> Spell Check" in report
