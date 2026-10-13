"""Shared fixtures: build small TEI documents from snippets and run them through the mapper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from tafsirkg.domain.model import TafsirChapter
from tafsirkg.issues import IssueCode, IssueLog, Severity
from tafsirkg.mapping.document import TafsirMapper
from tafsirkg.mapping.quran_quotes import QuranQuoteResolver
from tafsirkg.mapping.registry import EntityRegistry
from tafsirkg.quran.corpus import QuranCorpus
from tafsirkg.tei.reader import TeiReader

from snippets import TEI_TEMPLATE


@pytest.fixture(scope="session")
def corpus() -> QuranCorpus:
    return QuranCorpus.bundled()


@pytest.fixture
def tei_file(tmp_path: Path):
    """Write a TEI document whose <body> is ``body`` and return its path."""

    def make(body: str, name: str = "test.xml") -> Path:
        path = tmp_path / name
        path.write_text(TEI_TEMPLATE.format(body=body), encoding="utf-8")
        return path

    return make


@dataclass
class Mapped:
    chapters: list[TafsirChapter]
    registry: EntityRegistry
    issues: IssueLog

    def codes(self, severity: Severity | None = None) -> list[IssueCode]:
        return [i.code for i in self.issues if severity is None or i.severity == severity]


@pytest.fixture
def map_bodies(tei_file, corpus):
    """Map one or more TEI bodies (as separate files) and return chapters, registry and issues."""

    def run(*bodies: str) -> Mapped:
        issues = IssueLog()
        registry = EntityRegistry()
        mapper = TafsirMapper(registry, QuranQuoteResolver(corpus, registry, issues), issues)
        reader = TeiReader(issues)
        for index, body in enumerate(bodies):
            mapper.add_document(reader.read(tei_file(body, f"file{index}.xml")))
        return Mapped(mapper.chapters, registry, issues)

    return run
