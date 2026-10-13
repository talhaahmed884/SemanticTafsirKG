# Generated knowledge graph

This folder holds the output of `python -m tafsirkg build Dataset/<folder>`. Each surah folder produces two files:

| File | Content |
|---|---|
| `<folder>.ttl` | The RDF graph in Turtle. Its instances live under `http://www.semantictafsir.com/resource/` and use the ontology in `Ontology/SemanticTafsirOntology.owl`. |
| `<folder>.issues.csv` | The data-quality report, with columns `severity, code, file, line, message`. **info** is an irregularity handled by a documented rule. **warning** means the data is probably wrong or something could not be modelled. **error** means an element could not be converted. |

The files are generated, so don't edit them by hand. Rebuilding from unchanged XML produces the same triples.

To load a graph into GraphDB, import the ontology and the `.ttl` file into the same repository.
