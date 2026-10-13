from tafsirkg.domain.model import Hadith, NarratorRole
from tafsirkg.issues import IssueCode

from snippets import section_body


def _hadiths(mapped) -> list[Hadith]:
    (section,) = mapped.chapters[0].subdivisions
    return [paragraph for paragraph in section.paragraphs if isinstance(paragraph, Hadith)]


def test_single_chain(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="hadith" xml:id="h1">حدثنا <persName ana="shaykh" n="L1">يونس</persName> عن '
            '<persName ana="rawi">ابن وهب</persName> عن <persName ana="sahabi" n="L3">أبي هريرة</persName> '
            "قال : <said>هي أم القرآن</said></p>"
        )
    )
    (hadith,) = _hadiths(mapped)
    (chain,) = hadith.chains
    assert [link.narrator.names[0] for link in chain.links] == ["يونس", "ابن وهب", "أبي هريرة"]
    assert [link.position for link in chain.links] == [1, 2, 3]
    assert chain.root.narrator.narrator_id == "L3" and chain.root.narrator.is_root
    assert chain.links[0].narrator.roles == {NarratorRole.SHAYKH}
    assert chain.id == "hadith/1/chain/1"
    assert [text.text for text in hadith.texts] == ["هي أم القرآن"]
    assert IssueCode.NARRATOR_WITHOUT_ID in mapped.codes()


def test_new_chain_starts_at_each_shaykh(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="hadith" xml:id="h2"><persName ana="shaykh">أ</persName> <persName ana="rawi">ب</persName>'
            ' وحدثنا <persName ana="shaykh">ج</persName> <persName ana="rawi">د</persName>'
            ' <persName ana="sahabi">هـ</persName></p>'
        )
    )
    (hadith,) = _hadiths(mapped)
    assert [[link.narrator.names[0] for link in chain.links] for chain in hadith.chains] == [
        ["أ", "ب"],
        ["ج", "د", "هـ"],
    ]


def test_narrator_before_first_shaykh_is_a_mention(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="hadith" xml:id="h3">وقال <seg ana="khilafaumar"><persName ana="sahabi">عمر</persName>'
            ' قولا</seg> ، حدثنا بذلك <persName ana="shaykh">يونس</persName> عن '
            '<persName ana="sahabi" n="L5">عمر</persName></p>'
        )
    )
    (hadith,) = _hadiths(mapped)
    (chain,) = hadith.chains
    assert [link.narrator.names[0] for link in chain.links] == ["يونس", "عمر"]
    (segment,) = hadith.segments
    assert [entity.names for entity in segment.mentions] == [["عمر"]]
    assert IssueCode.NARRATOR_BEFORE_CHAIN in mapped.codes()
    assert IssueCode.PERSNAME_OUTSIDE_ISNAD not in mapped.codes()


def test_role_outside_enumeration_is_kept_on_the_link(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="hadith" xml:id="h4"><persName ana="shaykh">أ</persName>'
            ' <persName ana="qari sahabi" n="L9">ابن عباس</persName></p>'
        )
    )
    (hadith,) = _hadiths(mapped)
    root = hadith.chains[0].root
    assert root.role_tokens == ("qari", "sahabi")
    assert root.narrator.roles == {NarratorRole.SAHABI}
    assert IssueCode.UNKNOWN_NARRATOR_ROLE in mapped.codes()


def test_narrators_merge_by_id_but_not_by_name(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="hadith" xml:id="h5"><persName ana="shaykh">أبو كريب</persName>'
            ' <persName ana="sahabi" n="L4883">ابن عباس</persName></p>'
            '<p n="hadith" xml:id="h6"><persName ana="shaykh">أبو كريب</persName>'
            ' <persName ana="sahabi" n="L4883">عبد الله بن عباس</persName></p>'
        )
    )
    first, second = _hadiths(mapped)
    assert first.chains[0].root.narrator is second.chains[0].root.narrator
    assert first.chains[0].root.narrator.names == ["ابن عباس", "عبد الله بن عباس"]
    assert first.chains[0].links[0].narrator is not second.chains[0].links[0].narrator


def test_branching_chain_is_reported(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="hadith" xml:id="h7"><persName ana="shaykh">أ</persName>'
            ' <persName ana="sahabi">ب</persName> وعن <persName ana="sahabi">ج</persName></p>'
        )
    )
    assert IssueCode.POSSIBLE_BRANCHING_CHAIN in mapped.codes()


def test_names_inside_the_matn_are_not_narrators(map_bodies):
    mapped = map_bodies(
        section_body(
            '<p n="hadith" xml:id="h8"><persName ana="shaykh">أ</persName> قال '
            '<said>سمعت <persName ana="rawi">ب</persName></said></p>'
        )
    )
    (hadith,) = _hadiths(mapped)
    assert len(hadith.chains[0].links) == 1
    assert [entity.names for entity in hadith.texts[0].mentions] == [["ب"]]
    assert IssueCode.PERSNAME_OUTSIDE_ISNAD in mapped.codes()
