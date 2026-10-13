"""Writes domain objects as RDF triples using the ontology vocabulary.

Modelling choices that the ontology leaves open, or where using it literally would
cause problems, are made here and documented next to the code:

* A section links its hadith with ``st:hasPart``, not ``st:containsCommentary``: the
  range of ``containsCommentary`` is ``Commentary``, which is disjoint with ``Hadith``.
* The root link of a chain is linked with both ``hasNarratorSegment`` and
  ``hasRootNarratorSegment``, so the ontology's ``hasNarrator`` property chain also
  reaches the root narrator.
* Narrator roles outside the ``NarratorType`` enumeration (e.g. ``qari``) are kept as
  ``st:hasType`` literals on the chain link.
* Every paragraph, heading and annotated span carries ``dcterms:source`` with the file
  and line it came from.
"""

from __future__ import annotations

from collections.abc import Iterable

from rdflib import RDF, RDFS, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS

from tafsirkg.domain.model import (
    Commentary,
    Division,
    Hadith,
    NarratorChain,
    Paragraph,
    Section,
    SharedResources,
    SubSection,
    TafsirChapter,
    TextUnit,
    ThematicVerseReference,
    Verse,
)
from tafsirkg.rdf.iris import IriFactory
from tafsirkg.rdf.vocabulary import ENTITY_CLASSES, HADITH, NARRATOR_TYPE_IRIS, PREFIXES, ST

ARABIC = "ar"


def _arabic(text: str) -> Literal:
    return Literal(text, lang=ARABIC)


def _number(value: str) -> Literal:
    """An integer literal when the value is a plain number, otherwise a string."""
    return Literal(int(value)) if value.isdigit() else Literal(value)


class GraphWriter:
    def __init__(self, iris: IriFactory) -> None:
        self._iri = iris
        self._graph = Graph()

    def write(self, chapters: Iterable[TafsirChapter], shared: SharedResources) -> Graph:
        self._graph = Graph()
        for prefix, namespace in PREFIXES.items():
            self._graph.bind(prefix, namespace)
        self._graph.bind("res", self._iri.base_iri)
        for chapter in chapters:
            self._chapter(chapter)
        self._shared_resources(shared)
        return self._graph

    def _add(self, subject: URIRef, predicate: URIRef, obj: URIRef | Literal) -> None:
        self._graph.add((subject, predicate, obj))

    # -- structure ------------------------------------------------------------------

    def _chapter(self, chapter: TafsirChapter) -> None:
        subject = self._iri(chapter.id)
        self._add(subject, RDF.type, ST.TafsirChapter)
        self._add(subject, RDFS.label, Literal(f"Tafsir chapter {chapter.number}", lang="en"))
        self._add(subject, ST.hasChapterNo, _number(chapter.number))
        if chapter.language:
            self._add(subject, ST.hasLanguage, Literal(chapter.language))
        if chapter.surah is not None:
            self._add(subject, ST.hasSurahNo, Literal(chapter.surah.number))
            self._add(subject, ST.refersTo, self._iri(chapter.surah.id))
        for source in chapter.sources:
            self._add(subject, DCTERMS.source, Literal(source.file))
        self._division_content(subject, chapter, ST.containsSection)

    def _division(self, division: Division) -> URIRef:
        subject = self._iri(division.id)
        if isinstance(division, Section):
            self._add(subject, RDF.type, ST.Section)
            self._add(subject, RDFS.label, Literal(f"Section {division.number}", lang="en"))
            self._add(subject, ST.hasSectionNo, Literal(division.number))
        elif isinstance(division, SubSection):
            self._add(subject, RDF.type, ST.SubSection)
            self._add(subject, RDFS.label, Literal(f"Subsection {division.number}", lang="en"))
            self._add(subject, ST.hasSubSectionNo, Literal(division.number))
        self._division_content(subject, division, ST.containsSubSection)
        return subject

    def _division_content(self, subject: URIRef, division: Division, subdivision_predicate: URIRef) -> None:
        # Qur'an quotations in a heading say which verses the division is about.
        self._text_unit(subject, division, quran_predicate=ST.isAbout)

        previous: URIRef | None = None
        for paragraph in division.paragraphs:
            node = self._paragraph(paragraph)
            predicate = ST.containsCommentary if isinstance(paragraph, Commentary) else ST.hasPart
            self._add(subject, predicate, node)
            if previous is not None:
                self._add(node, HADITH.follows, previous)
            previous = node

        previous = None
        for subdivision in division.subdivisions:
            node = self._division(subdivision)
            self._add(subject, subdivision_predicate, node)
            if previous is not None:
                self._add(node, HADITH.follows, previous)
            previous = node

    # -- paragraphs and text --------------------------------------------------------

    def _paragraph(self, paragraph: Paragraph) -> URIRef:
        subject = self._iri(paragraph.id)
        if isinstance(paragraph, Hadith):
            self._hadith(subject, paragraph)
        else:
            self._add(subject, RDF.type, ST.Commentary)
            self._add(subject, ST.hasCommentaryNo, Literal(paragraph.ordinal))
        for note in paragraph.notes:
            node = self._iri(note.id)
            self._add(node, RDF.type, ST.Note)
            self._add(node, ST.hasText, Literal(note.text))
            self._add(subject, ST.hasNote, node)
        self._text_unit(subject, paragraph)
        return subject

    def _hadith(self, subject: URIRef, hadith: Hadith) -> None:
        self._add(subject, RDF.type, HADITH.Hadith)
        if hadith.number is not None:
            self._add(subject, ST.hasHadithNo, Literal(hadith.number))
            self._add(subject, RDFS.label, Literal(f"Hadith {hadith.number}", lang="en"))
        if hadith.continues is not None:
            self._add(subject, ST.refersTo, self._iri(hadith.continues.id))
        for matn in hadith.texts:
            node = self._iri(matn.id)
            self._add(node, RDF.type, HADITH.HadithText)
            self._add(subject, HADITH.hasHadithText, node)
            self._text_unit(node, matn)
        for chain in hadith.chains:
            self._chain(subject, chain)

    def _chain(self, hadith: URIRef, chain: NarratorChain) -> None:
        subject = self._iri(chain.id)
        self._add(subject, RDF.type, HADITH.NarratorChain)
        self._add(hadith, HADITH.hasNarratorChain, subject)
        self._add(subject, ST.isPartOfHadith, hadith)

        previous = None
        for link in chain.links:
            node = self._iri(link.id)
            narrator = self._iri(link.narrator.id)
            self._add(node, RDF.type, HADITH.NarratorChainSegment)
            self._add(subject, HADITH.hasNarratorSegment, node)
            self._add(node, HADITH.refersToNarrator, narrator)
            for token in link.role_tokens:
                self._add(node, ST.hasType, Literal(token))
            if previous is not None:
                self._add(self._iri(previous.id), HADITH.precedes, node)
                if previous.narrator is not link.narrator:
                    self._add(self._iri(previous.narrator.id), HADITH.heardFrom, narrator)
            previous = link

        root = self._iri(chain.root.id)
        self._add(root, RDF.type, HADITH.RootNarratorChainSegment)
        self._add(subject, HADITH.hasRootNarratorSegment, root)
        self._add(hadith, HADITH.hasRootNarrator, self._iri(chain.root.narrator.id))

    def _text_unit(self, subject: URIRef, unit: TextUnit, quran_predicate: URIRef = ST.refersTo) -> None:
        if unit.text:
            self._add(subject, ST.hasText, _arabic(unit.text))
        if not isinstance(unit, TafsirChapter):  # a chapter lists its files instead
            self._add(subject, DCTERMS.source, Literal(str(unit.source)))
        for theme in unit.themes:
            self._add(subject, ST.hasTheme, self._iri(theme.id))
        for entity in unit.mentions:
            self._add(subject, ST.mentions, self._iri(entity.id))
        for target in unit.quran_references:
            self._add(subject, quran_predicate, self._iri(target.id))
        for reference in unit.thematic_references:
            self._add(subject, ST.references, self._thematic_reference(reference))
        for segment in unit.segments:
            node = self._iri(segment.id)
            self._add(node, RDF.type, ST.Segment)
            self._add(subject, ST.containsSegment, node)
            self._text_unit(node, segment)
        for poem in unit.poems:
            node = self._iri(poem.id)
            self._add(node, RDF.type, ST.Poetry)
            self._add(subject, ST.hasPart, node)
            self._text_unit(node, poem)
        for addition in unit.additions:
            node = self._iri(addition.id)
            self._add(node, RDF.type, ST.AdditionalText)
            if addition.kind:
                self._add(node, ST.hasType, Literal(addition.kind))
            self._add(subject, ST.containsAdditionalText, node)
            self._text_unit(node, addition)
        for location in unit.book_locations:
            self._add(subject, ST.hasBookLocation, self._iri(location.id))
        for location in unit.dataset_locations:
            self._add(subject, ST.hasDatasetLocation, self._iri(location.id))
        for line in unit.line_beginnings:
            self._add(subject, ST.hasLineBeginning, self._iri(line.id))

    def _thematic_reference(self, reference: ThematicVerseReference) -> URIRef:
        subject = self._iri(reference.id)
        is_verse = isinstance(reference.target, Verse)
        self._add(
            subject,
            RDF.type,
            ST.ThematicVerseReference if is_verse else ST.ThematicVerseFragmentReference,
        )
        self._add(subject, ST.refersTo, self._iri(reference.target.id))
        self._add(subject, ST.hasText, _arabic(reference.text))
        self._add(subject, DCTERMS.source, Literal(str(reference.source)))
        for theme in reference.themes:
            self._add(subject, ST.hasTheme, self._iri(theme.id))
        return subject

    # -- shared resources -----------------------------------------------------------

    def _shared_resources(self, shared: SharedResources) -> None:
        for theme in shared.themes:
            subject = self._iri(theme.id)
            self._add(subject, RDF.type, ST.Theme)
            self._add(subject, ST.hasName, Literal(theme.code))
            self._add(subject, RDFS.label, Literal(theme.code))

        for entity in shared.named_entities:
            subject = self._iri(entity.id)
            self._add(subject, RDF.type, ENTITY_CLASSES[entity.kind])
            self._names(subject, entity.names)

        for narrator in shared.narrators:
            subject = self._iri(narrator.id)
            self._add(subject, RDF.type, HADITH.HadithNarrator)
            if narrator.is_root:
                self._add(subject, RDF.type, HADITH.RootNarrator)
            if narrator.narrator_id:
                self._add(subject, ST.hasID, Literal(narrator.narrator_id))
            self._names(subject, narrator.names)
            for role in narrator.roles:
                self._add(subject, ST.hasNarratorType, NARRATOR_TYPE_IRIS[role])

        for surah in shared.surahs:
            subject = self._iri(surah.id)
            self._add(subject, RDF.type, ST.Surah)
            self._add(subject, ST.hasSurahNo, Literal(surah.number))
            for verse in surah.verses:
                self._add(subject, ST.containsVerse, self._iri(verse.id))

        for verse in shared.verses:
            subject = self._iri(verse.id)
            self._add(subject, RDF.type, ST.Verse)
            self._add(subject, RDFS.label, Literal(f"{verse.surah.number}:{verse.number}"))
            self._add(subject, ST.hasSurahNo, Literal(verse.surah.number))
            self._add(subject, ST.hasVerseNo, Literal(verse.number))
            self._add(subject, ST.hasText, _arabic(verse.text))

        for fragment in shared.verse_fragments:
            subject = self._iri(fragment.id)
            self._add(subject, RDF.type, ST.VerseFragment)
            self._add(subject, ST.hasText, _arabic(fragment.text))
            for verse in fragment.verses:
                self._add(subject, ST.isPartOfVerse, self._iri(verse.id))
            if fragment.reading_type:
                self._add(subject, ST.hasType, Literal(fragment.reading_type))
            if fragment.subtype:
                self._add(subject, ST.hasSubType, Literal(fragment.subtype))

        for book in shared.book_locations:
            subject = self._iri(book.id)
            self._add(subject, RDF.type, ST.BookLocation)
            self._add(subject, ST.hasEdition, Literal(book.edition))
            self._add(subject, ST.hasVolumeNo, Literal(book.volume))
            self._add(subject, ST.hasPageNo, Literal(book.page))

        for dataset in shared.dataset_locations:
            subject = self._iri(dataset.id)
            self._add(subject, RDF.type, ST.DatasetLocation)
            self._add(subject, ST.hasEdition, Literal(dataset.edition))
            self._add(subject, ST.hasReferenceNo, Literal(dataset.reference))
            self._add(subject, ST.hasPageNo, _number(dataset.page))

        for line in shared.line_beginnings:
            subject = self._iri(line.id)
            self._add(subject, RDF.type, ST.LineBeginning)
            self._add(subject, ST.hasReferenceNo, _number(line.number))

    def _names(self, subject: URIRef, names: list[str]) -> None:
        for name in names:
            self._add(subject, ST.hasName, _arabic(name))
        if names:
            self._add(subject, RDFS.label, _arabic(names[0]))
