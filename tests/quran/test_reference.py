import pytest

from tafsirkg.quran.reference import MalformedReferenceError, QuranReference


def test_single_verse():
    reference = QuranReference.parse("15:87")
    assert (reference.surah, reference.first_verse, reference.last_verse) == (15, 87, 87)
    assert not reference.is_range
    assert str(reference) == "15:87"


def test_range_with_spaces():
    reference = QuranReference.parse(" 4:66 - 69 ")
    assert list(reference.verse_numbers) == [66, 67, 68, 69]
    assert reference.is_range


@pytest.mark.parametrize("value", ["", "1", "1:", "a:b", "1:2:3", "1:2-3 extra", "1:5-2"])
def test_malformed(value):
    with pytest.raises(MalformedReferenceError):
        QuranReference.parse(value)
