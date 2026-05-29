from pathlib import Path

from quill.core.document import Document


def test_document_name_defaults_to_untitled() -> None:
    document = Document()
    assert document.name == "Untitled"


def test_document_name_uses_file_name() -> None:
    document = Document(path=Path("C:\\tmp\\story.md"))
    assert document.name == "story.md"


def test_set_text_marks_document_modified_and_increments_revision() -> None:
    document = Document(text="one")
    document.set_text("two")
    assert document.modified is True
    assert document.revision == 1


def test_mark_saved_updates_path_and_clears_modified() -> None:
    document = Document(text="x", modified=True)
    path = Path("C:\\tmp\\doc.txt")
    document.mark_saved(path)
    assert document.path == path
    assert document.modified is False
