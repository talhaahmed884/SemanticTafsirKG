"""Turns the relative identifiers of domain objects into IRIs."""

from __future__ import annotations

from urllib.parse import quote

from rdflib import URIRef

DEFAULT_BASE_IRI = "http://www.semantictafsir.com/resource/"


class IriFactory:
    def __init__(self, base_iri: str = DEFAULT_BASE_IRI) -> None:
        if not base_iri.endswith(("/", "#")):
            raise ValueError(f"base IRI must end with '/' or '#': {base_iri!r}")
        self.base_iri = base_iri

    def __call__(self, resource_id: str) -> URIRef:
        return URIRef(self.base_iri + quote(resource_id, safe="/:-._~"))
