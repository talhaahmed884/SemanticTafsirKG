from rdflib import RDF, Literal, URIRef

from tafsirkg.domain.model import NarratorRole
from tafsirkg.rdf.iris import IriFactory
from tafsirkg.rdf.vocabulary import HADITH, NARRATOR_TYPE_IRIS, ST
from tafsirkg.rdf.writer import GraphWriter

from snippets import section_body

BASE = "http://example.org/r/"
IRI = IriFactory(BASE)

BODY = section_body(
    '<p n="nothadith" ana="lugha">قال <name role="location">مكة</name></p>'
    '<p n="hadith" xml:id="h9" ana="kalam"><note> 9 /1 </note><persName ana="shaykh" n="L1">أ</persName>'
    ' عن <persName ana="sahabi" n="L2">ب</persName> : <said>'
    '<quote type="quran" n="1:2">الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ</quote></said></p>',
    head='<quote type="quran" n="1:2">الْحَمْدُ لِلَّهِ</quote>',
)


def _graph(mapped):
    return GraphWriter(IRI).write(mapped.chapters, mapped.registry)


def test_structure_triples(map_bodies):
    graph = _graph(map_bodies(BODY))
    chapter, section = IRI("chapter/1"), IRI("section/1.1")
    commentary, hadith = IRI("commentary/1.1/1"), IRI("hadith/9")
    assert (chapter, RDF.type, ST.TafsirChapter) in graph
    assert (chapter, ST.containsSection, section) in graph
    assert (chapter, ST.refersTo, IRI("quran/surah/1")) in graph
    assert (section, ST.containsCommentary, commentary) in graph
    # Hadith is disjoint with Commentary, so it is linked with the generic hasPart.
    assert (section, ST.hasPart, hadith) in graph
    assert (section, ST.containsCommentary, hadith) not in graph
    assert (hadith, HADITH.follows, commentary) in graph
    assert (section, ST.isAbout, None) in graph
    assert (commentary, ST.hasTheme, IRI("theme/lugha")) in graph
    assert (commentary, ST.mentions, None) in graph
    assert (hadith, ST.hasHadithNo, Literal(9)) in graph
    assert (hadith, ST.hasNote, IRI("hadith/9/note/1")) in graph


def test_chain_triples(map_bodies):
    graph = _graph(map_bodies(BODY))
    hadith, chain = IRI("hadith/9"), IRI("hadith/9/chain/1")
    first, root = IRI("hadith/9/chain/1/link/1"), IRI("hadith/9/chain/1/link/2")
    shaykh, sahabi = IRI("narrator/L1"), IRI("narrator/L2")
    assert (hadith, HADITH.hasNarratorChain, chain) in graph
    assert (chain, HADITH.hasNarratorSegment, root) in graph
    assert (chain, HADITH.hasRootNarratorSegment, root) in graph
    assert (root, RDF.type, HADITH.RootNarratorChainSegment) in graph
    assert (first, HADITH.precedes, root) in graph
    assert (first, HADITH.refersToNarrator, shaykh) in graph
    assert (shaykh, HADITH.heardFrom, sahabi) in graph
    assert (hadith, HADITH.hasRootNarrator, sahabi) in graph
    assert (sahabi, RDF.type, HADITH.RootNarrator) in graph
    assert (sahabi, ST.hasNarratorType, NARRATOR_TYPE_IRIS[NarratorRole.SAHABI]) in graph
    assert (sahabi, ST.hasID, Literal("L2")) in graph


def test_matn_and_quran_triples(map_bodies):
    graph = _graph(map_bodies(BODY))
    matn, verse = IRI("hadith/9/text/1"), IRI("quran/verse/1/2")
    assert (IRI("hadith/9"), HADITH.hasHadithText, matn) in graph
    assert (matn, ST.refersTo, verse) in graph
    assert (verse, RDF.type, ST.Verse) in graph
    assert (IRI("quran/surah/1"), ST.containsVerse, verse) in graph
    (fragment,) = graph.subjects(RDF.type, ST.VerseFragment)
    assert (fragment, ST.isPartOfVerse, verse) in graph
    texts = list(graph.objects(matn, ST.hasText))
    assert texts and all(text.language == "ar" for text in texts)


def test_every_node_points_back_to_its_source_line(map_bodies):
    graph = _graph(map_bodies(BODY))
    source = graph.value(IRI("hadith/9"), URIRef("http://purl.org/dc/terms/source"))
    assert str(source) == "file0.xml#L1"


def test_output_is_deterministic(map_bodies):
    first = set(_graph(map_bodies(BODY)))
    second = set(_graph(map_bodies(BODY)))
    assert first == second
