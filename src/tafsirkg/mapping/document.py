"""Maps TEI documents (chapters, sections, paragraphs) onto domain objects.

Structure rules:

* A chapter can be spread over several files; all ``<div type="chapter" n="X">`` with
  the same ``n`` are merged into one :class:`TafsirChapter`.
* Some files close the chapter ``<div>`` right after its heading and put the sections
  after it, at body level. Such sections belong to the chapter that precedes them.
* Hadith paragraphs are numbered by ``xml:id`` (``h134``). A hadith paragraph without
  one continues the previous hadith (it typically gives another isnad for the same
  text, ending in "بمثله"/"بنحوه").
"""

from __future__ import annotations

import re
from collections import Counter

from tafsirkg.domain.model import (
    Commentary,
    Division,
    Hadith,
    Paragraph,
    Section,
    SubSection,
    TafsirChapter,
)
from tafsirkg.issues import IssueCode, IssueLog
from tafsirkg.mapping import identity
from tafsirkg.mapping.inline import InlineContentMapper
from tafsirkg.mapping.isnad import IsnadBuilder, IsnadResult
from tafsirkg.mapping.quran_quotes import QuranQuoteResolver
from tafsirkg.mapping.registry import EntityRegistry
from tafsirkg.tei import model as tei
from tafsirkg.tei.text import plain_text

_CHAPTER, _SECTION, _SUBSECTION = "chapter", "section", "subsection"
_HADITH, _NOT_HADITH = "hadith", "nothadith"
_HADITH_ID = re.compile(r"^h(\d+)$")
_LEADING_NUMBER = re.compile(r"^\s*(\d+)")
_SURAH_COUNT = 114


class TafsirMapper:
    """Accumulates the chapters of one or more TEI documents."""

    def __init__(self, registry: EntityRegistry, quotes: QuranQuoteResolver, issues: IssueLog) -> None:
        self._issues = issues
        self._registry = registry
        self._inline = InlineContentMapper(registry, quotes, issues)
        self._isnad = IsnadBuilder(registry, issues)
        self._chapters: dict[str, TafsirChapter] = {}
        self._used_ids: set[str] = set()
        self._last_hadith: Hadith | None = None
        self._continuations: Counter[str] = Counter()

    @property
    def chapters(self) -> list[TafsirChapter]:
        return list(self._chapters.values())

    def add_document(self, document: tei.TeiDocument) -> None:
        chapter: TafsirChapter | None = None
        for node in document.body:
            if isinstance(node, str):
                continue
            if not isinstance(node, tei.Division):
                self._issues.warning(
                    IssueCode.UNEXPECTED_ELEMENT,
                    f"<{node.tag_name}> directly in <body> is ignored",
                    node.source,
                )
            elif node.type == _CHAPTER:
                chapter = self._chapter(node, document)
            elif chapter is None:
                self._issues.error(
                    IssueCode.SECTION_OUTSIDE_CHAPTER,
                    f"<div type={node.type!r} n={node.n!r}> before any chapter is ignored",
                    node.source,
                )
            else:
                self._issues.info(
                    IssueCode.SECTION_OUTSIDE_CHAPTER,
                    f"<div n={node.n!r}> follows the chapter <div> instead of being inside it; "
                    f"attached to chapter {chapter.number}",
                    node.source,
                )
                chapter.subdivisions.append(self._division(node, chapter))

    # -- divisions ------------------------------------------------------------------

    def _chapter(self, element: tei.Division, document: tei.TeiDocument) -> TafsirChapter:
        number = (element.n or "").strip()
        if not number:
            number = "unnumbered"
            self._issues.error(IssueCode.DIVISION_WITHOUT_NUMBER, "chapter <div> without @n", element.source)
        chapter = self._chapters.get(number)
        if chapter is None:
            chapter = TafsirChapter(id=identity.chapter(number), source=element.source, number=number)
            if number.isdigit() and 1 <= int(number) <= _SURAH_COUNT:
                chapter.surah = self._registry.surah(int(number))
            self._chapters[number] = chapter
        chapter.language = chapter.language or element.lang
        if document.source not in chapter.sources:
            chapter.sources.append(document.source)
        self._fill(chapter, element)
        return chapter

    def _division(self, element: tei.Division, parent: Division) -> Division:
        number = (element.n or "").strip()
        if not number:
            number = f"{parent.number}.unnumbered{len(parent.subdivisions) + 1}"
            self._issues.error(
                IssueCode.DIVISION_WITHOUT_NUMBER, f"<div> without @n numbered {number}", element.source
            )
        division_type = element.type
        if division_type not in (_SECTION, _SUBSECTION):
            division_type = _SECTION if isinstance(parent, TafsirChapter) else _SUBSECTION
            self._issues.warning(
                IssueCode.UNEXPECTED_ELEMENT,
                f"<div type={element.type!r}> inside {parent.id} treated as a {division_type}",
                element.source,
            )
        if division_type == _SECTION:
            division: Division = Section(
                id=self._unique(identity.section(number), element), source=element.source, number=number
            )
            if isinstance(parent, TafsirChapter) and number.split(".")[0] != parent.number:
                self._issues.info(
                    IssueCode.SECTION_NUMBER_MISMATCH,
                    f"section {number} is inside chapter {parent.number}",
                    element.source,
                )
        else:
            division = SubSection(
                id=self._unique(identity.subsection(number), element),
                source=element.source,
                number=number,
            )
        self._fill(division, element)
        return division

    def _fill(self, division: Division, element: tei.Division) -> None:
        # A division can be filled more than once (a chapter spread over several files), so
        # positions continue from the paragraphs it already holds instead of restarting at 1.
        for child in element.elements():
            if isinstance(child, tei.Head):
                heading = plain_text(child)
                division.text = f"{division.text} {heading}".strip() if division.text else heading
                self._inline.map(division, child.children)
            elif isinstance(child, tei.Paragraph):
                ordinal = len(division.paragraphs) + 1
                division.paragraphs.append(self._paragraph(child, division, ordinal))
            elif isinstance(child, tei.Division):
                division.subdivisions.append(self._division(child, division))
            else:
                self._issues.warning(
                    IssueCode.UNEXPECTED_ELEMENT,
                    f"<{child.tag_name}> directly inside <div> is ignored",
                    child.source,
                )

    def _unique(self, resource_id: str, element: tei.TeiElement) -> str:
        if resource_id in self._used_ids:
            duplicate = f"{resource_id}/duplicate/{element.source.line}"
            self._issues.error(
                IssueCode.DUPLICATE_ID, f"{resource_id} occurs twice; renamed {duplicate}", element.source
            )
            resource_id = duplicate
        self._used_ids.add(resource_id)
        return resource_id

    # -- paragraphs -----------------------------------------------------------------

    def _paragraph(self, element: tei.Paragraph, division: Division, ordinal: int) -> Paragraph:
        isnad: IsnadResult | None = None
        paragraph: Paragraph
        if element.n == _HADITH:
            paragraph = self._hadith(element, division, ordinal)
            isnad = self._isnad.build(paragraph, element)
        else:
            if element.n != _NOT_HADITH:
                self._issues.warning(
                    IssueCode.UNKNOWN_PARAGRAPH_KIND,
                    f"<p n={element.n!r}> treated as commentary",
                    element.source,
                )
            paragraph = Commentary(
                id=self._unique(identity.commentary(division.number, ordinal), element),
                source=element.source,
                ordinal=ordinal,
            )
        paragraph.text = plain_text(element)
        paragraph.themes = self._inline.themes(element.ana, element.source)
        self._inline.map(paragraph, element.children, paragraph=paragraph, isnad=isnad)

        if not paragraph.text:
            self._issues.info(IssueCode.EMPTY_PARAGRAPH, f"{paragraph.id} has no text", element.source)
        if isinstance(paragraph, Hadith):
            self._check_hadith(paragraph, element)
        return paragraph

    def _hadith(self, element: tei.Paragraph, division: Division, ordinal: int) -> Hadith:
        match = _HADITH_ID.match(element.xml_id or "")
        if match:
            number = int(match.group(1))
            hadith = Hadith(
                id=self._unique(identity.hadith(number), element),
                source=element.source,
                ordinal=ordinal,
                number=number,
            )
            self._last_hadith = hadith
            return hadith

        if element.xml_id is not None:
            self._issues.warning(
                IssueCode.HADITH_WITHOUT_ID,
                f"xml:id={element.xml_id!r} is not of the form h<number>",
                element.source,
            )
        previous = self._last_hadith
        if previous is None:
            resource_id = identity.unnumbered_hadith(division.number, ordinal)
            self._issues.warning(
                IssueCode.HADITH_WITHOUT_ID,
                f"hadith paragraph without xml:id and no previous hadith; named {resource_id}",
                element.source,
            )
        else:
            self._continuations[previous.id] += 1
            resource_id = identity.hadith_continuation(previous.id, self._continuations[previous.id])
            self._issues.info(
                IssueCode.HADITH_WITHOUT_ID,
                f"hadith paragraph without xml:id treated as a continuation of {previous.id}",
                element.source,
            )
        return Hadith(
            id=self._unique(resource_id, element),
            source=element.source,
            ordinal=ordinal,
            continues=previous,
        )

    def _check_hadith(self, hadith: Hadith, element: tei.Paragraph) -> None:
        if not hadith.texts:
            self._issues.info(
                IssueCode.HADITH_WITHOUT_MATN,
                f"{hadith.id} has no <said>; its matn is not separated from the isnad",
                element.source,
            )
        if hadith.number is not None:
            for note in hadith.notes:
                match = _LEADING_NUMBER.match(note.text)
                if match and int(match.group(1)) != hadith.number:
                    self._issues.warning(
                        IssueCode.NOTE_NUMBER_MISMATCH,
                        f"{hadith.id}: note {note.text!r} starts with a different hadith number",
                        element.source,
                    )
