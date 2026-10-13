"""Visitor base class for the TEI node tree."""

from __future__ import annotations

from typing import Any

from tafsirkg.tei.model import TeiElement, TeiNode


class TeiVisitor:
    """Dispatches each node to ``visit_<ClassName>`` (text goes to :meth:`visit_text`).

    Subclasses override only the element types they care about; everything else falls
    back to :meth:`generic_visit`, which visits the children in document order.
    """

    def visit(self, node: TeiNode) -> Any:
        if isinstance(node, str):
            return self.visit_text(node)
        method = getattr(self, f"visit_{type(node).__name__}", self.generic_visit)
        return method(node)

    def visit_children(self, element: TeiElement) -> None:
        for child in element.children:
            self.visit(child)

    def generic_visit(self, element: TeiElement) -> Any:
        self.visit_children(element)

    def visit_text(self, text: str) -> Any:
        return None
