"""Every ontology term the converter emits must be declared in the ontology file."""

from pathlib import Path

import pytest
from rdflib import OWL, RDF, Graph, URIRef

from tafsirkg.domain.model import EntityKind, NarratorRole
from tafsirkg.rdf.vocabulary import ENTITY_CLASSES, HADITH, NARRATOR_TYPE_IRIS, ST

ONTOLOGY = Path(__file__).resolve().parents[2] / "Ontology" / "SemanticTafsirOntology.owl"
DECLARATIONS = (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.NamedIndividual)


@pytest.fixture(scope="module")
def declared() -> set[URIRef]:
    graph = Graph().parse(ONTOLOGY, format="xml")
    return {subject for kind in DECLARATIONS for subject in graph.subjects(RDF.type, kind)}


@pytest.mark.parametrize("namespace", [ST, HADITH])
def test_terms_are_declared(namespace, declared):
    terms = {namespace[name] for name in namespace.__annotations__}
    assert terms - declared == set()


def test_narrator_types_are_the_ontology_individuals(declared):
    assert set(NARRATOR_TYPE_IRIS) == set(NarratorRole)
    assert set(NARRATOR_TYPE_IRIS.values()) <= declared


def test_every_entity_kind_has_a_class():
    assert set(ENTITY_CLASSES) == set(EntityKind)
