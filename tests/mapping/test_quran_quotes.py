from tafsirkg.domain.model import Verse, VerseFragment
from tafsirkg.issues import IssueCode, Severity

from snippets import section_body


def _paragraph(mapped):
    (paragraph,) = mapped.chapters[0].subdivisions[0].paragraphs
    return paragraph


def test_whole_verse(map_bodies):
    mapped = map_bodies(
        section_body('<p n="nothadith"><quote type="quran" n="1:2">الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ</quote></p>')
    )
    (target,) = _paragraph(mapped).quran_references
    assert isinstance(target, Verse) and target.id == "quran/verse/1/2"
    assert target.text.startswith("ٱلْحَمْدُ")
    assert target in target.surah.verses


def test_fragment_of_a_verse_is_shared_by_identical_quotations(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="nothadith"><quote type="quran" n="1:2">رَبِّ الْعَالَمِينَ</quote></p>'
            '<p n="nothadith"><quote type="quran" n="1:2">رب العالمين</quote></p>'
        )
    )
    first, second = mapped.chapters[0].subdivisions[0].paragraphs
    (fragment,) = first.quran_references
    assert isinstance(fragment, VerseFragment)
    assert [verse.id for verse in fragment.verses] == ["quran/verse/1/2"]
    assert second.quran_references == [fragment]
    assert fragment.id.startswith("quran/verse/1/2/fragment/")


def test_variant_reading(map_bodies):
    mapped = map_bodies(
        section_body('<p n="nothadith"><quote type="qiraat" n="1:4">مَلِكِ يَوْمِ الدِّينِ</quote></p>')
    )
    (fragment,) = _paragraph(mapped).quran_references
    assert isinstance(fragment, VerseFragment) and fragment.reading_type == "qiraat"
    assert fragment.verses[0].number == 4


def test_quotation_without_reference_is_kept_unlinked(map_bodies):
    mapped = map_bodies(section_body('<p n="nothadith"><quote type="quran" subtype="short">غَيْرِ</quote></p>'))
    (fragment,) = _paragraph(mapped).quran_references
    assert fragment.verses == [] and fragment.subtype == "short"
    assert fragment.id.startswith("quran/fragment/")
    assert mapped.codes(Severity.INFO) == [IssueCode.QUOTE_WITHOUT_REFERENCE]


def test_range_is_resolved_line_by_line(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="nothadith"><quote type="quran" n="1:2-3"><l n="2">رَبِّ الْعَالَمِينَ</l>'
            '<l n="3"><seg ana="sifatilahi">الرَّحْمَنِ</seg> الرَّحِيمِ</l></quote></p>'
        )
    )
    paragraph = _paragraph(mapped)
    fragment, verse = paragraph.quran_references
    assert isinstance(fragment, VerseFragment) and fragment.verses[0].number == 2
    assert isinstance(verse, Verse) and verse.number == 3
    (reference,) = paragraph.thematic_references
    assert reference.target is verse and reference.text == "الرَّحْمَنِ"
    assert [theme.code for theme in reference.themes] == ["sifatilahi"]
    assert paragraph.segments == []


def test_text_not_in_the_verse_is_reported(map_bodies):
    mapped = map_bodies(
        section_body('<p n="nothadith"><quote type="quran" n="1:4">مَالِكِ يَوْمِ الدِّينِ ، بِمَعْنَى</quote></p>')
    )
    (fragment,) = _paragraph(mapped).quran_references
    assert isinstance(fragment, VerseFragment) and fragment.verses[0].number == 4
    assert IssueCode.QUOTE_TEXT_NOT_IN_VERSE in mapped.codes(Severity.WARNING)


def test_unknown_verse_is_an_error(map_bodies):
    mapped = map_bodies(section_body('<p n="nothadith"><quote type="quran" n="1:8">نص</quote></p>'))
    (fragment,) = _paragraph(mapped).quran_references
    assert fragment.verses == []
    assert IssueCode.UNKNOWN_VERSE in mapped.codes(Severity.ERROR)


def test_heading_quotation_says_what_the_section_is_about(map_bodies):
    mapped = map_bodies(section_body("", head='<quote type="quran" n="1:2">الْحَمْدُ لِلَّهِ</quote>'))
    (section,) = mapped.chapters[0].subdivisions
    (fragment,) = section.quran_references
    assert fragment.text == "الْحَمْدُ لِلَّهِ"
