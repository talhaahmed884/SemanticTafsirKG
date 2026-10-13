"""Enumerates what a set of TEI files contains: elements, nesting and attribute values.

Run it before converting a new chapter to see which tags and values occur, e.g.::

    python -m tafsirkg inventory Dataset/S001M
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable

from tafsirkg.tei.model import TeiDocument, TeiElement

# Attributes whose values are identifiers: only the number of distinct values is shown.
_IDENTIFIER_ATTRIBUTES = frozenset({"xml:id", "n", "edRef"})
# ...except on these elements, where ``n`` is a category worth listing.
_CATEGORY_N_ELEMENTS = frozenset({"p", "div"})


class TeiInventory:
    """Counts element nesting and attribute values over one or more documents."""

    def __init__(self) -> None:
        self.elements: Counter[str] = Counter()
        self.nesting: Counter[tuple[str, str]] = Counter()
        self.attribute_values: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)

    def add_documents(self, documents: Iterable[TeiDocument]) -> TeiInventory:
        for document in documents:
            for node in document.body:
                if isinstance(node, TeiElement):
                    self._add(node, parent="body")
        return self

    def _add(self, element: TeiElement, parent: str) -> None:
        tag = element.tag_name
        self.elements[tag] += 1
        self.nesting[(parent, tag)] += 1
        for name, value in element.attributes.items():
            self.attribute_values[(tag, name)][value] += 1
        for child in element.elements():
            self._add(child, parent=tag)

    def render(self) -> str:
        lines = ["Elements:"]
        lines += [f"  {tag:<10} {count}" for tag, count in self.elements.most_common()]
        lines.append("Nesting (parent > child):")
        lines += [
            f"  {parent:>9} > {child:<9} {count}" for (parent, child), count in sorted(self.nesting.items())
        ]
        lines.append("Attributes:")
        for (tag, name), values in sorted(self.attribute_values.items()):
            total = sum(values.values())
            if name in _IDENTIFIER_ATTRIBUTES and tag not in _CATEGORY_N_ELEMENTS:
                lines.append(f"  {tag}@{name}: {total} uses, {len(values)} distinct values")
                continue
            listed = ", ".join(f"{value!r}={count}" for value, count in values.most_common())
            lines.append(f"  {tag}@{name}: {listed}")
        return "\n".join(lines)
