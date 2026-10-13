"""Resolves ``<quote type="quran|qiraat">`` elements to verses and verse fragments.

Rules:

* ``@n`` gives the verse(s). The quoted text is compared with the canonical text: if
  it is the whole verse (or whole range) the quotation refers to the ``Verse`` itself,
  otherwise to a ``VerseFragment`` that is part of it.
* A quotation of a range with one ``<l n="..">`` per verse is resolved line by line.
* ``type="qiraat"`` is a variant reading: always a fragment, marked as ``qiraat``.
* Without ``@n`` the fragment is kept but not linked to any verse. Short quotations
  without ``@n`` are often a single word (``غَيْرِ``) that occurs in many verses, so
  guessing the verse from the text would be unreliable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tafsirkg.domain.model import QuranTarget
from tafsirkg.issues import IssueCode, IssueLog
from tafsirkg.mapping.registry import EntityRegistry
from tafsirkg.quran.corpus import Match, QuranCorpus
from tafsirkg.quran.reference import MalformedReferenceError, QuranReference
from tafsirkg.source import SourceRef
from tafsirkg.tei import model as tei
from tafsirkg.tei.text import plain_text

QIRAAT = "qiraat"


@dataclass
class QuoteResolution:
    """What a quotation refers to, overall and (for per-verse lines) line by line."""

    targets: list[QuranTarget] = field(default_factory=list)
    _by_line: dict[int, list[QuranTarget]] = field(default_factory=dict)

    def targets_for_line(self, line: tei.Line) -> list[QuranTarget] | None:
        return self._by_line.get(id(line))

    def add(self, targets: list[QuranTarget], line: tei.Line | None = None) -> None:
        if line is not None:
            self._by_line[id(line)] = targets
        for target in targets:
            if target not in self.targets:
                self.targets.append(target)


class QuranQuoteResolver:
    def __init__(self, corpus: QuranCorpus, registry: EntityRegistry, issues: IssueLog) -> None:
        self._corpus = corpus
        self._registry = registry
        self._issues = issues

    def resolve(self, quote: tei.Quote) -> QuoteResolution:
        resolution = QuoteResolution()
        text = plain_text(quote)
        reading = QIRAAT if quote.type == QIRAAT else None
        reference = self._reference(quote)
        if reference is None:
            resolution.add([self._registry.verse_fragment(text, [], reading, quote.subtype)])
            return resolution

        lines = [node for node in quote.descendants() if isinstance(node, tei.Line) and node.n is not None]
        if reference.is_range and lines:
            for line in lines:
                verse_number = self._line_verse(line, reference)
                if verse_number is not None:
                    targets = self._classify(
                        reference.surah, [verse_number], plain_text(line), reading, quote.subtype, line.source
                    )
                    resolution.add(targets, line)
            if resolution.targets:
                return resolution

        resolution.add(
            self._classify(
                reference.surah, list(reference.verse_numbers), text, reading, quote.subtype, quote.source
            )
        )
        return resolution

    def _reference(self, quote: tei.Quote) -> QuranReference | None:
        if quote.n is None:
            self._issues.info(
                IssueCode.QUOTE_WITHOUT_REFERENCE,
                f"{quote.type} quotation without @n kept as an unlinked fragment: {plain_text(quote)!r}",
                quote.source,
            )
            return None
        try:
            reference = QuranReference.parse(quote.n)
        except MalformedReferenceError as exc:
            self._issues.warning(IssueCode.MALFORMED_QURAN_REFERENCE, str(exc), quote.source)
            return None
        missing = [
            number for number in reference.verse_numbers if (reference.surah, number) not in self._corpus
        ]
        if missing:
            self._issues.error(
                IssueCode.UNKNOWN_VERSE,
                f"@n={quote.n!r} refers to verse(s) {missing} that do not exist in surah {reference.surah}",
                quote.source,
            )
            return None
        return reference

    def _line_verse(self, line: tei.Line, reference: QuranReference) -> int | None:
        if line.n is not None and line.n.strip().isdigit():
            number = int(line.n)
            if number in reference.verse_numbers:
                return number
        self._issues.warning(
            IssueCode.MALFORMED_QURAN_REFERENCE,
            f"<l n={line.n!r}> is not a verse of the quotation's range {reference}",
            line.source,
        )
        return None

    def _classify(
        self,
        surah: int,
        verse_numbers: list[int],
        text: str,
        reading: str | None,
        subtype: str | None,
        source: SourceRef,
    ) -> list[QuranTarget]:
        verses = [
            self._registry.verse(surah, number, self._corpus.text(surah, number)) for number in verse_numbers
        ]
        match = self._corpus.match(text, [(surah, number) for number in verse_numbers])
        if match is Match.WHOLE_VERSE and reading is None:
            return list(verses)
        if match is Match.NOT_FOUND:
            location = f"{surah}:{verse_numbers[0]}" + (
                f"-{verse_numbers[-1]}" if len(verse_numbers) > 1 else ""
            )
            if reading is None:
                self._issues.warning(
                    IssueCode.QUOTE_TEXT_NOT_IN_VERSE,
                    f"quoted text {text!r} not found in the canonical text of {location}",
                    source,
                )
            else:
                self._issues.info(
                    IssueCode.QUOTE_TEXT_NOT_IN_VERSE,
                    f"variant reading {text!r} differs from the canonical text of {location}",
                    source,
                )
        return [self._registry.verse_fragment(text, verses, reading, subtype)]
