# `tafsirkg.rdf`: domain → RDF

| File | What it does |
|---|---|
| `vocabulary.py` | Defines the ontology terms the converter uses as rdflib `DefinedNamespace`s: `ST` for `http://www.semantictafsir.com/ontology/` and `HADITH` for `http://www.semantichadith.com/ontology/`. A misspelled term raises an error immediately. `tests/rdf/test_vocabulary.py` checks that every listed term is declared in the OWL file. The `NarratorType` individuals are declared with a `#` (`…/ontology#rawi`) and are used exactly as declared. |
| `iris.py` | `IriFactory` adds the base IRI to a domain id. The default base is `http://www.semantictafsir.com/resource/`; change it with `--base-iri`. |
| `labels.py` | Holds every `rdfs:label` rule. Each node gets exactly one plain-literal label that starts with its type (`Verse 1:2`, `Chain Link 2`, `Narrator L4883: …`), so node types are recognisable when the graph is visualised. A unit owned by another unit is labelled with its type and index only (`Thematic Verse Reference 3`, not `Commentary 0.11/4 Thematic Verse Reference 3`), because its relationship to the parent already says where it belongs; the index is taken from its id. |
| `writer.py` | `GraphWriter` walks the chapters and the shared resources and adds the triples. Its module docstring lists the modelling choices that the ontology leaves open. |

To emit a new ontology term:
1. Add it to `vocabulary.py`.
2. Make sure it is declared in `Ontology/SemanticTafsirOntology.owl`.
3. Use it in `writer.py`. Declare new nodes with `GraphWriter._typed`, which adds the class and the label; add the label rule to `labels.py`.
