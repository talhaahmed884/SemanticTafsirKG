# SemanticTafsirKG

This project converts the TEI-annotated Arabic text of **Tafsir al-Tabari** (*Jāmiʿ al-Bayān ʿan Taʾwīl Āy al-Qurʾān*) into an **RDF knowledge graph**, using the SemanticTafsir ontology. The graph covers:
- the structure of the tafsir: chapters, sections, commentary and hadith;
- hadith narrator chains;
- quotations of the Qur'an, at verse or fragment level;
- poetry, named entities, annotated themes;
- page and line locations in the print and digital editions.

Every node records the file and line it came from.

The graph is built one surah at a time. **Surah 1 (al-Fatiha, `Dataset/S001M`) is converted.**

## Repository layout

| Path | Content |
|---|---|
| `Dataset/` | The TEI XML, one folder per surah (`S001M`, `S002A`, …). The `*.xpr` files are Oxygen XML Editor projects, not data. |
| `Ontology/SemanticTafsirOntology.owl` | The ontology (OWL 2, RDF/XML). |
| `src/tafsirkg/` | The converter, a Python package. Each sub-folder has a README. |
| `tests/` | The pytest suite. |
| `KnowledgeGraph/` | Generated graphs (`<surah>.ttl`) and data-quality reports (`<surah>.issues.csv`). |

## Setup

This needs Python 3.11 or later. Inside the project environment, run:

```bash
python -m pip install -e ".[dev]"
```

## Usage

```bash
# See which elements, nesting and attribute values a surah folder contains
python -m tafsirkg inventory Dataset/S001M

# Convert a surah folder; writes KnowledgeGraph/S001M.ttl and KnowledgeGraph/S001M.issues.csv
python -m tafsirkg build Dataset/S001M

# Several folders, another output folder, another base IRI
python -m tafsirkg build Dataset/S001M Dataset/S002A -o out --base-iri https://example.org/resource/
```

`build` prints a summary:

```
files read                2
chapters                  1
sections and subsections  20
commentary paragraphs     166
hadith paragraphs         83
narrator chains           89
narrators                 382
named entities            157
themes                    60
verses                    41
verse fragments           70
triples                   16338
issues (info)             410
issues (warning)          16
issues (error)            0
```

To load a graph into GraphDB, import `Ontology/SemanticTafsirOntology.owl` and the `.ttl` file into the same repository.

## How the conversion works

```
TEI XML ──► tei (typed node tree) ──► mapping (domain objects) ──► rdf (rdflib graph) ──► Turtle
                                         │
                                         └─► issue log ──► <surah>.issues.csv
```

| Layer | Role |
|---|---|
| `tei` | Reads the XML faithfully: typed nodes, mixed content kept in order, the source line of every element. |
| `domain` | Plain classes mirroring the ontology: `Section`, `Commentary`, `Hadith`, `NarratorChain`, `Verse`, `VerseFragment`, … |
| `mapping` | Applies the interpretation rules: document structure, isnad splitting, Qur'an quotation resolution, themes, entities and locations. An identity map ensures there is one resource per narrator, entity, theme or verse. |
| `rdf` | Writes the triples with an ontology vocabulary that fails fast and is checked against the OWL file by a test. |

The main rules:
- **Narrator chains.** A chain is the sequence of `persName` elements, and a new chain starts at every `shaykh` (Tabari's teacher). The last narrator in a chain is the root narrator, and each narrator `heardFrom` the next one.
- **Narrators.** Narrators are merged across the text only by their narrator ID (`L4883`). A narrator without an ID is kept per occurrence rather than guessed.
- **Qur'an quotations.** A quotation refers to the whole `Verse` when its text is the entire verse. Otherwise it refers to a `VerseFragment` that `isPartOfVerse` the verse. The quoted text is compared with the bundled canonical Uthmani text in a way that ignores spelling differences. Variant readings (`qiraat`) are always fragments.
- **Identifiers.** IRIs are deterministic, for example `section/1.1`, `hadith/134`, `hadith/134/chain/1/link/2`, `narrator/L4883` and `quran/verse/1/2`. Converting the same XML again produces exactly the same graph.
- **Data quality.** Irregular data is never fixed silently. Every interpretation, skip or likely annotation error is listed in the issue report with its file and line. For S001M, the warnings point to real annotation errors, such as a `</quote>` closing too late or an isnad that branches.

## Development

```bash
python -m pytest                                       # run the tests
python -m ruff check src tests                         # lint
python -m ruff format src tests                        # format
```
