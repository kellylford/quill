"""Generate an app_updater-compatible JSON feed for Quill incremental updates.

This script maps Quill release artifacts to the autoupdate library format,
enabling cross-platform micro-updates and delta installations.

Upstream: AccessibleApps/app_updater (https://github.com/accessibleapps/app_updater)
License: MIT

Usage:
  python scripts/generate_app_updater_feed.py \\
    --version "1.0.0" \\
    --windows-url "https://releases.example.com/quill-1.0.0-windows.zip" \\
    --macos-url "https://releases.example.com/quill-1.0.0-macos.zip" \\
    --linux-url "https://releases.example.com/quill-1.0.0-linux.zip" \\
    --description "Bug fixes and performance improvements" \\
    --output docs/site/updates/.quill-app-updater-v1.json
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate an app_updater-compatible Quill update feed."
    )
    parser.add_argument("--version", required=True, help="Release version (e.g., 1.0.0)")
    parser.add_argument("--windows-url", required=True, help="Windows update ZIP URL")
    parser.add_argument("--macos-url", required=True, help="macOS update ZIP URL")
    parser.add_argument("--linux-url", required=True, help="Linux update ZIP URL")
    parser.add_argument(
        "--description",
        default="",
        help="Short release description for update prompt",
    )
    parser.add_argument(
        "--published-at",
        default=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        help="ISO-8601 release time (UTC)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs") / "site" / "updates" / ".quill-app-updater-v1.json",
        help="Target feed file path",
    )
    args = parser.parse_args()

    payload = {
        "current_version": args.version.strip(),
        "description": args.description.strip(),
        "published_at": args.published_at.strip(),
        "downloads": {
            "Windows": args.windows_url.strip(),
            "Darwin": args.macos_url.strip(),
            "Linux": args.linux_url.strip(),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote app_updater feed to {args.output}")
    print("Format: app_updater v1 (autoupdate library compatible)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
