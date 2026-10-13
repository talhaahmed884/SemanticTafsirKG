import pytest

from tafsirkg.arabic import collapse_whitespace, quran_match_key, strip_marks


def test_collapse_whitespace_removes_indentation():
    assert collapse_whitespace("  قَالَ\n\t\t  أَبُو  جَعْفَرٍ ") == "قَالَ أَبُو جَعْفَرٍ"


def test_strip_marks_merges_vocalized_and_plain_spellings():
    assert strip_marks("الْقُرْآنِ") == strip_marks("القرآن") == "القران"
    assert strip_marks("عَلَى") == strip_marks("على")


@pytest.mark.parametrize(
    ("uthmani", "imlai"),
    [
        ("ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ", "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"),
        ("ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", "الرَّحْمَنِ الرَّحِيمِ"),
        ("ٱلَّذِى هَدَىٰنَا لِهَٰذَا", "الَّذِي هَدَانَا لِهَذَا"),
        ("وَلَقَدْ ءَاتَيْنَٰكَ", "وَلَقَدْ آتَيْنَاكَ"),
        ("بَنِىٓ إِسْرَٰٓءِيلَ", "بَنِي إِسْرَائِيلَ"),
        ("ٱلصَّلَوٰةَ", "الصَّلَاةَ"),
    ],
)
def test_quran_match_key_ignores_uthmani_orthography(uthmani, imlai):
    assert quran_match_key(uthmani) == quran_match_key(imlai)


def test_quran_match_key_still_distinguishes_different_words():
    assert quran_match_key("الْحَمْدُ لِلَّهِ") != quran_match_key("الشُّكْرُ لِلَّهِ")
