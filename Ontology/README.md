# Ontology

| File                         | Content                                                                                                                                                                                                                                                                                                                                                                         |
|------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `SemanticTafsirOntology.owl` | The SemanticTafsir ontology (OWL 2, RDF/XML, edited in Protégé). Its namespace is `st:` = `http://www.semantictafsir.com/ontology/`, and it reuses terms of the Semantic Hadith ontology (`hadith:` = `http://www.semantichadith.com/ontology/`). It is aligned with CIDOC CRM, LRMoo and schema.org, and links to other Qur'an and hadith vocabularies with `skos:closeMatch`. |
| `SemanticTafsirShapes.ttl`   | SHACL shapes that a generated graph must satisfy. Violations are structural errors; warnings are gaps in the source annotation.                                                                                                                                                                                                                                                 |
| `CHANGELOG.md`               | What changed in each version, and why.                                                                                                                                                                                                                                                                                                                                          |
| `LICENSE`                    | The ontology and the shapes are licensed CC BY-SA 4.0.                                                                                                                                                                                                                                                                                                                          |

**The ontology states what the data means; the shapes check what the data contains.** OWL's open-world reasoning never
reports missing data, so completeness rules (for example "every hadith has a narrator chain") are shapes rather than OWL
restrictions.

When editing the ontology:

- record the change in `CHANGELOG.md`;
- raise `owl:versionInfo` and `owl:versionIRI` for a release;
- list removed or renamed terms in `CHANGELOG.md`, because graphs that use them must be regenerated.

Don't add an `rdfs:domain` or `rdfs:range` without checking every class that uses the property. In OWL these axioms
infer types, so a narrow one makes valid data contradict the disjointness axiom.
