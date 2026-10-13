"""Convert the TEI-annotated Tafsir al-Tabari into an RDF knowledge graph.

The package is layered; each layer only depends on the ones listed before it:

``tafsirkg.tei``      reads TEI XML into a faithful, typed node tree.
``tafsirkg.domain``   business classes mirroring the ontology (no RDF, no XML).
``tafsirkg.quran``    canonical Qur'an text and quotation resolution.
``tafsirkg.mapping``  turns TEI nodes into domain objects.
``tafsirkg.rdf``      turns domain objects into an rdflib graph.
``tafsirkg.pipeline`` wires the layers together (used by ``tafsirkg.cli``).
"""

__version__ = "0.1.0"
