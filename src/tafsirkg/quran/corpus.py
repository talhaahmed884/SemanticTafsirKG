"""The canonical Qur'an text, used to tell full-verse quotations from fragments."""

from __future__ import annotations

from enum import Enum
from importlib import resources
from pathlib import Path

from tafsirkg.arabic import quran_match_key

_BUNDLED_TEXT = "quran-uthmani.txt"


class Match(Enum):
    """How a quoted text relates to the canonical text of a verse."""

    WHOLE_VERSE = "whole-verse"
    PART_OF_VERSE = "part-of-verse"
    NOT_FOUND = "not-found"


class QuranCorpus:
    """Verse texts keyed by ``(surah, verse)``.

    The source file has one verse per line in the form ``surah|verse|text``.
    """

    def __init__(self, verses: dict[tuple[int, int], str]) -> None:
        self._verses = verses
        self._keys = {location: quran_match_key(text) for location, text in verses.items()}

    @classmethod
    def from_file(cls, path: Path) -> QuranCorpus:
        return cls._parse(path.read_text(encoding="utf-8-sig"))

    @classmethod
    def bundled(cls) -> QuranCorpus:
        """The Uthmani text shipped with the package."""
        text = resources.files("tafsirkg.resources").joinpath(_BUNDLED_TEXT).read_text("utf-8-sig")
        return cls._parse(text)

    @classmethod
    def _parse(cls, text: str) -> QuranCorpus:
        verses: dict[tuple[int, int], str] = {}
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) != 3:
                raise ValueError(f"line {line_number}: expected 'surah|verse|text', got {line!r}")
            verses[(int(parts[0]), int(parts[1]))] = parts[2].strip()
        return cls(verses)

    def __contains__(self, location: tuple[int, int]) -> bool:
        return location in self._verses

    def text(self, surah: int, verse: int) -> str:
        return self._verses[(surah, verse)]

    def match(self, quoted: str, verses: list[tuple[int, int]]) -> Match:
        """Compare ``quoted`` with the concatenated text of ``verses`` (all must exist)."""
        quoted_key = quran_match_key(quoted)
        verse_key = "".join(self._keys[location] for location in verses)
        if not quoted_key:
            return Match.NOT_FOUND
        if quoted_key == verse_key:
            return Match.WHOLE_VERSE
        if quoted_key in verse_key:
            return Match.PART_OF_VERSE
        return Match.NOT_FOUND
