"""Business classes mirroring the SemanticTafsir ontology.

These classes hold what the knowledge graph will say, without any RDF or XML. Each
class documents the ontology class it becomes. Every object has an ``id``: a
relative, deterministic identifier (e.g. ``hadith/134/chain/1``) from which the RDF
layer mints the IRI, so re-running the conversion never changes identifiers.

Objects that are shared across the text (narrators, named entities, themes, verses,
verse fragments, page locations) are created only through
:class:`tafsirkg.mapping.registry.EntityRegistry`, which guarantees one object per
identity. Everything else is owned by exactly one parent.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from tafsirkg.source import SourceRef


# ---------------------------------------------------------------------------
# Shared resources
# ---------------------------------------------------------------------------


@dataclass(eq=False)
class Theme:
    """A theme code from an ``@ana`` attribute, e.g. ``lugha``. -> ``st:Theme``"""

    id: str
    code: str


class EntityKind(Enum):
    """The ``@role`` of a ``<name>``; decides the ontology class of the entity."""

    PERSON = "person"  # st:Person
    ORGANIZATION = "organization"  # st:Organization
    LOCATION = "location"  # st:Location
    TIME = "time"  # st:Time
    OTHER = "other"  # st:Other


@dataclass(eq=False)
class NamedEntity:
    """Something mentioned by name. All mentions with the same normalized name and kind share it."""

    id: str
    kind: EntityKind
    names: list[str] = field(default_factory=list)  # distinct surface forms, as written


class NarratorRole(Enum):
    """The ``NarratorType`` individuals of the ontology (``persName/@ana``)."""

    SHAYKH = "shaykh"  # Tabari's own teacher: the first narrator of a chain
    RAWI = "rawi"
    SAHABI = "sahabi"
    UNKNOWN_RAWI = "unknown_rawi"
    UNKNOWN_SAHABI = "unknown_sahabi"


@dataclass(eq=False)
class Narrator:
    """A hadith narrator. -> ``hadith:HadithNarrator`` (also ``hadith:RootNarrator`` if ever root)

    Narrators with a narrator ID (``persName/@n``, e.g. ``L4883``) are merged across the
    whole text by that ID. Narrators without an ID are kept per occurrence: merging by
    name would conflate different people (``أبيه``, "his father", is a different person
    in every chain). Merging those is left to a separate entity-resolution step.
    """

    id: str
    narrator_id: str | None
    names: list[str] = field(default_factory=list)
    roles: set[NarratorRole] = field(default_factory=set)
    is_root: bool = False


@dataclass(eq=False)
class Surah:
    """-> ``st:Surah``"""

    id: str
    number: int
    verses: list[Verse] = field(default_factory=list)


@dataclass(eq=False)
class Verse:
    """A whole verse, with its canonical text. -> ``st:Verse``"""

    id: str
    surah: Surah
    number: int
    text: str


@dataclass(eq=False)
class VerseFragment:
    """Quoted text that is not a whole verse. -> ``st:VerseFragment``

    Identical quotations of the same verse(s) share one fragment. ``verses`` is empty
    when the quotation has no ``@n`` and could not be located.
    """

    id: str
    text: str
    verses: list[Verse] = field(default_factory=list)
    reading_type: str | None = None  # "qiraat" for a variant reading
    subtype: str | None = None  # quote/@subtype, e.g. "short"


QuranTarget = Verse | VerseFragment


@dataclass(eq=False)
class BookLocation:
    """A page in a print edition (``<pb type="turki" n="1:106"/>``). -> ``st:BookLocation``"""

    id: str
    edition: str
    volume: int
    page: int


@dataclass(eq=False)
class DatasetLocation:
    """A page in the digital edition (``<pb ed="GK" edRef=".." n=".."/>``). -> ``st:DatasetLocation``"""

    id: str
    edition: str
    reference: str
    page: str


@dataclass(eq=False)
class LineBeginning:
    """``<lb n="177"/>``. -> ``st:LineBeginning``"""

    id: str
    number: str


# ---------------------------------------------------------------------------
# Text units: everything that has text and can carry inline annotations
# ---------------------------------------------------------------------------


@dataclass(eq=False, kw_only=True)
class ThematicVerseReference:
    """A themed span inside a Qur'an quotation, e.g. ``<seg ana="sifatilahi">الرَّحْمَنِ</seg>``.

    -> ``st:ThematicVerseReference`` (target is a verse) or
    ``st:ThematicVerseFragmentReference`` (target is a fragment).
    """

    id: str
    source: SourceRef
    target: QuranTarget
    text: str
    themes: list[Theme] = field(default_factory=list)


@dataclass(eq=False, kw_only=True)
class TextUnit:
    """Base for every unit of text. Inline annotations attach to the innermost unit."""

    id: str
    source: SourceRef
    text: str = ""
    themes: list[Theme] = field(default_factory=list)
    mentions: list[NamedEntity] = field(default_factory=list)
    quran_references: list[QuranTarget] = field(default_factory=list)
    thematic_references: list[ThematicVerseReference] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    poems: list[Poetry] = field(default_factory=list)
    additions: list[AdditionalText] = field(default_factory=list)
    book_locations: list[BookLocation] = field(default_factory=list)
    dataset_locations: list[DatasetLocation] = field(default_factory=list)
    line_beginnings: list[LineBeginning] = field(default_factory=list)


@dataclass(eq=False, kw_only=True)
class Segment(TextUnit):
    """An annotated span (``<seg>``, or a ``<name>``/``<time>`` carrying ``@ana``). -> ``st:Segment``"""


@dataclass(eq=False, kw_only=True)
class Poetry(TextUnit):
    """A quoted poem (``<quote type="poetry">``). -> ``st:Poetry``"""

    lines: list[str] = field(default_factory=list)


@dataclass(eq=False, kw_only=True)
class AdditionalText(TextUnit):
    """An editorial addition (``<add>``). -> ``st:AdditionalText``"""

    kind: str | None = None


@dataclass(eq=False, kw_only=True)
class HadithText(TextUnit):
    """The matn of a hadith (``<said>``). -> ``hadith:HadithText``"""


@dataclass(eq=False)
class Note:
    """Reference numbers of a hadith (``<note> 119 /2 /140 </note>``). -> ``st:Note``"""

    id: str
    text: str


@dataclass(eq=False, kw_only=True)
class Paragraph(TextUnit):
    """A ``<p>``. ``ordinal`` is its 1-based position among all ``<p>`` of its division.

    The position counts every paragraph, hadith included, and continues across files
    when a division is spread over several of them. It mirrors the XML and is used for
    identifiers; the commentary number is a separate count (``Division.commentaries``).
    """

    ordinal: int
    notes: list[Note] = field(default_factory=list)


@dataclass(eq=False, kw_only=True)
class Commentary(Paragraph):
    """``<p n="nothadith">``: Tabari's own commentary. -> ``st:Commentary``"""


@dataclass(eq=False)
class ChainLink:
    """One narrator's place in a chain. -> ``hadith:NarratorChainSegment``

    The last link of a chain is the root (earliest) narrator and becomes a
    ``hadith:RootNarratorChainSegment``. ``role_tokens`` keeps ``persName/@ana`` as
    written, including tokens outside the ``NarratorType`` enumeration (e.g. ``qari``).
    """

    id: str
    position: int
    narrator: Narrator
    role_tokens: tuple[str, ...]


@dataclass(eq=False)
class NarratorChain:
    """An isnad, from Tabari's teacher (first) to the root narrator (last). -> ``hadith:NarratorChain``"""

    id: str
    links: list[ChainLink] = field(default_factory=list)

    @property
    def root(self) -> ChainLink:
        return self.links[-1]


@dataclass(eq=False, kw_only=True)
class Hadith(Paragraph):
    """``<p n="hadith">``. -> ``hadith:Hadith``

    ``number`` comes from ``xml:id`` (``h134`` -> 134). Continuation paragraphs (no
    ``xml:id``, typically "بمثله"/"بنحوه") have no number and point to the hadith they
    continue.
    """

    number: int | None = None
    continues: Hadith | None = None
    chains: list[NarratorChain] = field(default_factory=list)
    texts: list[HadithText] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Document structure
# ---------------------------------------------------------------------------


@dataclass(eq=False, kw_only=True)
class Division(TextUnit):
    """A ``<div>``. Its ``text`` is the heading; Qur'an quotes in the heading say what it is about."""

    number: str
    paragraphs: list[Paragraph] = field(default_factory=list)
    subdivisions: list[Division] = field(default_factory=list)

    @property
    def commentaries(self) -> tuple[Commentary, ...]:
        """The division's commentary paragraphs in order; commentary ``k`` is ``commentaries[k - 1]``.

        Commentary numbering counts only Tabari's own words. A hadith is quoted material,
        not commentary, so it does not take a commentary number (it has its own number).
        The numbers are derived from ``paragraphs``, so they cannot drift from the structure.
        """
        return tuple(paragraph for paragraph in self.paragraphs if isinstance(paragraph, Commentary))


@dataclass(eq=False, kw_only=True)
class SubSection(Division):
    """``<div type="subsection" n="1.2.3">``. -> ``st:SubSection``"""


@dataclass(eq=False, kw_only=True)
class Section(Division):
    """``<div type="section" n="1.2">``. -> ``st:Section``"""


@dataclass(eq=False, kw_only=True)
class TafsirChapter(Division):
    """``<div type="chapter" n="1">``: the tafsir of one surah. -> ``st:TafsirChapter``

    A chapter can span several files; ``sources`` lists all of them.
    """

    language: str | None = None
    surah: Surah | None = None
    sources: list[SourceRef] = field(default_factory=list)


class SharedResources(Protocol):
    """Read access to the resources shared across chapters (see ``EntityRegistry``)."""

    @property
    def themes(self) -> Sequence[Theme]: ...
    @property
    def named_entities(self) -> Sequence[NamedEntity]: ...
    @property
    def narrators(self) -> Sequence[Narrator]: ...
    @property
    def surahs(self) -> Sequence[Surah]: ...
    @property
    def verses(self) -> Sequence[Verse]: ...
    @property
    def verse_fragments(self) -> Sequence[VerseFragment]: ...
    @property
    def book_locations(self) -> Sequence[BookLocation]: ...
    @property
    def dataset_locations(self) -> Sequence[DatasetLocation]: ...
    @property
    def line_beginnings(self) -> Sequence[LineBeginning]: ...
