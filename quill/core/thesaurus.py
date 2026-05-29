"""Thesaurus support backed by the LibreOffice MyThes en_US data file.

The data file lives at ``quill/data/th_en_US_v2.dat`` and uses this format:

    UTF-8
    word|N            (N meanings follow)
    (pos)|syn1|syn2|...
    (pos)|syn1|syn2|...
    next-word|N
    ...

The parser is lazy: the first lookup builds an in-memory dict keyed by
lowercase headword. The .dat is ~18 MB, so the dict is a few tens of MB at
most and load time is well under a second on a modern machine.

If the data file is missing, all lookups return an empty result and
``is_available()`` returns ``False`` so the UI can surface a friendly
"data not installed" dialog.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "th_en_US_v2.dat"

_LOAD_LOCK = threading.Lock()
_INDEX: dict[str, list[Meaning]] | None = None
_LOAD_ERROR: str | None = None


@dataclass(frozen=True, slots=True)
class Meaning:
    """One sense of a word, with its part of speech and synonyms."""

    part_of_speech: str  # e.g. "noun", "verb", "adj", "adv"
    synonyms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ThesaurusEntry:
    word: str
    meanings: tuple[Meaning, ...]

    @property
    def all_synonyms(self) -> tuple[str, ...]:
        seen: set[str] = set()
        ordered: list[str] = []
        for meaning in self.meanings:
            for syn in meaning.synonyms:
                key = syn.lower()
                if key in seen:
                    continue
                seen.add(key)
                ordered.append(syn)
        return tuple(ordered)


def is_available() -> bool:
    """Return True when the thesaurus data file is present on disk."""
    return _DATA_PATH.is_file()


def data_path() -> Path:
    """Return the absolute path to the expected data file (may not exist)."""
    return _DATA_PATH


def load_error() -> str | None:
    """Return the parse error message from the last load attempt, if any."""
    return _LOAD_ERROR


def _ensure_loaded() -> dict[str, list[Meaning]]:
    global _INDEX, _LOAD_ERROR
    if _INDEX is not None:
        return _INDEX
    with _LOAD_LOCK:
        if _INDEX is not None:
            return _INDEX
        if not _DATA_PATH.is_file():
            _INDEX = {}
            _LOAD_ERROR = f"Thesaurus data file not found at {_DATA_PATH}"
            return _INDEX
        try:
            text = _DATA_PATH.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            _INDEX = {}
            _LOAD_ERROR = f"Could not read thesaurus data: {error}"
            return _INDEX
        try:
            _INDEX = _parse_mythes(text)
            _LOAD_ERROR = None
        except Exception as error:  # pragma: no cover - data should be valid
            _INDEX = {}
            _LOAD_ERROR = f"Thesaurus data parse error: {error}"
        return _INDEX


def _parse_mythes(text: str) -> dict[str, list[Meaning]]:
    index: dict[str, list[Meaning]] = {}
    lines = text.splitlines()
    # First line is the encoding declaration ("UTF-8"); skip it.
    cursor = 1 if lines and lines[0].strip().lower() == "utf-8" else 0
    while cursor < len(lines):
        header = lines[cursor].strip()
        cursor += 1
        if not header or "|" not in header:
            continue
        word_part, _, count_part = header.partition("|")
        word = word_part.strip().lower()
        try:
            meaning_count = int(count_part.strip())
        except ValueError:
            continue
        meanings: list[Meaning] = []
        for _ in range(meaning_count):
            if cursor >= len(lines):
                break
            sense_line = lines[cursor].rstrip()
            cursor += 1
            parts = sense_line.split("|")
            if not parts:
                continue
            raw_pos = parts[0].strip()
            # Strip surrounding parens if present: "(noun)" -> "noun".
            if raw_pos.startswith("(") and raw_pos.endswith(")"):
                raw_pos = raw_pos[1:-1].strip()
            synonyms = tuple(_clean_synonym(syn) for syn in parts[1:] if _clean_synonym(syn))
            if synonyms:
                meanings.append(Meaning(part_of_speech=raw_pos or "", synonyms=synonyms))
        if word and meanings:
            # A headword may appear more than once across senses; merge.
            existing = index.get(word)
            if existing is None:
                index[word] = meanings
            else:
                existing.extend(meanings)
    return index


def _clean_synonym(raw: str) -> str:
    """Trim MyThes annotations like '(generic term)' and '(antonym)'.

    MyThes synonyms can include parenthetical hints after the term itself,
    e.g. ``"capital (generic term)"``. We keep the leading term and drop
    the trailing annotation so the suggestion list reads cleanly.
    """
    text = raw.strip()
    if not text:
        return ""
    if "(" in text:
        head, _, _ = text.partition("(")
        head = head.strip()
        if head:
            return head
    return text


def lookup(word: str) -> ThesaurusEntry | None:
    """Return the thesaurus entry for *word*, or ``None`` if not found."""
    if not word or not word.strip():
        return None
    cleaned = word.strip().lower()
    index = _ensure_loaded()
    meanings = index.get(cleaned)
    if meanings is None:
        # Try a naive singularisation for plural lookups (cats -> cat).
        if cleaned.endswith("s") and len(cleaned) > 3:
            meanings = index.get(cleaned[:-1])
        if meanings is None:
            return None
    return ThesaurusEntry(word=cleaned, meanings=tuple(meanings))


def word_at(text: str, position: int) -> tuple[str, int, int] | None:
    """Return ``(word, start, end)`` for the word under *position* in *text*.

    Returns ``None`` if the position isn't inside an alphabetic word. Used by
    the UI to look up the word at the caret without requiring a selection.
    """
    if not text or position < 0 or position > len(text):
        return None
    if position == len(text) and position > 0:
        position -= 1
    if not _is_word_char(text[position]):
        # Try the character just before the caret (typical when caret sits
        # immediately after a word).
        if position > 0 and _is_word_char(text[position - 1]):
            position -= 1
        else:
            return None
    start = position
    while start > 0 and _is_word_char(text[start - 1]):
        start -= 1
    end = position
    while end < len(text) and _is_word_char(text[end]):
        end += 1
    if start == end:
        return None
    return text[start:end], start, end


def _is_word_char(char: str) -> bool:
    return char.isalpha() or char == "'"
