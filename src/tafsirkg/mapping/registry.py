"""Identity map for resources shared across the text.

A theme, a person mentioned by name, a narrator with an ID, a verse or a page is the
same resource wherever it appears. The registry hands out exactly one domain object per
identity, so the mappers never create duplicates and never need to look anything up in
the graph.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from tafsirkg.arabic import collapse_whitespace, quran_match_key, strip_marks
from tafsirkg.domain.model import (
    BookLocation,
    DatasetLocation,
    EntityKind,
    LineBeginning,
    NamedEntity,
    Narrator,
    Surah,
    Theme,
    Verse,
    VerseFragment,
)
from tafsirkg.mapping import identity

_K = TypeVar("_K")
_V = TypeVar("_V")


def _get_or_create(store: dict[_K, _V], key: _K, create: Callable[[], _V]) -> _V:
    if key not in store:
        store[key] = create()
    return store[key]


def _add_name(names: list[str], surface: str) -> None:
    surface = collapse_whitespace(surface)
    if surface and surface not in names:
        names.append(surface)


class EntityRegistry:
    def __init__(self) -> None:
        self._themes: dict[str, Theme] = {}
        self._entities: dict[tuple[EntityKind, str], NamedEntity] = {}
        self._narrators: dict[str, Narrator] = {}
        self._surahs: dict[int, Surah] = {}
        self._verses: dict[tuple[int, int], Verse] = {}
        self._fragments: dict[str, VerseFragment] = {}
        self._book_locations: dict[str, BookLocation] = {}
        self._dataset_locations: dict[str, DatasetLocation] = {}
        self._line_beginnings: dict[str, LineBeginning] = {}

    # -- creation -----------------------------------------------------------------

    def theme(self, code: str) -> Theme:
        return _get_or_create(self._themes, code, lambda: Theme(identity.theme(code), code))

    def named_entity(self, kind: EntityKind, surface: str) -> NamedEntity:
        key = strip_marks(surface)
        entity = _get_or_create(
            self._entities,
            (kind, key),
            lambda: NamedEntity(identity.named_entity(kind, key), kind),
        )
        _add_name(entity.names, surface)
        return entity

    def narrator(self, narrator_id: str | None, surface: str, link_id: str) -> Narrator:
        """The narrator with ``narrator_id``, or a new per-occurrence narrator if there is none."""
        if narrator_id is None:
            resource_id = identity.unidentified_narrator(link_id)
        else:
            resource_id = identity.narrator(narrator_id)
        narrator = _get_or_create(self._narrators, resource_id, lambda: Narrator(resource_id, narrator_id))
        _add_name(narrator.names, surface)
        return narrator

    def surah(self, number: int) -> Surah:
        return _get_or_create(self._surahs, number, lambda: Surah(identity.surah(number), number))

    def verse(self, surah_number: int, verse_number: int, canonical_text: str) -> Verse:
        def create() -> Verse:
            surah = self.surah(surah_number)
            verse = Verse(identity.verse(surah_number, verse_number), surah, verse_number, canonical_text)
            surah.verses.append(verse)
            return verse

        return _get_or_create(self._verses, (surah_number, verse_number), create)

    def verse_fragment(
        self,
        text: str,
        verses: list[Verse],
        reading_type: str | None = None,
        subtype: str | None = None,
    ) -> VerseFragment:
        """The fragment for this text of these verses; identical quotations share one."""
        locations = [(verse.surah.number, verse.number) for verse in verses]
        key = f"{quran_match_key(text)}|{reading_type or ''}|{subtype or ''}"
        resource_id = identity.verse_fragment(locations, key)
        return _get_or_create(
            self._fragments,
            resource_id,
            lambda: VerseFragment(
                resource_id, collapse_whitespace(text), list(verses), reading_type, subtype
            ),
        )

    def book_location(self, edition: str, volume: int, page: int) -> BookLocation:
        resource_id = identity.book_location(edition, volume, page)
        return _get_or_create(
            self._book_locations,
            resource_id,
            lambda: BookLocation(resource_id, edition, volume, page),
        )

    def dataset_location(self, edition: str, reference: str, page: str) -> DatasetLocation:
        resource_id = identity.dataset_location(edition, reference)
        return _get_or_create(
            self._dataset_locations,
            resource_id,
            lambda: DatasetLocation(resource_id, edition, reference, page),
        )

    def line_beginning(self, number: str) -> LineBeginning:
        resource_id = identity.line_beginning(number)
        return _get_or_create(self._line_beginnings, resource_id, lambda: LineBeginning(resource_id, number))

    # -- read access for the RDF layer ----------------------------------------------

    @property
    def themes(self) -> tuple[Theme, ...]:
        return tuple(self._themes.values())

    @property
    def named_entities(self) -> tuple[NamedEntity, ...]:
        return tuple(self._entities.values())

    @property
    def narrators(self) -> tuple[Narrator, ...]:
        return tuple(self._narrators.values())

    @property
    def surahs(self) -> tuple[Surah, ...]:
        return tuple(self._surahs.values())

    @property
    def verses(self) -> tuple[Verse, ...]:
        return tuple(self._verses.values())

    @property
    def verse_fragments(self) -> tuple[VerseFragment, ...]:
        return tuple(self._fragments.values())

    @property
    def book_locations(self) -> tuple[BookLocation, ...]:
        return tuple(self._book_locations.values())

    @property
    def dataset_locations(self) -> tuple[DatasetLocation, ...]:
        return tuple(self._dataset_locations.values())

    @property
    def line_beginnings(self) -> tuple[LineBeginning, ...]:
        return tuple(self._line_beginnings.values())
