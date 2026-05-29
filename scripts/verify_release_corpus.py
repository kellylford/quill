from __future__ import annotations

import argparse
import json
from pathlib import Path

from quill.io.text import read_text_document


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Quill release corpus.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("tests") / "corpus" / "release" / "manifest.json",
    )
    args = parser.parse_args()
    verify_release_corpus(args.manifest)
    print(f"Verified release corpus: {args.manifest}")
    return 0


def verify_release_corpus(manifest_path: Path) -> None:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = payload.get("files", [])
    if not isinstance(entries, list):
        raise ValueError("Release corpus manifest is invalid.")

    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("Release corpus manifest is invalid.")
        relative_path = item.get("path")
        expected_text = item.get("text")
        if not isinstance(relative_path, str) or not isinstance(expected_text, str):
            raise ValueError("Release corpus manifest is invalid.")
        source = (manifest_path.parent / relative_path).resolve()
        document = read_text_document(source)
        if document.text != expected_text:
            raise AssertionError(f"Corpus mismatch for {relative_path}")


if __name__ == "__main__":
    raise SystemExit(main())
