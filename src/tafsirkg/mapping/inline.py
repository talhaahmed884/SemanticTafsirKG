"""Maps the inline (mixed) content of a paragraph or heading onto domain text units.

The mapper keeps a stack of open text units. An element that opens a unit (``<seg>``,
``<said>``, a poem, ``<add>``) pushes it, so annotations inside it attach to the
innermost unit; parent units reach them through ``hasPart`` and its sub-properties.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from tafsirkg.domain.annotations import AnaAnnotation
from tafsirkg.domain.model import (
    AdditionalText,
    EntityKind,
    Hadith,
    HadithText,
    NamedEntity,
    Note,
    Paragraph,
    Poetry,
    QuranTarget,
    Segment,
    TextUnit,
    ThematicVerseReference,
    Theme,
)
from tafsirkg.issues import IssueCode, IssueLog
from tafsirkg.mapping import identity
from tafsirkg.mapping.isnad import IsnadResult
from tafsirkg.mapping.quran_quotes import QuoteResolution, QuranQuoteResolver
from tafsirkg.mapping.registry import EntityRegistry
from tafsirkg.source import SourceRef
from tafsirkg.tei import model as tei
from tafsirkg.tei.text import plain_text
from tafsirkg.tei.visitor import TeiVisitor

_ENTITY_KINDS = {kind.value: kind for kind in EntityKind}
_QURAN_QUOTE_TYPES = frozenset({"quran", "qiraat"})
_POETRY = "poetry"
_PRINT_EDITION = "turki"


def _append_once(items: list, item: object) -> None:
    if item not in items:
        items.append(item)


class InlineContentMapper(TeiVisitor):
    def __init__(self, registry: EntityRegistry, quotes: QuranQuoteResolver, issues: IssueLog) -> None:
        self._registry = registry
        self._quotes = quotes
        self._issues = issues
        self._units: list[TextUnit] = []
        self._paragraph: Paragraph | None = None
        self._isnad = IsnadResult()
        self._resolutions: list[QuoteResolution] = []
        self._targets: list[list[QuranTarget]] = []
        self._poetry_depth = 0
        self._child_counts: Counter[tuple[str, str]] = Counter()

    # -- public API -------------------------------------------------------------------

    def map(
        self,
        unit: TextUnit,
        nodes: Iterable[tei.TeiNode],
        paragraph: Paragraph | None = None,
        isnad: IsnadResult | None = None,
    ) -> None:
        """Attach the annotations found in ``nodes`` to ``unit`` (and units opened inside it)."""
        self._units = [unit]
        self._paragraph = paragraph
        self._isnad = isnad or IsnadResult()
        self._resolutions, self._targets, self._poetry_depth = [], [], 0
        for node in nodes:
            self.visit(node)

    def themes(self, raw_ana: str | None, source: SourceRef) -> list[Theme]:
        """The themes of an ``@ana`` value, reporting irregular spelling of the value."""
        annotation = AnaAnnotation.parse(raw_ana)
        if annotation.is_irregular:
            self._issues.info(
                IssueCode.MALFORMED_ANA,
                f"@ana={raw_ana!r} read as {list(annotation.codes)}",
                source,
            )
        return [self._registry.theme(code) for code in annotation.codes]

    # -- unit stack -----------------------------------------------------------------

    @property
    def _current(self) -> TextUnit:
        return self._units[-1]

    def _child_id(self, parent: TextUnit, kind: str) -> str:
        self._child_counts[(parent.id, kind)] += 1
        return identity.child(parent.id, kind, self._child_counts[(parent.id, kind)])

    def _within(self, unit: TextUnit, element: tei.TeiElement) -> None:
        self._units.append(unit)
        self.visit_children(element)
        self._units.pop()

    @property
    def _in_quran_quote(self) -> bool:
        return bool(self._targets)

    # -- annotated spans ------------------------------------------------------------

    def visit_Seg(self, element: tei.Seg) -> None:
        self._annotated_span(element, element.ana, always_segment=True)

    def visit_Time(self, element: tei.Time) -> None:
        self._annotated_span(element, element.ana)

    def visit_Name(self, element: tei.Name) -> None:
        kind = _ENTITY_KINDS.get((element.role or "").strip())
        if kind is None:
            kind = EntityKind.OTHER
            self._issues.warning(
                IssueCode.UNKNOWN_ENTITY_ROLE,
                f"<name role={element.role!r}> mapped to Other",
                element.source,
            )
        text = plain_text(element)
        mention = self._registry.named_entity(kind, text) if text else None
        self._annotated_span(element, element.ana, mention=mention)

    def _annotated_span(
        self,
        element: tei.TeiElement,
        raw_ana: str | None,
        mention: NamedEntity | None = None,
        always_segment: bool = False,
    ) -> None:
        themes = self.themes(raw_ana, element.source)
        if self._in_quran_quote:
            # A themed span of a quotation tags the quoted verse, not the commentary.
            for target in self._targets[-1] if themes else ():
                self._current.thematic_references.append(
                    ThematicVerseReference(
                        id=self._child_id(self._current, "thematic-reference"),
                        source=element.source,
                        target=target,
                        text=plain_text(element),
                        themes=themes,
                    )
                )
        elif themes or always_segment:
            if not themes:
                self._issues.info(
                    IssueCode.SEGMENT_WITHOUT_THEME,
                    f"segment without theme: {plain_text(element)!r}",
                    element.source,
                )
            segment = Segment(
                id=self._child_id(self._current, "segment"),
                source=element.source,
                text=plain_text(element),
                themes=themes,
            )
            self._current.segments.append(segment)
            if mention is not None:
                segment.mentions.append(mention)
            self._within(segment, element)
            return
        if mention is not None:
            self._current.mentions.append(mention)
        self.visit_children(element)

    # -- quotations and poetry ------------------------------------------------------

    def visit_Quote(self, element: tei.Quote) -> None:
        if element.type in _QURAN_QUOTE_TYPES:
            resolution = self._quotes.resolve(element)
            for target in resolution.targets:
                _append_once(self._current.quran_references, target)
            self._resolutions.append(resolution)
            self._targets.append(resolution.targets)
            self.visit_children(element)
            self._targets.pop()
            self._resolutions.pop()
        elif element.type == _POETRY:
            self._poem(element)
        else:
            self._issues.warning(
                IssueCode.UNKNOWN_QUOTE_TYPE, f"<quote type={element.type!r}>", element.source
            )
            self.visit_children(element)

    def visit_Line(self, element: tei.Line) -> None:
        if self._resolutions:
            line_targets = self._resolutions[-1].targets_for_line(element)
            if line_targets is not None:
                self._targets.append(line_targets)
                self.visit_children(element)
                self._targets.pop()
                return
        elif self._poetry_depth == 0 and element.n is not None:
            self._issues.warning(
                IssueCode.ORPHAN_VERSE_LINE,
                f"<l n={element.n!r}> outside a Qur'an quotation; its text is kept but not linked to a verse",
                element.source,
            )
        self.visit_children(element)

    def visit_LineGroup(self, element: tei.LineGroup) -> None:
        if self._poetry_depth or self._resolutions:
            self.visit_children(element)
            return
        self._issues.info(
            IssueCode.POETRY_WITHOUT_QUOTE,
            "<lg> outside <quote type='poetry'> mapped as a poem",
            element.source,
        )
        self._poem(element)

    def _poem(self, element: tei.TeiElement) -> None:
        lines = [plain_text(line) for line in element.descendants() if isinstance(line, tei.Line)]
        poem = Poetry(
            id=self._child_id(self._current, "poetry"),
            source=element.source,
            text="\n".join(lines) if lines else plain_text(element),
            lines=lines,
        )
        self._current.poems.append(poem)
        self._poetry_depth += 1
        self._within(poem, element)
        self._poetry_depth -= 1

    # -- hadith parts ---------------------------------------------------------------

    def visit_PersName(self, element: tei.PersName) -> None:
        if id(element) not in self._isnad.in_chain:
            if id(element) not in self._isnad.mentioned_only:
                self._issues.warning(
                    IssueCode.PERSNAME_OUTSIDE_ISNAD,
                    f"<persName> {plain_text(element)!r} is not part of an isnad; kept as a person mention",
                    element.source,
                )
            self._current.mentions.append(self._registry.named_entity(EntityKind.PERSON, plain_text(element)))
        self.visit_children(element)

    def visit_Said(self, element: tei.Said) -> None:
        if not isinstance(self._paragraph, Hadith):
            self._issues.warning(
                IssueCode.MATN_OUTSIDE_HADITH,
                "<said> outside a hadith paragraph; its content is kept in the enclosing text",
                element.source,
            )
            self.visit_children(element)
            return
        matn = HadithText(
            id=self._child_id(self._paragraph, "text"),
            source=element.source,
            text=plain_text(element),
        )
        self._paragraph.texts.append(matn)
        self._within(matn, element)

    def visit_Note(self, element: tei.Note) -> None:
        if self._paragraph is None:
            self._issues.warning(
                IssueCode.UNEXPECTED_ELEMENT, "<note> outside a paragraph is ignored", element.source
            )
            return
        index = len(self._paragraph.notes) + 1
        self._paragraph.notes.append(
            Note(identity.note(self._paragraph.id, index), plain_text(element, include_notes=True))
        )

    def visit_Addition(self, element: tei.Addition) -> None:
        addition = AdditionalText(
            id=self._child_id(self._current, "addition"),
            source=element.source,
            text=plain_text(element),
            kind=element.type,
        )
        self._current.additions.append(addition)
        self._within(addition, element)

    # -- locations ------------------------------------------------------------------

    def visit_PageBreak(self, element: tei.PageBreak) -> None:
        if element.type == _PRINT_EDITION:
            volume, _, page = (element.n or "").partition(":")
            if volume.strip().isdigit() and page.strip().isdigit():
                location = self._registry.book_location(_PRINT_EDITION, int(volume), int(page))
                _append_once(self._current.book_locations, location)
                return
        elif element.ed and element.ed_ref and element.n:
            location = self._registry.dataset_location(element.ed, element.ed_ref, element.n)
            _append_once(self._current.dataset_locations, location)
            return
        self._issues.warning(
            IssueCode.MALFORMED_PAGE_BREAK,
            f"<pb> with attributes {dict(element.attributes)} not understood",
            element.source,
        )

    def visit_LineBreak(self, element: tei.LineBreak) -> None:
        if element.n:
            _append_once(self._current.line_beginnings, self._registry.line_beginning(element.n))
        else:
            self._issues.warning(IssueCode.UNEXPECTED_ELEMENT, "<lb> without @n", element.source)

    # -- elements that do not belong in inline content ------------------------------

    def generic_visit(self, element: tei.TeiElement) -> None:
        if not isinstance(element, tei.UnknownElement):  # unknown ones were reported when read
            self._issues.warning(
                IssueCode.UNEXPECTED_ELEMENT,
                f"<{element.tag_name}> inside running text; its content is kept",
                element.source,
            )
        self.visit_children(element)
