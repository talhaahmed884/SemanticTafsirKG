from snippets import section_body

from tafsirkg.domain.model import Commentary, EntityKind, Hadith, Section, Segment
from tafsirkg.issues import IssueCode, Severity


def test_structure_and_identifiers(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="nothadith" ana="kalam lugha yes">قال <name role="person">أبو جعفر</name></p>'
            '<p n="hadith" xml:id="h134"><persName ana="shaykh">أ</persName></p>'
            '<p n="hadith"><persName ana="shaykh">ب</persName> بمثله</p>'
        )
    )
    (chapter,) = mapped.chapters
    (section,) = chapter.subdivisions
    commentary, hadith, continuation = section.paragraphs
    assert isinstance(section, Section) and section.id == "section/1.1" and section.text == "عنوان"
    assert isinstance(commentary, Commentary) and commentary.id == "commentary/1.1/1"
    assert [theme.code for theme in commentary.themes] == ["kalam", "lugha"]
    (person,) = commentary.mentions
    assert person.kind is EntityKind.PERSON and person.names == ["أبو جعفر"]
    assert isinstance(hadith, Hadith) and hadith.id == "hadith/134" and hadith.number == 134
    assert continuation.id == "hadith/134/continuation/1"
    assert continuation.continues is hadith and continuation.number is None
    assert mapped.codes(Severity.WARNING) == []


def test_sections_after_a_closed_chapter_div_belong_to_it(map_bodies):
    mapped = map_bodies(
        '<div type="chapter" n="1"><head type="1">تفسير الفاتحة</head></div>'
        '<div type="section" n="1.1"><head>أ</head></div>'
        '<div type="section" n="1.2"><head>ب</head></div>'
    )
    (chapter,) = mapped.chapters
    assert chapter.text == "تفسير الفاتحة"
    assert [section.number for section in chapter.subdivisions] == ["1.1", "1.2"]
    assert mapped.codes().count(IssueCode.SECTION_OUTSIDE_CHAPTER) == 2


def test_a_chapter_split_over_files_is_merged(map_bodies):
    mapped = map_bodies(
        '<div type="chapter" n="1"><div type="section" n="0.11"><head>أ</head></div></div>',
        '<div type="chapter" n="1" xml:lang="ar"><div type="section" n="1.1"><head>ب</head></div></div>',
    )
    (chapter,) = mapped.chapters
    assert [section.id for section in chapter.subdivisions] == ["section/0.11", "section/1.1"]
    assert [source.file for source in chapter.sources] == ["file0.xml", "file1.xml"]
    assert chapter.language == "ar"
    assert chapter.surah is not None and chapter.surah.number == 1
    assert IssueCode.SECTION_NUMBER_MISMATCH in mapped.codes()


def test_paragraph_positions_continue_when_a_chapter_resumes_in_another_file(map_bodies):
    mapped = map_bodies(
        '<div type="chapter" n="1"><p n="nothadith">أ</p><p n="nothadith">ب</p></div>',
        '<div type="chapter" n="1"><p n="nothadith">ج</p></div>',
    )
    (chapter,) = mapped.chapters
    assert [p.ordinal for p in chapter.paragraphs] == [1, 2, 3]
    assert [p.id for p in chapter.paragraphs] == ["commentary/1/1", "commentary/1/2", "commentary/1/3"]
    assert IssueCode.DUPLICATE_ID not in mapped.codes()


def test_commentaries_are_numbered_without_hadith(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="nothadith">أ</p>'
            '<p n="hadith" xml:id="h9"><persName ana="shaykh">ب</persName></p>'
            '<p n="nothadith">ج</p>'
            '<div type="subsection" n="1.1.1"><head>د</head><p n="nothadith">ه</p></div>'
            '<p n="nothadith">و</p>'
        )
    )
    (section,) = mapped.chapters[0].subdivisions
    # Positions mirror the XML and keep counting hadith, so identifiers stay stable.
    assert [p.ordinal for p in section.paragraphs] == [1, 2, 3, 4]
    assert [c.id for c in section.commentaries] == [
        "commentary/1.1/1",
        "commentary/1.1/3",
        "commentary/1.1/4",
    ]
    # Numbering restarts in a nested division and resumes in the parent after it.
    (subsection,) = section.subdivisions
    assert [c.id for c in subsection.commentaries] == ["commentary/1.1.1/1"]


def test_duplicate_identifiers_are_reported(map_bodies):
    mapped = map_bodies(
        section_body('<p n="hadith" xml:id="h1"><persName ana="shaykh">أ</persName></p>')
        + '<div type="chapter" n="1"><div type="section" n="1.1"><head>x</head></div></div>'
    )
    assert IssueCode.DUPLICATE_ID in mapped.codes(Severity.ERROR)
    sections = mapped.chapters[0].subdivisions
    assert sections[1].id.startswith("section/1.1/duplicate/")


def test_annotated_spans_nest(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="nothadith"><seg ana="murad"><seg ana="samiyat">الجن</seg> والإنس</seg>'
            ' <name role="other" ana="samiyat">الشيطان</name> <seg>بلا موضوع</seg></p>'
        )
    )
    (paragraph,) = mapped.chapters[0].subdivisions[0].paragraphs
    outer, themed_name, unthemed = paragraph.segments
    assert [theme.code for theme in outer.themes] == ["murad"]
    (inner,) = outer.segments
    assert isinstance(inner, Segment) and inner.text == "الجن" and inner.id.endswith("/segment/1/segment/1")
    assert [entity.names for entity in themed_name.mentions] == [["الشيطان"]]
    assert unthemed.themes == []
    assert IssueCode.SEGMENT_WITHOUT_THEME in mapped.codes()


def test_page_and_line_locations_attach_to_the_innermost_unit(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="nothadith"><lb n="178"/>نص <pb type="turki" n="1:106"/>'
            '<seg ana="lughawi">قيل <pb ed="GK" edRef="33628" n="67"/></seg></p>'
        )
    )
    (paragraph,) = mapped.chapters[0].subdivisions[0].paragraphs
    assert [line.number for line in paragraph.line_beginnings] == ["178"]
    (book,) = paragraph.book_locations
    assert (book.edition, book.volume, book.page) == ("turki", 1, 106)
    (dataset,) = paragraph.segments[0].dataset_locations
    assert (dataset.edition, dataset.reference, dataset.page) == ("GK", "33628", "67")


def test_poetry_and_additions(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="hadith" xml:id="h1"><note> 1 /2 /140 </note><persName ana="shaykh">أ</persName>'
            '<quote type="poetry"><lg><l>بيت أول</l><l>بيت ثان</l></lg></quote>'
            '<add type="parenthesis">أو قال</add></p>'
        )
    )
    (hadith,) = mapped.chapters[0].subdivisions[0].paragraphs
    (poem,) = hadith.poems
    assert poem.lines == ["بيت أول", "بيت ثان"] and poem.text == "بيت أول\nبيت ثان"
    (addition,) = hadith.additions
    assert addition.kind == "parenthesis" and addition.text == "أو قال"
    assert [note.text for note in hadith.notes] == ["1 /2 /140"]
    assert IssueCode.NOTE_NUMBER_MISMATCH not in mapped.codes()


def test_note_number_must_match_hadith_number(map_bodies):
    mapped = map_bodies(
        section_body('<p n="hadith" xml:id="h5"><note> 6 /2 </note><persName ana="shaykh">أ</persName></p>')
    )
    assert IssueCode.NOTE_NUMBER_MISMATCH in mapped.codes(Severity.WARNING)
