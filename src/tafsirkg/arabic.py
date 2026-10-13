"""Arabic text normalization.

The original (vocalized) text is always what goes into the graph. The functions here
only build *keys* used to compare strings: for merging repeated mentions of an entity,
and for locating a quotation inside the canonical Qur'an text.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
# Harakat, Qur'anic annotation signs, small high letters and tatweel.
_MARKS = re.compile("[\u0610-\u061a\u064b-\u065f\u0640\u06d6-\u06ed]")
_DAGGER_ALEF = "\u0670"
_ALEF_VARIANTS = str.maketrans({"\u0671": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"})


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace (including the XML's indentation) to single spaces."""
    return _WHITESPACE.sub(" ", text).strip()


def strip_marks(text: str) -> str:
    """Remove diacritics and unify alef/yaa variants, keeping the consonantal word shapes.

    Used as the identity key for named entities, so that ``الْقُرْآنِ`` and ``القرآن``
    are the same mention.
    """
    text = unicodedata.normalize("NFC", text).replace(_DAGGER_ALEF, "")
    text = _MARKS.sub("", text).translate(_ALEF_VARIANTS)
    return collapse_whitespace(text)


_VOWEL_LETTERS_AND_HAMZA = re.compile("[اويءئؤ ]")


def quran_match_key(text: str) -> str:
    """Return the consonant skeleton of ``text``, for comparing a quotation with a verse.

    The canonical text is in Uthmani script while the TEI uses standard (imla'i)
    spelling. The two differ in how long vowels and hamza are written: ``ٱلْعَٰلَمِينَ``
    / ``الْعَالَمِينَ``, ``هَدَىٰنَا`` / ``هَدَانَا``, ``ءَاتَيْنَٰكَ`` / ``آتَيْنَاكَ``,
    ``ٱلصَّلَوٰةَ`` / ``الصَّلَاةَ``. Dropping the long-vowel letters, hamza and spaces
    makes both spellings produce the same key. The key is only used to test equality
    and containment against the verse named by ``@n``; it is never shown or stored.
    """
    return _VOWEL_LETTERS_AND_HAMZA.sub("", strip_marks(text))
