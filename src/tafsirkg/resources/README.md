# Bundled data

`quran-uthmani.txt` is the canonical Qur'an text in Uthmani script, one verse per line in the form `surah|verse|text`, with 6,236 verses. The basmala is not repeated at the start of each surah; it is verse 1:1 of al-Fatiha only.

It is used only to:
- decide whether a quotation is a whole verse or a fragment;
- give each `st:Verse` its canonical `st:hasText`.

The format and script match the Tanzil Project's Uthmani text (tanzil.net). Confirm the source and include its license notice before publishing the graph.
