"""Parsing of ``@ana`` theme lists."""

from __future__ import annotations

import re
from dataclasses import dataclass

# The annotators separate codes with spaces, sometimes with commas (",yes", "dua,yes").
_SEPARATORS = re.compile(r"[\s,]+")
# A flag the annotators append to many lists. Its meaning is not documented and it
# is not a theme, so it is dropped.
REVIEW_FLAG = "yes"


@dataclass(frozen=True, slots=True)
class AnaAnnotation:
    """The theme codes of one ``@ana`` value, lower-cased, in order, without duplicates."""

    codes: tuple[str, ...]
    is_irregular: bool  # commas, stray spaces, upper case or duplicates in the raw value

    @classmethod
    def parse(cls, raw: str | None) -> AnaAnnotation:
        if raw is None:
            return cls((), is_irregular=False)
        tokens = [token for token in _SEPARATORS.split(raw) if token]
        codes: list[str] = []
        for token in tokens:
            code = token.lower()
            if code != REVIEW_FLAG and code not in codes:
                codes.append(code)
        lowered = [token.lower() for token in tokens]
        is_irregular = " ".join(tokens) != raw or lowered != tokens or len(set(lowered)) != len(lowered)
        return cls(tuple(codes), is_irregular)
