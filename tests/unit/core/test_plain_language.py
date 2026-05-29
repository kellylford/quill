from quill.core.plain_language import lint_plain_language


def test_lint_plain_language_finds_controlled_vocabulary_terms() -> None:
    text = "We will utilize this path in order to commence processing."
    issues = lint_plain_language(text)
    assert [issue.suggestion for issue in issues] == ["use", "to", "start"]


def test_lint_plain_language_reports_line_and_column() -> None:
    text = "Line one.\nPlease leverage this."
    issues = lint_plain_language(text)
    leverage_issue = next(issue for issue in issues if issue.suggestion == "use")
    assert leverage_issue.line == 2
    assert leverage_issue.column == 8
