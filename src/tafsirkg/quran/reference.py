"""Qur'an references such as ``1:2`` or ``4:66-69``, as written in ``quote/@n``."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Surah, first verse, optional last verse. Anything after the range (the data
# sometimes has stray text there) is ignored by the caller, which reports it.
_REFERENCE = re.compile(r"^\s*(\d{1,3})\s*:\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?\s*$")


class MalformedReferenceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class QuranReference:
    surah: int
    first_verse: int
    last_verse: int

    @classmethod
    def parse(cls, value: str) -> QuranReference:
        match = _REFERENCE.match(value)
        if match is None:
            raise MalformedReferenceError(f"not a Qur'an reference: {value!r}")
        surah, first, last = match.group(1), match.group(2), match.group(3) or match.group(2)
        reference = cls(int(surah), int(first), int(last))
        if reference.first_verse > reference.last_verse:
            raise MalformedReferenceError(f"verse range runs backwards: {value!r}")
        return reference

    @property
    def is_range(self) -> bool:
        return self.first_verse != self.last_verse

    @property
    def verse_numbers(self) -> range:
        return range(self.first_verse, self.last_verse + 1)

    def __str__(self) -> str:
        if self.is_range:
            return f"{self.surah}:{self.first_verse}-{self.last_verse}"
        return f"{self.surah}:{self.first_verse}"
