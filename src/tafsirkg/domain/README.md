# `tafsirkg.domain`: the business model

These are plain Python classes that mirror the ontology. They contain no XML and no RDF. The docstring of each class names the ontology class it becomes.

| File | What it does |
|---|---|
| `model.py` | **Structure:** `TafsirChapter` → `Section` → `SubSection`, all subclasses of `Division`. **Paragraphs:** `Commentary` and `Hadith`. **Hadith parts:** `NarratorChain`, `ChainLink`, `HadithText` and `Note`. **Units of text:** `TextUnit`, the base class for anything that can carry annotations, with subclasses `Segment`, `Poetry` and `AdditionalText`. **Shared resources:** `Theme`, `NamedEntity`, `Narrator`, `Surah`, `Verse`, `VerseFragment`, `BookLocation`, `DatasetLocation` and `LineBeginning`. **`SharedResources`:** the read-only protocol that the RDF writer depends on. |
| `annotations.py` | `AnaAnnotation.parse` reads an `@ana` theme list. It accepts both comma and space separators, lower-cases the codes, removes duplicates and drops the `yes` flag. It also reports whether the raw value was irregular. |

Conventions:
- Every object has an `id`, a relative and deterministic identifier such as `hadith/134/chain/1`. The rules that build these ids live in `mapping/identity.py`.
- Shared resources are created only by `mapping/registry.py`, so there is exactly one object per identity. Every other object is owned by exactly one parent.
- Inline annotations attach to the innermost text unit. Parents reach them through `hasPart` and its sub-properties.
