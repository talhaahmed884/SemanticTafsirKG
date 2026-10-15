from tafsirkg.domain.model import Surah, Verse, VerseFragment
from tafsirkg.rdf import labels


def test_excerpt_shortens_long_text():
    assert labels.excerpt("a b c", words=5) == "a b c"
    assert labels.excerpt("a b c d e f", words=5) == "a b c d e …"


def test_owned_label_takes_the_index_from_the_id():
    assert labels.owned("Narrator Chain", "hadith/9/chain/2") == "Narrator Chain 2"


def test_verse_fragment_labels():
    surah = Surah("quran/surah/2", 2)
    verses = [Verse(f"quran/verse/2/{n}", surah, n, "") for n in (3, 4)]
    assert labels.verse_fragment(VerseFragment("f", "نص", verses)) == "Verse Fragment 2:3-4 (نص)"
    qiraat = VerseFragment("f", "نص", verses[:1], reading_type="qiraat")
    assert labels.verse_fragment(qiraat) == "Qiraat Verse Fragment 2:3 (نص)"
    assert labels.verse_fragment(VerseFragment("f", "نص")) == "Verse Fragment (نص)"
