from tafsirkg.quran.corpus import Match, QuranCorpus


def test_bundled_text_has_every_verse(corpus):
    assert (1, 7) in corpus
    assert (114, 6) in corpus
    assert (1, 8) not in corpus
    assert (2, 286) in corpus


def test_match(corpus):
    assert corpus.match("الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", [(1, 2)]) is Match.WHOLE_VERSE
    assert corpus.match("رَبِّ الْعَالَمِينَ", [(1, 2)]) is Match.PART_OF_VERSE
    assert corpus.match("مَالِكِ يَوْمِ الدِّينِ ، بِمَعْنَى", [(1, 4)]) is Match.NOT_FOUND


def test_match_over_a_range(corpus):
    quoted = "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ الرَّحْمَنِ الرَّحِيمِ"
    assert corpus.match(quoted, [(1, 2), (1, 3)]) is Match.WHOLE_VERSE


def test_from_file(tmp_path):
    path = tmp_path / "quran.txt"
    path.write_text("1|1|بِسْمِ ٱللَّهِ\n\n1|2|ٱلْحَمْدُ لِلَّهِ\n", encoding="utf-8")
    corpus = QuranCorpus.from_file(path)
    assert corpus.text(1, 2) == "ٱلْحَمْدُ لِلَّهِ"
