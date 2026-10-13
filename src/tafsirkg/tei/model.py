"""A faithful, typed model of the TEI elements used in the dataset.

Each class corresponds to one TEI element and exposes the attributes the converter
relies on as typed fields. Every element also keeps all of its raw ``attributes`` so
that nothing in the XML is lost, and its ``source`` (file and line) for issue reports.

Mixed content is kept in order: ``children`` holds both child elements and the text
between them (as ``str``). Elements compare by identity, so two textually identical
``persName`` elements in different places are still different nodes.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from tafsirkg.source import SourceRef

TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"
XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"


@dataclass(frozen=True, eq=False, kw_only=True)
class TeiElement:
    TAG: ClassVar[str] = ""

    source: SourceRef
    attributes: Mapping[str, str] = field(default_factory=dict)
    children: tuple[TeiNode, ...] = ()

    @property
    def tag_name(self) -> str:
        """The TEI element name, e.g. ``persName``."""
        return self.TAG

    def elements(self) -> Iterator[TeiElement]:
        """Direct child elements, skipping text."""
        return (child for child in self.children if isinstance(child, TeiElement))

    def descendants(self) -> Iterator[TeiElement]:
        """All descendant elements in document order."""
        for child in self.elements():
            yield child
            yield from child.descendants()


TeiNode = TeiElement | str


@dataclass(frozen=True, eq=False, kw_only=True)
class Division(TeiElement):
    """``<div>``: a chapter, section or subsection."""

    TAG: ClassVar[str] = "div"

    type: str | None = None
    n: str | None = None
    lang: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class Head(TeiElement):
    """``<head>``: the heading of a division."""

    TAG: ClassVar[str] = "head"

    type: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class Paragraph(TeiElement):
    """``<p>``: ``n`` is ``hadith`` or ``nothadith``; ``ana`` holds theme codes."""

    TAG: ClassVar[str] = "p"

    n: str | None = None
    xml_id: str | None = None
    ana: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class Quote(TeiElement):
    """``<quote>``: ``type`` is ``quran``, ``qiraat`` or ``poetry``; ``n`` is e.g. ``1:2-4``."""

    TAG: ClassVar[str] = "quote"

    type: str | None = None
    n: str | None = None
    subtype: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class LineGroup(TeiElement):
    """``<lg>``: a group of lines (a verse of poetry)."""

    TAG: ClassVar[str] = "lg"


@dataclass(frozen=True, eq=False, kw_only=True)
class Line(TeiElement):
    """``<l>``: a line of poetry, or one Qur'an verse (with ``n``) inside a quotation."""

    TAG: ClassVar[str] = "l"

    n: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class Seg(TeiElement):
    """``<seg>``: an annotated span; ``ana`` holds theme codes."""

    TAG: ClassVar[str] = "seg"

    ana: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class Name(TeiElement):
    """``<name>``: a named-entity mention; ``role`` is person, location, organization, time, other."""

    TAG: ClassVar[str] = "name"

    role: str | None = None
    ana: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class PersName(TeiElement):
    """``<persName>``: a narrator in an isnad; ``ana`` is the narrator role, ``n`` the narrator ID."""

    TAG: ClassVar[str] = "persName"

    ana: str | None = None
    n: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class Said(TeiElement):
    """``<said>``: the matn (text) of a hadith."""

    TAG: ClassVar[str] = "said"


@dataclass(frozen=True, eq=False, kw_only=True)
class PageBreak(TeiElement):
    """``<pb>``: a page break in the print edition (``type``) or the digital edition (``ed``)."""

    TAG: ClassVar[str] = "pb"

    type: str | None = None
    ed: str | None = None
    ed_ref: str | None = None
    n: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class LineBreak(TeiElement):
    """``<lb>``: a line beginning."""

    TAG: ClassVar[str] = "lb"

    n: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class Note(TeiElement):
    """``<note>``: reference numbers attached to a hadith, e.g. ``119 /2 /140``."""

    TAG: ClassVar[str] = "note"


@dataclass(frozen=True, eq=False, kw_only=True)
class Addition(TeiElement):
    """``<add>``: an editorial addition, e.g. ``type="parenthesis"``."""

    TAG: ClassVar[str] = "add"

    type: str | None = None
    subtype: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class Time(TeiElement):
    """``<time>``: carries asbab al-nuzul codes in ``ana`` (e.g. ``aball``)."""

    TAG: ClassVar[str] = "time"

    ana: str | None = None


@dataclass(frozen=True, eq=False, kw_only=True)
class UnknownElement(TeiElement):
    """Any element the model does not know. Kept so its content is not lost."""

    tag: str

    @property
    def tag_name(self) -> str:
        return self.tag


@dataclass(frozen=True, eq=False, kw_only=True)
class TeiDocument:
    """One TEI file: the top-level ``<div>`` elements of its ``<body>``."""

    path: Path
    source: SourceRef
    body: tuple[TeiNode, ...]
