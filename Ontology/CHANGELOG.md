# Ontology changelog

## 2.0.0 (2026-10-15)

`owl:versionIRI` is `http://www.semantictafsir.com/ontology/2.0.0`, and `owl:priorVersion` points to the previous
release at `https://purl.org/semantictafsir`. The namespace `http://www.semantictafsir.com/ontology/` has not changed.

### Consistency

These ranges and domains made valid data contradict the disjointness axiom:

- **Removed `rdfs:range hadith:Hadith` from `st:isPartOf`.** Through its sub-property `st:isPartOfVerse`, every verse
  that a fragment belongs to was inferred to be a Hadith, which is disjoint with Verse. `st:isPartOfHadith` keeps its
  own Hadith range.
- **Removed `rdfs:domain st:Section` from `st:isAbout`, and the matching `rdfs:range st:Section` from its inverse
  `st:commentedIn`.** Chapters and subsections also say which verses they are about, and both are disjoint with Section.
- **Added `st:containsHadith`** (⊑ `st:hasPart`, range `hadith:Hadith`). A division links its hadith with this property;
  `st:containsCommentary` (range Commentary) is only for commentary, because the two classes are disjoint.

### Alignments to other vocabularies

- **The `owl:equivalentClass` / `owl:equivalentProperty` alignments are now `skos:closeMatch` links to IRIs.** These are
  the 14 class and 5 property alignments to quranontology, DBpedia, Wikidata, mlode, schema.org and Semantic Hadith.
    - Previously they were string values on built-in OWL properties that had been redeclared as annotation properties.
      They had no logical effect and put the file outside OWL 2 DL. Both redeclarations are removed.
    - `skos:closeMatch` is not used for reasoning, so it does not make the vocabularies equivalent to each other, which
      turning them into real equivalences would have done.
- **The two `skos:closeMatch` values on narrator types are now IRIs**, instead of strings.
- **The DBpedia and Wikidata targets now use their canonical `http://` IRIs.**

### CIDOC CRM alignment

- **`st:hasTheme`** is no longer ⊑ `crm:P127_has_broader_term`, which relates two types. It stays ⊑ `crm:P129_is_about`.
- **`st:isSubThemeOf`** is now ⊑ `crm:P127_has_broader_term`. It was `P127i`, which pointed the wrong way.
- **`st:hasSubTheme`**
    - It is now the inverse of `st:isSubThemeOf`, ⊑ `crm:P127i_has_narrower_term`, with domain Theme and range SubTheme.
    - It was a sub-property of `st:hasTheme`, which would have made every theme "about" its sub-themes.
- **`st:Theme` is now ⊑ `crm:E55_Type`.** Themes are concepts, and P127 relates types.
- **`st:hasNote`** is now ⊑ `crm:P67i_is_referred_to_by`. CRM's `P3_has_note` points to a literal, while notes are
  nodes. The `P3_has_note` declaration is removed.
- **The text classes are now ⊑ `crm:E33_Linguistic_Object`**, which is ⊑ E73 and declared in the file. These are Verse,
  VerseFragment, Commentary, Hadith, HadithText, Note, Poetry and AdditionalText.
    - Previously a VerseFragment (E73) was classified more specifically than the Verse it is part of (E90).
    - The structural classes (Surah, TafsirChapter, Section, SubSection, Segment, TafsirCollection) stay ⊑ E90.

### Namespace

- **The five `NarratorType` individuals moved from `…/ontology#rawi` to `…/ontology/rawi`**, the namespace of every
  other term. The same applies to `sahabi`, `shaykh`, `unknown_rawi` and `unknown_sahabi`.
- **The old IRIs are removed.** Graphs that use them must be regenerated.
- **New `NarratorType` individual `st:qari`** (label "Qari", قارئ) for a Qur'an reciter in a chain of transmission. The
  data annotates such narrators with `ana="qari"`, which had no individual before.

### Datatypes

All 18 datatype properties have an `rdfs:range`:

| Range              | Properties                                                                                                                                       |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| `xsd:integer`      | `hasChapterNo`, `hasCommentaryNo`, `hasHadithNo`, `hasPageNo`, `hasSurahNo`, `hasVerseNo`, `hasVolumeNo`                                         |
| `xsd:string`       | `hasEdition`, `hasID`, `hasReferenceNo`, `hasSectionNo` and `hasSubSectionNo` (dotted numbers such as `1.1`), `hasSubType`, `hasTime`, `hasType` |
| `xsd:language`     | `hasLanguage`                                                                                                                                    |
| `rdf:PlainLiteral` | `hasName`, `hasText` (a string with or without a language tag)                                                                                   |

No domains were added, because these properties are shared by many classes.

### New properties

| Property               | Definition                                                                                     | Inverse of                |
|------------------------|------------------------------------------------------------------------------------------------|---------------------------|
| `st:containsChapter`   | ⊑ `hasPart`, domain TafsirCollection, range TafsirChapter. Gives the chapter hierarchy a root. | (`st:isChapterOf`)        |
| `st:isChapterOf`       | ⊑ `isPartOf`                                                                                   | `containsChapter`         |
| `st:containsHadith`    | see Consistency above                                                                          |                           |
| `st:isSectionOf`       | ⊑ `isPartOf`                                                                                   | `containsSection`         |
| `st:isSubSectionOf`    | ⊑ `isPartOf`                                                                                   | `containsSubSection`      |
| `st:isVerseOf`         | ⊑ `isPartOf`                                                                                   | `containsVerse`           |
| `st:isNarratorChainOf` | ⊑ `isPartOfHadith`                                                                             | `hadith:hasNarratorChain` |

Also new:

- **`st:hasPart` and `st:isPartOf` are declared inverses.**
- **The comment on `st:containsVerse`** now says what the property is used for: a Surah to its verses.

### Labels

- **English labels:** every class, property and individual of the ontology now has an `rdfs:label` in English.
  Previously 0 of 66 properties and 3 of 41 classes had one. A new label is the term's name exactly as written in its
  IRI, without spaces (`TafsirChapter`, `containsCommentary`), so Protégé shows the same names whether it renders IRIs
  or labels. The existing labels are unchanged, such as `st:Verse` = "Ayah" and the narrator types ("Rawi", "Unknown
  Rawi", …), except `st:NarratorType`, whose label "Narrator Type" became "NarratorType".
- **Arabic labels:** these well-established terms have an Arabic label:
    - classes: Verse (آية), Surah (سورة), Hadith (حديث), HadithText (متن الحديث), NarratorChain (إسناد), HadithNarrator
      (راوي الحديث), Poetry (شعر);
    - narrator types: qari (قارئ), rawi (راوي), sahabi (صحابي), shaykh (شيخ).

### Validation

- **New `SemanticTafsirShapes.ttl`.** It holds SHACL shapes for generated graphs, covering:
    - cardinalities and datatypes;
    - every node having exactly one label;
    - every chapter belonging to a collection;
    - part-of links forming no cycles.

  Missing source annotations, such as a hadith without an isnad, are warnings. Structural errors are violations.

### Metadata

- `owl:versionInfo` is `2.0.0`.
- `dcterms:license` is now an IRI (CC BY-SA 4.0), instead of a string.
