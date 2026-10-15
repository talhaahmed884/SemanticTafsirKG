"""The labelling scheme: every rule for a node's ``rdfs:label`` lives here.

Each node gets exactly one label that starts with its type, so a node can be recognised
in a graph visualisation without opening it (``Verse 1:2``, ``Chain Link 2``,
``Narrator L4883: أبو كريب``). Labels are plain literals without a language tag, because
many of them combine an English type name with Arabic text; the Arabic names themselves
are kept as ``st:hasName`` / ``st:hasText`` literals tagged ``@ar``.

A unit owned by another unit is labelled with its type and its index only
(``Thematic Verse Reference 3``, ``Commentary 4``), not with its parent's label: the relationship to the
parent already says where it belongs. The index is taken from the end of the id, so a
label always agrees with its IRI.
"""

from __future__ import annotations

from tafsirkg.domain.model import (
    BookLocation,
    DatasetLocation,
    LineBeginning,
    NamedEntity,
    Narrator,
    Surah,
    Theme,
    Verse,
    VerseFragment,
)

EXCERPT_WORDS = 5


def excerpt(text: str, words: int = EXCERPT_WORDS) -> str:
    """The first ``words`` words of a text, with an ellipsis when it is longer."""
    parts = text.split()
    return " ".join(parts[:words]) + (" …" if len(parts) > words else "")


# -- document structure -----------------------------------------------------------


def chapter(number: str) -> str:
    return f"Tafsir Chapter {number}"


def section(number: str) -> str:
    return f"Section {number}"


def subsection(number: str) -> str:
    return f"Subsection {number}"


def commentary(ordinal: int) -> str:
    return f"Commentary {ordinal}"


def hadith(number: int) -> str:
    return f"Hadith {number}"


def unnumbered_hadith(ordinal: int) -> str:
    return f"Unnumbered Hadith {ordinal}"


def owned(kind: str, resource_id: str) -> str:
    """A unit owned by another unit, e.g. ``Narrator Chain 1`` for ``hadith/134/chain/1``."""
    return f"{kind} {resource_id.rsplit('/', 1)[-1]}"


# -- shared resources ---------------------------------------------------------------


def theme(theme: Theme) -> str:
    return f"Theme {theme.code}"


def named_entity(entity: NamedEntity) -> str:
    kind = entity.kind.value.capitalize()
    return f"{kind}: {entity.names[0]}" if entity.names else kind


def narrator(narrator: Narrator) -> str:
    head = f"Narrator {narrator.narrator_id}" if narrator.narrator_id else "Narrator"
    return f"{head}: {narrator.names[0]}" if narrator.names else head


def surah(surah: Surah) -> str:
    return f"Surah {surah.number}"


def verse(verse: Verse) -> str:
    return f"Verse {verse.surah.number}:{verse.number}"


def verse_fragment(fragment: VerseFragment) -> str:
    """``Verse Fragment 1:2 (الْحَمْدُ لِلَّهِ)``; the excerpt tells fragments of one verse apart.

    A fragment without verses (a quotation without ``@n``) gets no verse reference.
    """
    head = "Verse Fragment"
    if fragment.reading_type:  # e.g. "Qiraat Verse Fragment" for a variant reading
        head = f"{fragment.reading_type.capitalize()} {head}"
    if fragment.verses:
        first, last = fragment.verses[0], fragment.verses[-1]
        span = f"{first.number}" if first is last else f"{first.number}-{last.number}"
        head = f"{head} {first.surah.number}:{span}"
    return f"{head} ({excerpt(fragment.text)})"


def book_location(location: BookLocation) -> str:
    return f"Book Location {location.edition} {location.volume}:{location.page}"


def dataset_location(location: DatasetLocation) -> str:
    return f"Dataset Location {location.edition} {location.reference}"


def line_beginning(line: LineBeginning) -> str:
    return f"Line Beginning {line.number}"
