"""Wires the layers together: a folder of TEI files in, a graph and an issue log out."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph

from tafsirkg.domain.model import Division, Hadith, TafsirChapter
from tafsirkg.issues import IssueLog, Severity
from tafsirkg.mapping.document import TafsirMapper
from tafsirkg.mapping.quran_quotes import QuranQuoteResolver
from tafsirkg.mapping.registry import EntityRegistry
from tafsirkg.quran.corpus import QuranCorpus
from tafsirkg.rdf.iris import DEFAULT_BASE_IRI, IriFactory
from tafsirkg.rdf.writer import GraphWriter
from tafsirkg.tei.model import TeiDocument
from tafsirkg.tei.reader import TeiFormatError, TeiReader


def tei_files(folder: Path) -> list[Path]:
    """The ``*.xml`` files of a surah folder in reading order (``.xpr`` and ``.bak`` are skipped)."""

    def natural_key(path: Path) -> list[int | str]:
        return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name)]

    return sorted(folder.glob("*.xml"), key=natural_key)


def read_documents(folder: Path, issues: IssueLog) -> list[TeiDocument]:
    """Reads every TEI file of ``folder``; unreadable files are reported and skipped."""
    reader = TeiReader(issues)
    documents = []
    for path in tei_files(folder):
        try:
            documents.append(reader.read(path, display_name=f"{folder.name}/{path.name}"))
        except TeiFormatError:
            continue  # already recorded in the issue log
    return documents


@dataclass
class BuildResult:
    name: str
    documents: list[TeiDocument]
    chapters: list[TafsirChapter]
    registry: EntityRegistry
    graph: Graph
    issues: IssueLog

    def summary(self) -> str:
        divisions = [division for chapter in self.chapters for division in _walk(chapter)]
        paragraphs = [paragraph for division in divisions for paragraph in division.paragraphs]
        hadiths = [paragraph for paragraph in paragraphs if isinstance(paragraph, Hadith)]
        severities = self.issues.count_by_severity()
        rows = [
            ("files read", len(self.documents)),
            ("chapters", len(self.chapters)),
            ("sections and subsections", len(divisions) - len(self.chapters)),
            ("commentary paragraphs", len(paragraphs) - len(hadiths)),
            ("hadith paragraphs", len(hadiths)),
            ("narrator chains", sum(len(hadith.chains) for hadith in hadiths)),
            ("narrators", len(self.registry.narrators)),
            ("named entities", len(self.registry.named_entities)),
            ("themes", len(self.registry.themes)),
            ("verses", len(self.registry.verses)),
            ("verse fragments", len(self.registry.verse_fragments)),
            ("triples", len(self.graph)),
            *((f"issues ({severity})", severities[severity]) for severity in Severity),
        ]
        width = max(len(label) for label, _ in rows)
        return "\n".join(f"{label:<{width}}  {value}" for label, value in rows)


def _walk(division: Division) -> list[Division]:
    result = [division]
    for subdivision in division.subdivisions:
        result.extend(_walk(subdivision))
    return result


class KnowledgeGraphBuilder:
    """Facade over the conversion: read TEI, map to the domain model, write RDF."""

    def __init__(self, corpus: QuranCorpus | None = None, base_iri: str = DEFAULT_BASE_IRI) -> None:
        self._corpus = corpus or QuranCorpus.bundled()
        self._iris = IriFactory(base_iri)

    def build(self, folder: Path) -> BuildResult:
        issues = IssueLog()
        registry = EntityRegistry()
        mapper = TafsirMapper(registry, QuranQuoteResolver(self._corpus, registry, issues), issues)
        documents = read_documents(folder, issues)
        for document in documents:
            mapper.add_document(document)
        graph = GraphWriter(self._iris).write(mapper.chapters, registry)
        return BuildResult(folder.name, documents, mapper.chapters, registry, graph, issues)


def write_outputs(result: BuildResult, output_dir: Path) -> tuple[Path, Path]:
    """Writes ``<name>.ttl`` and ``<name>.issues.csv`` into ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    graph_path = output_dir / f"{result.name}.ttl"
    issues_path = output_dir / f"{result.name}.issues.csv"
    result.graph.serialize(destination=graph_path, format="turtle", encoding="utf-8")
    result.issues.write_csv(issues_path)
    return graph_path, issues_path
