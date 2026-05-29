# Quality gates

The project quality bar is enforced with these commands:

```powershell
python -m ruff check .
python -m mypy quill\core quill\io
python -m pytest -q
```

## Required checks before merge

1. Lint and import hygiene (`ruff`)
2. Type-checking in `core` and `io` (`mypy`)
3. Unit tests (`pytest`)

## Single-test invocation

```powershell
python -m pytest tests\unit\io\test_text.py::test_read_text_document -q
```

## PRD alignment intent

The CI model will expand toward PRD section 10.8 phases:

- unit, integration, a11y, and perf test partitions
- schema validation and accessibility static checks
- packaging/signing stages
