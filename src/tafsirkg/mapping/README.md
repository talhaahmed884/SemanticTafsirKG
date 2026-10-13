# `tafsirkg.mapping`: TEI → domain

This layer contains all the logic that interprets the annotations. Each module's docstring states the rules it applies.

| File | What it does |
|---|---|
| `document.py` | `TafsirMapper` maps the structure: chapters, sections and subsections, and paragraphs. It merges a chapter that is split over several files, and attaches sections that come after a closed chapter `<div>` to that chapter. It numbers hadith by `xml:id` and treats a hadith paragraph without an id as a continuation of the previous hadith. |
| `inline.py` | `InlineContentMapper` is a `TeiVisitor` over the running text. It keeps a stack of open text units and turns each element into a domain object: `<seg>`, `<name>`, `<time>`, `<quote>`, `<said>`, `<add>`, `<pb>`, `<lb>`, `<note>`. |
| `isnad.py` | `IsnadBuilder` builds narrator chains from `<persName>`. A new chain starts at each `shaykh`. Narrators inside the matn or a quotation are excluded. The last narrator is the root. |
| `quran_quotes.py` | `QuranQuoteResolver` decides whether a quotation is a whole `Verse` or a `VerseFragment`. A range with one `<l n>` per verse is resolved line by line. Variant readings (`qiraat`) are always fragments. A quotation without `@n` becomes a fragment that is not linked to any verse. |
| `registry.py` | `EntityRegistry` is the identity map for shared resources. Narrators are merged by narrator ID only, named entities by kind and normalized name, verse fragments by verse and normalized text. |
| `identity.py` | Every identifier rule in one place. Ids are derived from the data only, never from run-wide counters, so rebuilding never changes the IRIs. |

Anything irregular is reported to the shared `IssueLog` (see `tafsirkg/issues.py`) and never silently fixed.
