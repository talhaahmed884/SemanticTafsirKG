# `tafsirkg.quran`: Qur'an references and canonical text

| File | What it does |
|---|---|
| `reference.py` | `QuranReference.parse("4:66-69")` parses the `@n` of a quotation. Malformed values raise `MalformedReferenceError`. |
| `corpus.py` | `QuranCorpus` holds the canonical verse texts (`QuranCorpus.bundled()` loads `resources/quran-uthmani.txt`). `match()` says whether a quotation is the whole verse, part of it, or not found in it. |

The canonical text is in Uthmani script, while the TEI uses standard spelling. The comparison uses `arabic.quran_match_key`, a consonant skeleton that drops diacritics, long-vowel letters, hamza and spaces. It is only used to compare against the verse that `@n` names, never to guess a verse from its text.
