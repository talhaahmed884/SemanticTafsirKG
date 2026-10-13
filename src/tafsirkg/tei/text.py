"""Plain-text extraction from TEI mixed content."""

from __future__ import annotations

from tafsirkg.arabic import collapse_whitespace
from tafsirkg.tei.model import Line, Note, TeiNode
from tafsirkg.tei.visitor import TeiVisitor


class PlainTextExtractor(TeiVisitor):
    """Concatenates the readable text under a node.

    ``<note>`` content (hadith reference numbers) is metadata, not text, so it is left
    out unless ``include_notes`` is set. Lines are separated by a space so that the last
    word of one line does not run into the first word of the next.
    """

    def __init__(self, include_notes: bool = False) -> None:
        self._parts: list[str] = []
        self._include_notes = include_notes

    @classmethod
    def extract(cls, node: TeiNode, include_notes: bool = False) -> str:
        extractor = cls(include_notes)
        extractor.visit(node)
        return collapse_whitespace("".join(extractor._parts))

    def visit_text(self, text: str) -> None:
        self._parts.append(text)

    def visit_Note(self, element: Note) -> None:
        if self._include_notes:
            self.visit_children(element)

    def visit_Line(self, element: Line) -> None:
        self._parts.append(" ")
        self.visit_children(element)
        self._parts.append(" ")


def plain_text(node: TeiNode, include_notes: bool = False) -> str:
    return PlainTextExtractor.extract(node, include_notes)
