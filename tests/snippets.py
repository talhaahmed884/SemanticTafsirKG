"""TEI snippet helpers for tests."""

TEI_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/>'
    '<text xml:lang="ar"><body>{body}</body></text></TEI>'
)


def section_body(paragraphs: str, head: str = "عنوان", number: str = "1.1") -> str:
    """A chapter 1 containing one section with the given paragraphs."""
    return (
        f'<div type="chapter" n="1"><div type="section" n="{number}">'
        f'<head type="30">{head}</head>{paragraphs}</div></div>'
    )
