"""The ontology terms the converter uses.

Each namespace is an rdflib ``DefinedNamespace``: using a term that is not listed here
raises an error instead of silently minting a misspelled IRI. A test checks that every
term listed here is declared in ``Ontology/SemanticTafsirOntology.owl``.
"""

from __future__ import annotations

from rdflib import URIRef
from rdflib.namespace import DCTERMS, DefinedNamespace, Namespace

from tafsirkg.domain.model import EntityKind, NarratorRole


class ST(DefinedNamespace):
    """``http://www.semantictafsir.com/ontology/``"""

    _NS = Namespace("http://www.semantictafsir.com/ontology/")
    _fail = True

    # Classes
    AdditionalText: URIRef
    BookLocation: URIRef
    Commentary: URIRef
    DatasetLocation: URIRef
    LineBeginning: URIRef
    Location: URIRef
    Note: URIRef
    Organization: URIRef
    Other: URIRef
    Person: URIRef
    Poetry: URIRef
    Section: URIRef
    Segment: URIRef
    SubSection: URIRef
    Surah: URIRef
    TafsirChapter: URIRef
    ThematicVerseFragmentReference: URIRef
    ThematicVerseReference: URIRef
    Theme: URIRef
    Time: URIRef
    Verse: URIRef
    VerseFragment: URIRef

    # Object properties
    containsAdditionalText: URIRef
    containsCommentary: URIRef
    containsSection: URIRef
    containsSegment: URIRef
    containsSubSection: URIRef
    containsVerse: URIRef
    hasBookLocation: URIRef
    hasDatasetLocation: URIRef
    hasLineBeginning: URIRef
    hasNarratorType: URIRef
    hasNote: URIRef
    hasPart: URIRef
    hasTheme: URIRef
    isAbout: URIRef
    isPartOfHadith: URIRef
    isPartOfVerse: URIRef
    mentions: URIRef
    references: URIRef
    refersTo: URIRef

    # Datatype properties
    hasChapterNo: URIRef
    hasCommentaryNo: URIRef
    hasEdition: URIRef
    hasHadithNo: URIRef
    hasID: URIRef
    hasLanguage: URIRef
    hasName: URIRef
    hasPageNo: URIRef
    hasReferenceNo: URIRef
    hasSectionNo: URIRef
    hasSubSectionNo: URIRef
    hasSubType: URIRef
    hasSurahNo: URIRef
    hasText: URIRef
    hasType: URIRef
    hasVerseNo: URIRef
    hasVolumeNo: URIRef


class HADITH(DefinedNamespace):
    """``http://www.semantichadith.com/ontology/``"""

    _NS = Namespace("http://www.semantichadith.com/ontology/")
    _fail = True

    # Classes
    Hadith: URIRef
    HadithNarrator: URIRef
    HadithText: URIRef
    NarratorChain: URIRef
    NarratorChainSegment: URIRef
    RootNarrator: URIRef
    RootNarratorChainSegment: URIRef

    # Object properties
    follows: URIRef
    hasHadithText: URIRef
    hasNarratorChain: URIRef
    hasNarratorSegment: URIRef
    hasRootNarrator: URIRef
    hasRootNarratorSegment: URIRef
    heardFrom: URIRef
    precedes: URIRef
    refersToNarrator: URIRef


# The NarratorType individuals are declared in the ontology under ``ontology#``
# (with a hash), unlike every other term. They are referenced exactly as declared so
# that they link to the ontology's individuals.
NARRATOR_TYPE = Namespace("http://www.semantictafsir.com/ontology#")

NARRATOR_TYPE_IRIS: dict[NarratorRole, URIRef] = {role: NARRATOR_TYPE[role.value] for role in NarratorRole}

ENTITY_CLASSES: dict[EntityKind, URIRef] = {
    EntityKind.PERSON: ST.Person,
    EntityKind.ORGANIZATION: ST.Organization,
    EntityKind.LOCATION: ST.Location,
    EntityKind.TIME: ST.Time,
    EntityKind.OTHER: ST.Other,
}

PREFIXES: dict[str, Namespace] = {
    "st": ST._NS,
    "hadith": HADITH._NS,
    "nt": NARRATOR_TYPE,
    "dcterms": Namespace(str(DCTERMS)),
}
