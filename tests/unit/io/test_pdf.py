from __future__ import annotations

from pathlib import Path

from quill.io.pdf import PdfExtractionResult, _score_pdf_text, format_pdf_document


def test_score_pdf_text_rewards_real_extraction() -> None:
    assert _score_pdf_text("Hello world" * 20, 2, 2) > _score_pdf_text("", 2, 0)


def test_format_pdf_document_uses_extraction_metadata(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(
        "quill.io.pdf.extract_pdf_text",
        lambda _path: PdfExtractionResult(
            text="Extracted PDF text\n",
            quality_score=72,
            engine="pypdf",
            page_count=1,
            extracted_pages=1,
            page_scores=[72],
        ),
    )

    formatted = format_pdf_document(pdf_path)

    assert "Engine: pypdf" in formatted
    assert "Quality score: 72/100" in formatted
    assert "Extracted PDF text" in formatted
