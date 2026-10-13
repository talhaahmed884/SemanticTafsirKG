import pytest

from tafsirkg.domain.annotations import AnaAnnotation


@pytest.mark.parametrize(
    ("raw", "codes", "irregular"),
    [
        (None, (), False),
        ("kalam lugha yes", ("kalam", "lugha"), False),
        ("yes kalam", ("kalam",), False),
        ("lughaterm", ("lughaterm",), False),
        (",yes", (), True),
        (" yes", (), True),
        ("dua,yes", ("dua",), True),
        ("qiraat  lugha yes ", ("qiraat", "lugha"), True),
        ("Qarimajhul yes qari", ("qarimajhul", "qari"), True),
        ("murad murad", ("murad",), True),
    ],
)
def test_parse(raw, codes, irregular):
    annotation = AnaAnnotation.parse(raw)
    assert annotation.codes == codes
    assert annotation.is_irregular is irregular
