from __future__ import annotations

from pathlib import Path

from scripts.verify_release_corpus import verify_release_corpus


def test_verify_release_corpus_passes(tmp_path: Path) -> None:
    corpus = tmp_path / "release"
    corpus.mkdir()
    (corpus / "plain.txt").write_text(
        "Quill release corpus plain text.\nSecond line.\n", encoding="utf-8"
    )
    (corpus / "note.md").write_text(
        "# Quill release corpus\n\n- item one\n- item two\n", encoding="utf-8"
    )
    (corpus / "manifest.json").write_text(
        """
        {
          "files": [
            {"path": "plain.txt", "text": "Quill release corpus plain text.\\nSecond line.\\n"},
            {"path": "note.md", "text": "# Quill release corpus\\n\\n- item one\\n- item two\\n"}
          ]
        }
        """.strip(),
        encoding="utf-8",
    )

    verify_release_corpus(corpus / "manifest.json")
