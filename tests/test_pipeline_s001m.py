"""End-to-end checks on the real data of Surah al-Fatiha (``Dataset/S001M``)."""

from pathlib import Path

import pytest
from rdflib import RDF, RDFS

from tafsirkg.domain.model import Commentary, Hadith
from tafsirkg.issues import Severity
from tafsirkg.pipeline import KnowledgeGraphBuilder, tei_files, write_outputs
from tafsirkg.rdf.vocabulary import HADITH, ST

S001M = Path(__file__).resolve().parents[1] / "Dataset" / "S001M"

pytestmark = pytest.mark.skipif(not S001M.is_dir(), reason="dataset not available")


@pytest.fixture(scope="module")
def result(corpus):
    return KnowledgeGraphBuilder(corpus).build(S001M)


def test_only_xml_files_are_read_in_section_order():
    assert [path.name for path in tei_files(S001M)] == [
        "sure_1_section_0.11-0.16.xml",
        "sure_1_section_1.1-1.14.xml",
    ]


def test_counts_match_the_xml(result):
    (chapter,) = result.chapters
    sections = chapter.subdivisions
    paragraphs = [paragraph for section in sections for paragraph in section.paragraphs]
    assert len(sections) == 20
    assert sum(isinstance(p, Commentary) for p in paragraphs) == 166
    assert sum(isinstance(p, Hadith) for p in paragraphs) == 83
    assert sum(1 for p in paragraphs if isinstance(p, Hadith) and p.number is not None) == 81


def test_no_errors(result):
    assert result.issues.count_by_severity()[Severity.ERROR] == 0


def test_graph_invariants(result):
    graph = result.graph
    for chain in graph.subjects(RDF.type, HADITH.NarratorChain):
        assert len(list(graph.objects(chain, HADITH.hasRootNarratorSegment))) == 1
        assert len(list(graph.objects(chain, ST.isPartOfHadith))) == 1
    for verse in graph.subjects(RDF.type, ST.Verse):
        assert graph.value(verse, ST.hasText) is not None
    for hadith in graph.subjects(RDF.type, HADITH.Hadith):
        assert (hadith, RDF.type, ST.Commentary) not in graph


def test_every_node_has_one_label(result):
    graph = result.graph
    for node in set(graph.subjects(RDF.type, None)):
        assert len(list(graph.objects(node, RDFS.label))) == 1, node


def test_rebuilding_gives_identical_triples(result, corpus):
    assert set(KnowledgeGraphBuilder(corpus).build(S001M).graph) == set(result.graph)


def test_outputs_are_written(result, tmp_path):
    graph_path, issues_path = write_outputs(result, tmp_path)
    assert graph_path.name == "S001M.ttl" and graph_path.stat().st_size > 0
    assert issues_path.read_text(encoding="utf-8").startswith("severity,code,file,line,message")
