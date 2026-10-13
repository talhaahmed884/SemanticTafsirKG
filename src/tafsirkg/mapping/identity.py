"""The identifier scheme: every rule for naming graph resources lives here.

Identifiers are relative paths such as ``hadith/134/chain/1``; the RDF layer prefixes
them with the base IRI. They are derived only from the data (numbers in the XML,
positions within a parent, or a hash of normalized text), never from counters over
the whole run, so converting the same XML twice gives the same IRIs, and converting
one chapter does not change the IRIs of another.
"""

from __future__ import annotations

import hashlib

from tafsirkg.domain.model import EntityKind


def text_hash(key: str) -> str:
    """A short, stable digest of a normalized text, for resources identified by their text."""
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def chapter(number: str) -> str:
    return f"chapter/{number}"


def section(number: str) -> str:
    return f"section/{number}"


def subsection(number: str) -> str:
    return f"subsection/{number}"


def commentary(division_number: str, ordinal: int) -> str:
    return f"commentary/{division_number}/{ordinal}"


def hadith(number: int) -> str:
    return f"hadith/{number}"


def hadith_continuation(continued_hadith_id: str, index: int) -> str:
    """A hadith paragraph without ``xml:id`` that continues the previous hadith."""
    return f"{continued_hadith_id}/continuation/{index}"


def unnumbered_hadith(division_number: str, ordinal: int) -> str:
    """A hadith paragraph without ``xml:id`` and no previous hadith to attach it to."""
    return f"hadith/unnumbered/{division_number}/{ordinal}"


def chain(hadith_id: str, index: int) -> str:
    return f"{hadith_id}/chain/{index}"


def chain_link(chain_id: str, position: int) -> str:
    return f"{chain_id}/link/{position}"


def child(parent_id: str, kind: str, index: int) -> str:
    """A unit owned by another unit, e.g. ``commentary/1.1/3/segment/2``."""
    return f"{parent_id}/{kind}/{index}"


def note(paragraph_id: str, index: int) -> str:
    return f"{paragraph_id}/note/{index}"


def narrator(narrator_id: str) -> str:
    return f"narrator/{narrator_id}"


def unidentified_narrator(link_id: str) -> str:
    """A narrator without a narrator ID: one resource per occurrence."""
    return f"{link_id}/narrator"


def named_entity(kind: EntityKind, key: str) -> str:
    return f"entity/{kind.value}/{text_hash(key)}"


def theme(code: str) -> str:
    return f"theme/{code}"


def surah(number: int) -> str:
    return f"quran/surah/{number}"


def verse(surah_number: int, verse_number: int) -> str:
    return f"quran/verse/{surah_number}/{verse_number}"


def verse_fragment(verse_locations: list[tuple[int, int]], key: str) -> str:
    if not verse_locations:
        return f"quran/fragment/{text_hash(key)}"
    surah_number = verse_locations[0][0]
    numbers = [number for _, number in verse_locations]
    span = str(numbers[0]) if len(numbers) == 1 else f"{numbers[0]}-{numbers[-1]}"
    return f"quran/verse/{surah_number}/{span}/fragment/{text_hash(key)}"


def book_location(edition: str, volume: int, page: int) -> str:
    return f"location/book/{edition}/{volume}/{page}"


def dataset_location(edition: str, reference: str) -> str:
    return f"location/dataset/{edition}/{reference}"


def line_beginning(number: str) -> str:
    return f"location/line/{number}"
