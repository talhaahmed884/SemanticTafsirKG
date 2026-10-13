import pytest

from tafsirkg.issues import IssueCode, IssueLog
from tafsirkg.tei import model as tei
from tafsirkg.tei.inventory import TeiInventory
from tafsirkg.tei.reader import TeiFormatError, TeiReader
from tafsirkg.tei.text import plain_text


def _read(tei_file, body: str) -> tuple[tei.TeiDocument, IssueLog]:
    issues = IssueLog()
    return TeiReader(issues).read(tei_file(body)), issues


def test_typed_nodes_and_attributes(tei_file):
    document, issues = _read(
        tei_file,
        '<div type="chapter" n="1" xml:lang="ar"><p n="hadith" xml:id="h7" ana="kalam yes">x</p></div>',
    )
    (chapter,) = [node for node in document.body if isinstance(node, tei.Division)]
    (paragraph,) = list(chapter.elements())
    assert (chapter.type, chapter.n, chapter.lang) == ("chapter", "1", "ar")
    assert isinstance(paragraph, tei.Paragraph)
    assert (paragraph.n, paragraph.xml_id, paragraph.ana) == ("hadith", "h7", "kalam yes")
    assert paragraph.attributes["xml:id"] == "h7"
    assert paragraph.source.line == 1
    assert len(issues) == 0


def test_mixed_content_keeps_text_and_tails_in_order(tei_file):
    document, _ = _read(tei_file, '<p n="nothadith">قال <name role="person">أبو جعفر</name> : نعم</p>')
    (paragraph,) = document.body
    first, name, tail = paragraph.children
    assert first == "قال "
    assert isinstance(name, tei.Name) and name.role == "person"
    assert tail == " : نعم"
    assert plain_text(paragraph) == "قال أبو جعفر : نعم"


def test_plain_text_leaves_out_notes_and_separates_lines(tei_file):
    document, _ = _read(
        tei_file,
        '<p n="hadith"><note> 1 /2 </note>نص<quote type="poetry"><l>أ</l><l>ب</l></quote></p>',
    )
    (paragraph,) = document.body
    assert plain_text(paragraph) == "نص أ ب"
    note = next(node for node in paragraph.descendants() if isinstance(node, tei.Note))
    assert plain_text(note, include_notes=True) == "1 /2"


def test_unknown_element_is_kept_and_reported(tei_file):
    document, issues = _read(tei_file, '<p n="nothadith">a<foo>b</foo>c</p>')
    (paragraph,) = document.body
    unknown = next(paragraph.elements())
    assert isinstance(unknown, tei.UnknownElement) and unknown.tag_name == "foo"
    assert plain_text(paragraph) == "abc"
    assert [issue.code for issue in issues] == [IssueCode.UNKNOWN_ELEMENT]


def test_wrong_namespace_is_rejected(tmp_path):
    path = tmp_path / "broken.xml"
    path.write_text('<TEI xmlns="http://www.tei-c.org/nimankufr/1.0"><text><body/></text></TEI>')
    issues = IssueLog()
    with pytest.raises(TeiFormatError):
        TeiReader(issues).read(path)
    assert [issue.code for issue in issues] == [IssueCode.INVALID_TEI]


def test_inventory_counts_elements_nesting_and_values(tei_file):
    document, _ = _read(
        tei_file,
        '<div type="chapter" n="1"><p n="hadith"><persName ana="shaykh" n="L1">x</persName>'
        '<persName ana="rawi" n="L2">y</persName></p></div>',
    )
    inventory = TeiInventory().add_documents([document])
    assert inventory.elements["persName"] == 2
    assert inventory.nesting[("p", "persName")] == 2
    assert inventory.attribute_values[("persName", "ana")] == {"shaykh": 1, "rawi": 1}
    rendered = inventory.render()
    assert "persName@n: 2 uses, 2 distinct values" in rendered
    assert "p@n: 'hadith'=1" in rendered
