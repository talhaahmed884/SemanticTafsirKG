# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

This project converts a hand-annotated TEI edition of **Tafsir al-Tabari** (Arabic) into an **RDF knowledge graph**. The graph uses the SemanticTafsir ontology and is meant to serve other applications as a reference and dictionary resource.

The quality bar is "as perfect as possible": correctness, traceability (every node records the file and line it came from) and validation come before speed. The owner edits the ontology in **Protégé** and loads graphs into **GraphDB**.

Graphs are built one surah folder at a time. `Dataset/S001M` (al-Fatiha) is converted; its output is in `KnowledgeGraph/`.

## Commands

The project's Python is the conda env `semantictafsirkg` (Python 3.13), which is also the PyCharm interpreter. Use `~/miniconda3/envs/semantictafsirkg/bin/python`, or activate the env first.

```bash
python -m pip install -e ".[dev]"                     # install the package plus pytest and ruff
python -m pytest                                      # all tests
python -m pytest tests/mapping/test_isnad.py          # one file
python -m pytest tests/mapping/test_isnad.py::test_single_chain   # one test
python -m ruff check src tests && python -m ruff format --check src tests
python -m tafsirkg inventory Dataset/S001M            # list elements, nesting and attribute values in a folder
python -m tafsirkg build Dataset/S001M                # write KnowledgeGraph/S001M.ttl and S001M.issues.csv
```

`build` takes several folders and has the options `-o <dir>` and `--base-iri <iri>` (default `http://www.semantictafsir.com/resource/`). After changing the converter, rebuild the graphs in `KnowledgeGraph/` and check the change in the issue counts.

## Architecture

The package is `src/tafsirkg/`. It has strict layers, and each layer imports only the layers listed before it. Every folder has a `README.md` describing its files.

```
tei/      TEI XML ──► typed node tree (reader, visitor, plain text, inventory)
domain/   business classes mirroring the ontology (no XML, no RDF)
quran/    Qur'an references (`1:2-4`) and the canonical text (resources/quran-uthmani.txt)
mapping/  TEI nodes ──► domain objects (document structure, inline content, isnad, Qur'an quotes)
rdf/      domain objects ──► rdflib Graph (fail-fast vocabulary, IRI factory, writer)
pipeline.py  facade wiring the layers together; cli.py  argparse entry point
```

Flow: `KnowledgeGraphBuilder.build(folder)` does the following:
1. `read_documents` reads the `*.xml` files in natural order (it skips `.xpr` and `.bak`).
2. `TafsirMapper.add_document` maps each file. It uses `InlineContentMapper`, `IsnadBuilder` and `QuranQuoteResolver`.
3. `EntityRegistry` holds the shared resources.
4. `GraphWriter.write` produces the graph.
5. `write_outputs` writes the Turtle file and the issue report.

Rules to keep:
- **Never fix data silently.** Every irregularity is recorded in the shared `IssueLog` (`issues.py`, with codes in `IssueCode`) and ends up in `<folder>.issues.csv` as info, warning or error. When you add an interpretation rule, add an issue code for it.
- **Identifiers are deterministic.** All id rules live in `mapping/identity.py`. Ids come from the data (section numbers, `xml:id`, narrator IDs, positions within a parent, or hashes of normalized text), never from run-wide counters. `tests/test_pipeline_s001m.py` checks that a rebuild gives identical triples.
- **Shared resources go through `EntityRegistry`.** This covers themes, named entities, narrators, surahs, verses, verse fragments and page and line locations, so there is one object per identity. Narrators are merged **only by narrator ID** (`persName/@n`). Narrators without an ID stay separate per occurrence, because names like أبيه ("his father") refer to different people. Named entities merge by kind and diacritic-free name.
- **Ontology terms go through `rdf/vocabulary.py`.** These are `DefinedNamespace`s, so a typo raises an error. `tests/rdf/test_vocabulary.py` checks that every term is declared in the OWL file.
- **Every node has one label naming its type.** All `rdfs:label` rules live in `rdf/labels.py` (`Verse 1:2`, `Chain Link 2`, `Narrator L4883: …`). Owned units are labelled with their type and index only, not their parent's label. The writer declares nodes through `_typed`, which adds both the class and the label. Labels are plain literals because they mix English and Arabic; Arabic names stay in `st:hasName`@ar. `test_pipeline_s001m.py` checks that every typed node has exactly one label.
- **Original text is kept.** Arabic text goes into the graph vocalized, as written (`@ar` literals). Normalization in `arabic.py` only builds comparison keys.
- **Tests use TEI snippets.** The fixtures are in `tests/conftest.py` and `tests/snippets.py`. Add an end-to-end test like `test_pipeline_s001m.py` for each newly converted surah.

## How the TEI is interpreted

- **Structure:** `div[@type=chapter]` → `div[@type=section][@n=s.k]` → `div[@type=subsection]`. A chapter spread over several files is merged. Some files close the chapter `<div>` right after its `<head>` and place the sections at body level; those sections belong to the preceding chapter. Section numbers can differ from the chapter: chapter 1 contains sections `0.11`–`0.16`.
- **Paragraphs:** `p[@n=nothadith]` becomes `st:Commentary`, and `p[@n=hadith]` becomes `hadith:Hadith`, numbered from `xml:id="h134"`. A hadith paragraph without `xml:id` continues the previous hadith (it gives another isnad, ending in بمثله/بنحوه). Its IRI is `hadith/<n>/continuation/<k>` and it gets `st:refersTo` pointing to the hadith it continues.
- **Paragraph numbering:** every paragraph has an `ordinal`, its position among all `<p>` of its division (hadith
  included). It is read from the division's paragraph list, so it continues when a chapter resumes in another file.
  Commentary IRIs use it (`commentary/1.2/7`). The commentary *number* (label `Commentary 6` and `st:hasCommentaryNo`)
  counts only commentary paragraphs (`Division.commentaries`), because a hadith is quoted material, not Tabari's own
  words. Numbering is per division: it starts at 1 in each section or subsection and resumes in the parent after a
  nested subsection.
- **Isnad:** made from the `persName` elements outside `said`/`quote`, in document order. A new chain starts at each `shaykh`. The last narrator is the root. Names before the first `shaykh` are mentions, not chain links. Chains naming several Companions may branch ("وعن"); they are reported but stay linear.
- **Themes:** `@ana` is split on spaces and commas and lower-cased, and the `yes` flag (meaning undocumented) is dropped. Paragraph themes go on the paragraph. A `seg`, or a `name`/`time` that has `@ana`, becomes an `st:Segment` with its themes. A themed span inside a Qur'an quotation becomes a `ThematicVerse(Fragment)Reference`. Themes are flat; there is no Theme/SubTheme hierarchy.
- **Qur'an:** `quote[@type=quran]` with `@n` refers to the `st:Verse` if the text is the whole verse, otherwise to an `st:VerseFragment` linked to it with `isPartOfVerse`. Comparison uses a consonant skeleton, so Uthmani and standard spelling match. A range with `<l n>` per verse is resolved line by line. `qiraat` quotes are always fragments with `st:hasType "qiraat"`. Quotes without `@n` (often `subtype="short"` single words) become fragments that are not linked to any verse.
- **Locations:** `pb[@type=turki][@n=vol:page]` becomes `st:BookLocation` (the print edition). `pb[@ed=GK][@edRef][@n]` becomes `st:DatasetLocation`. `lb[@n]` becomes `st:LineBeginning`. Each attaches to the innermost text unit. `note` (e.g. `"134 /3 /140 /40"`; the first number equals the hadith number and is checked) becomes `st:Note`.
- **Remaining warnings for S001M** are genuine annotation errors:
  - `</quote>` placed too late, so commentary is swallowed into the quotation;
  - branching isnads;
  - verse lines (`<l n>`) outside any `<quote>`;
  - `ana="qari sahabi"`.

## Dataset notes

- Folders are named `S<NNN><suffix>` (zero-padded surah number). The suffix (`A`, `N`, `M`, `Cat*`, …) is undocumented. `S000A MuqadimaA` is the introduction. Watch the irregular names: `S114٘M` contains an invisible U+0658, and `S005Cat NER MA` contains spaces. Always quote paths.
- `*.xpr` files are Oxygen XML Editor project files and not data. `S000A MuqadimaA/*.xml.bak` is a backup.
- `Dataset/S074N/sure_74_section_74.1-74.10.xml` is corrupted: every `s` was replaced with `imankufr`, so the TEI namespace is wrong. The reader rejects it with an `invalid-tei` error. Be careful with global find-and-replace.
- Only some `persName` elements carry a narrator ID (`L<num>`): about 209 of 502 in S001M.

## Ontology (`Ontology/SemanticTafsirOntology.owl`, RDF/XML)

- `st:` = `http://www.semantictafsir.com/ontology/`, `hadith:` = `http://www.semantichadith.com/ontology/`. It is aligned with CIDOC CRM and LRMoo and uses schema.org, Dublin Core and SKOS.
- The converter works around these known problems. The ontology file itself has not been changed.
  - `st:isPartOf` has range `hadith:Hadith`, and `isPartOfVerse` is a sub-property of it. Under OWL reasoning every `VerseFragment … isPartOfVerse` triple makes the verse a `Hadith`, which is disjoint with `Verse`, so the data becomes **inconsistent**. Expect this if reasoning with disjointness is enabled in GraphDB.
  - `Hadith` and `Commentary` are disjoint while `containsCommentary` has range `Commentary`, so sections link hadith with `st:hasPart`.
  - The `NarratorType` individuals use `…/ontology#rawi` (with a hash); the converter uses those exact IRIs. Roles outside the enumeration (`qari`) are kept as `st:hasType` literals on the chain link.
  - `owl:equivalentClass`/`owl:equivalentProperty` are redeclared as annotation properties with string values. `isSubThemeOf` maps to `crm:P127i` instead of `P127`. The datatype properties have no domains or ranges.
