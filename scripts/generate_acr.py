from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from quill.core.acr import ACRMetadata, render_acr_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an ACR/VPAT markdown template.")
    parser.add_argument("--product", default="Quill")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--date", default=str(date.today()))
    parser.add_argument("--contact", default="accessibility@quill.local")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs") / "accessibility" / "acr-vpat.md",
    )
    args = parser.parse_args()

    metadata = ACRMetadata(
        product_name=args.product,
        product_version=args.version,
        report_date=args.date,
        contact=args.contact,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_acr_markdown(metadata), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
