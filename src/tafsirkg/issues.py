"""Data-quality issues found while converting.

Irregular data is never fixed silently: every component that has to interpret,
skip or work around something in the XML records an :class:`Issue` in the shared
:class:`IssueLog`. The pipeline writes the log out as a CSV report next to the graph.
"""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from tafsirkg.source import SourceRef


class Severity(StrEnum):
    INFO = "info"  # an expected irregularity, handled by a documented rule
    WARNING = "warning"  # the data is probably wrong, or some information could not be modelled
    ERROR = "error"  # an element could not be converted at all


class IssueCode(StrEnum):
    """Every kind of issue the converter can report."""

    # TEI reading
    INVALID_TEI = "invalid-tei"
    UNKNOWN_ELEMENT = "unknown-element"
    UNEXPECTED_ELEMENT = "unexpected-element"
    # Document structure
    SECTION_OUTSIDE_CHAPTER = "section-outside-chapter"
    DUPLICATE_ID = "duplicate-id"
    DIVISION_WITHOUT_NUMBER = "division-without-number"
    SECTION_NUMBER_MISMATCH = "section-number-mismatch"
    UNKNOWN_PARAGRAPH_KIND = "unknown-paragraph-kind"
    EMPTY_PARAGRAPH = "empty-paragraph"
    # Annotations
    MALFORMED_ANA = "malformed-ana"
    SEGMENT_WITHOUT_THEME = "segment-without-theme"
    UNKNOWN_ENTITY_ROLE = "unknown-entity-role"
    MALFORMED_PAGE_BREAK = "malformed-page-break"
    # Hadith and isnad
    HADITH_WITHOUT_ID = "hadith-without-id"
    HADITH_WITHOUT_CHAIN = "hadith-without-chain"
    HADITH_WITHOUT_MATN = "hadith-without-matn"
    CHAIN_WITHOUT_SHAYKH = "chain-without-shaykh"
    NARRATOR_BEFORE_CHAIN = "narrator-before-chain"
    NARRATOR_WITHOUT_ID = "narrator-without-id"
    UNKNOWN_NARRATOR_ROLE = "unknown-narrator-role"
    POSSIBLE_BRANCHING_CHAIN = "possible-branching-chain"
    PERSNAME_OUTSIDE_ISNAD = "persname-outside-isnad"
    MATN_OUTSIDE_HADITH = "matn-outside-hadith"
    NOTE_NUMBER_MISMATCH = "note-number-mismatch"
    # Qur'an quotations
    QUOTE_WITHOUT_REFERENCE = "quote-without-reference"
    MALFORMED_QURAN_REFERENCE = "malformed-quran-reference"
    UNKNOWN_VERSE = "unknown-verse"
    QUOTE_TEXT_NOT_IN_VERSE = "quote-text-not-in-verse"
    UNKNOWN_QUOTE_TYPE = "unknown-quote-type"
    ORPHAN_VERSE_LINE = "orphan-verse-line"
    POETRY_WITHOUT_QUOTE = "poetry-without-quote"


@dataclass(frozen=True, slots=True)
class Issue:
    severity: Severity
    code: IssueCode
    message: str
    source: SourceRef | None = None


class IssueLog:
    """Collects issues from all components (the *Notification* pattern)."""

    def __init__(self) -> None:
        self._issues: list[Issue] = []

    def report(
        self, severity: Severity, code: IssueCode, message: str, source: SourceRef | None = None
    ) -> None:
        self._issues.append(Issue(severity, code, message, source))

    def info(self, code: IssueCode, message: str, source: SourceRef | None = None) -> None:
        self.report(Severity.INFO, code, message, source)

    def warning(self, code: IssueCode, message: str, source: SourceRef | None = None) -> None:
        self.report(Severity.WARNING, code, message, source)

    def error(self, code: IssueCode, message: str, source: SourceRef | None = None) -> None:
        self.report(Severity.ERROR, code, message, source)

    def __iter__(self) -> Iterator[Issue]:
        return iter(self._issues)

    def __len__(self) -> int:
        return len(self._issues)

    def count_by_severity(self) -> Counter[Severity]:
        return Counter(issue.severity for issue in self._issues)

    def count_by_code(self) -> Counter[tuple[Severity, IssueCode]]:
        return Counter((issue.severity, issue.code) for issue in self._issues)

    def write_csv(self, path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["severity", "code", "file", "line", "message"])
            for issue in self._issues:
                source = issue.source
                writer.writerow(
                    [
                        issue.severity,
                        issue.code,
                        source.file if source else "",
                        source.line if source and source.line is not None else "",
                        issue.message,
                    ]
                )
