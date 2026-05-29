from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegionSnapshot:
    tab_order: tuple[str, ...]
    active_regions: tuple[str, ...]
    anomalies: tuple[str, ...]

    @property
    def has_keyboard_trap(self) -> bool:
        return bool(self.active_regions)


class RegionTracker:
    def __init__(self, max_entries: int = 32) -> None:
        self._max_entries = max_entries
        self._tab_order: list[str] = []
        self._active_regions: list[str] = []
        self._anomalies: list[str] = []

    def _normalize_region_label(self, region: str) -> str:
        cleaned = " ".join(region.replace("&", "").split())
        return cleaned or "Unknown"

    def enter(self, region: str) -> None:
        label = self._normalize_region_label(region)
        self._active_regions.append(label)
        if not self._tab_order or self._tab_order[-1] != label:
            self._tab_order.append(label)
            if len(self._tab_order) > self._max_entries:
                self._tab_order = self._tab_order[-self._max_entries :]

    def exit(self, region: str) -> None:
        label = self._normalize_region_label(region)
        if not self._active_regions:
            self._anomalies.append(f"Exited {label} with no active region")
            return
        if self._active_regions[-1] == label:
            self._active_regions.pop()
            return
        self._anomalies.append(f"Exited {label} while {self._active_regions[-1]} was active")
        if label in self._active_regions:
            self._active_regions.remove(label)

    def snapshot(self) -> RegionSnapshot:
        return RegionSnapshot(
            tab_order=tuple(self._tab_order),
            active_regions=tuple(self._active_regions),
            anomalies=tuple(self._anomalies),
        )


def render_snapshot(snapshot: RegionSnapshot) -> str:
    lines = ["Keyboard trap audit and tab-order snapshot", ""]
    if snapshot.tab_order:
        lines.append("Tab-order snapshot:")
        for index, region in enumerate(snapshot.tab_order, start=1):
            lines.append(f"{index}. {region}")
    else:
        lines.append("Tab-order snapshot: (no region transitions captured yet)")
    lines.append("")
    if snapshot.has_keyboard_trap:
        lines.append("Potential keyboard trap: yes")
        lines.append("Active region stack: " + " > ".join(snapshot.active_regions))
    else:
        lines.append("Potential keyboard trap: no")
    if snapshot.anomalies:
        lines.append("")
        lines.append("Anomalies:")
        lines.extend(f"- {item}" for item in snapshot.anomalies)
    return "\n".join(lines)


def build_accessibility_audit_report(
    snapshot: RegionSnapshot,
    screen_reader_name: str,
) -> str:
    lines = ["Accessibility audit report", ""]
    if screen_reader_name != "none":
        lines.append(f"Screen reader detected: {screen_reader_name}")
    else:
        lines.append("Screen reader detected: none")
    lines.append(
        "Keyboard trap status: potential trap detected"
        if snapshot.has_keyboard_trap
        else "Keyboard trap status: no trap detected"
    )
    lines.append(f"Tab-order transition count: {len(snapshot.tab_order)}")
    if snapshot.tab_order:
        lines.append("Recent regions: " + " -> ".join(snapshot.tab_order[-8:]))
    if snapshot.anomalies:
        lines.append(f"Anomaly count: {len(snapshot.anomalies)}")
    else:
        lines.append("Anomaly count: 0")
    return "\n".join(lines)
