# Tests

Run them with `python -m pytest`. The configuration in `pyproject.toml` puts `src/` and `tests/` on the path.

- The test folders mirror the package layers (`tei/`, `domain/`, `quran/`, `mapping/`, `rdf/`). Most tests build a small TEI snippet with the helpers in `snippets.py` and the fixtures in `conftest.py`:
  - `tei_file` writes a snippet to a temporary file.
  - `map_bodies` maps one or more snippets and returns the chapters, the registry and the issues.
  - `corpus` is the bundled Qur'an text.
- `rdf/test_vocabulary.py` fails if the converter uses an ontology term that is not declared in `Ontology/SemanticTafsirOntology.owl`.
- `test_pipeline_s001m.py` runs the whole pipeline on `Dataset/S001M`. It checks the counts against the XML, that there are no errors, some graph invariants, and that a rebuild gives identical triples. When a new surah is added, add an equivalent test for it.
