"""Reads TEI files into the typed node model of :mod:`tafsirkg.tei.model`."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from lxml import etree

from tafsirkg.issues import IssueCode, IssueLog
from tafsirkg.source import SourceRef
from tafsirkg.tei import model as tei

_XML_ID = f"{{{tei.XML_NAMESPACE}}}id"
_XML_LANG = f"{{{tei.XML_NAMESPACE}}}lang"

# One factory per TEI element: builds the typed node from the lxml element and the
# keyword arguments shared by all nodes (source, attributes, children).
ElementFactory = Callable[[etree._Element, dict[str, Any]], tei.TeiElement]

_FACTORIES: Mapping[str, ElementFactory] = {
    tei.Division.TAG: lambda el, kw: tei.Division(
        type=el.get("type"), n=el.get("n"), lang=el.get(_XML_LANG), **kw
    ),
    tei.Head.TAG: lambda el, kw: tei.Head(type=el.get("type"), **kw),
    tei.Paragraph.TAG: lambda el, kw: tei.Paragraph(
        n=el.get("n"), xml_id=el.get(_XML_ID), ana=el.get("ana"), **kw
    ),
    tei.Quote.TAG: lambda el, kw: tei.Quote(
        type=el.get("type"), n=el.get("n"), subtype=el.get("subtype"), **kw
    ),
    tei.LineGroup.TAG: lambda el, kw: tei.LineGroup(**kw),
    tei.Line.TAG: lambda el, kw: tei.Line(n=el.get("n"), **kw),
    tei.Seg.TAG: lambda el, kw: tei.Seg(ana=el.get("ana"), **kw),
    tei.Name.TAG: lambda el, kw: tei.Name(role=el.get("role"), ana=el.get("ana"), **kw),
    tei.PersName.TAG: lambda el, kw: tei.PersName(ana=el.get("ana"), n=el.get("n"), **kw),
    tei.Said.TAG: lambda el, kw: tei.Said(**kw),
    tei.PageBreak.TAG: lambda el, kw: tei.PageBreak(
        type=el.get("type"), ed=el.get("ed"), ed_ref=el.get("edRef"), n=el.get("n"), **kw
    ),
    tei.LineBreak.TAG: lambda el, kw: tei.LineBreak(n=el.get("n"), **kw),
    tei.Note.TAG: lambda el, kw: tei.Note(**kw),
    tei.Addition.TAG: lambda el, kw: tei.Addition(type=el.get("type"), subtype=el.get("subtype"), **kw),
    tei.Time.TAG: lambda el, kw: tei.Time(ana=el.get("ana"), **kw),
}


class TeiFormatError(ValueError):
    """The file is not a TEI document this reader can process."""


class TeiReader:
    """Parses a TEI file and builds the node tree below ``<text>/<body>``."""

    def __init__(self, issues: IssueLog) -> None:
        self._issues = issues

    def read(self, path: Path, display_name: str | None = None) -> tei.TeiDocument:
        name = display_name or path.name
        try:
            root = etree.parse(str(path)).getroot()
        except etree.XMLSyntaxError as exc:
            self._fail(f"XML is not well formed: {exc}", SourceRef(name))
        if root.tag != _qualified("TEI"):
            qname = etree.QName(root)
            namespace = qname.namespace or "no namespace"
            self._fail(
                f"root element is <{qname.localname}> in {namespace}, expected <TEI> in {tei.TEI_NAMESPACE}",
                SourceRef(name, root.sourceline),
            )
        body = root.find(f"{_qualified('text')}/{_qualified('body')}")
        if body is None:
            self._fail("document has no <text>/<body>", SourceRef(name))
        return tei.TeiDocument(
            path=path,
            source=SourceRef(name, body.sourceline),
            body=self._children(body, name),
        )

    def _fail(self, message: str, source: SourceRef) -> None:
        self._issues.error(IssueCode.INVALID_TEI, message, source)
        raise TeiFormatError(f"{source}: {message}")

    def _children(self, element: etree._Element, file_name: str) -> tuple[tei.TeiNode, ...]:
        nodes: list[tei.TeiNode] = []
        if element.text:
            nodes.append(element.text)
        for child in element:
            if isinstance(child.tag, str):  # skip comments and processing instructions
                nodes.append(self._build(child, file_name))
            if child.tail:
                nodes.append(child.tail)
        return tuple(nodes)

    def _build(self, element: etree._Element, file_name: str) -> tei.TeiElement:
        source = SourceRef(file_name, element.sourceline)
        common: dict[str, Any] = {
            "source": source,
            "attributes": {_attribute_name(key): value for key, value in element.attrib.items()},
            "children": self._children(element, file_name),
        }
        qname = etree.QName(element)
        factory = _FACTORIES.get(qname.localname) if qname.namespace == tei.TEI_NAMESPACE else None
        if factory is None:
            self._issues.warning(
                IssueCode.UNKNOWN_ELEMENT, f"element <{qname.localname}> is not modelled", source
            )
            return tei.UnknownElement(tag=qname.localname, **common)
        return factory(element, common)


def _qualified(local_name: str) -> str:
    return f"{{{tei.TEI_NAMESPACE}}}{local_name}"


def _attribute_name(key: str) -> str:
    return key.replace(f"{{{tei.XML_NAMESPACE}}}", "xml:")
