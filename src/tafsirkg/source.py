"""Pointers back into the source XML, used for traceability and issue reports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceRef:
    """A location in a source file: the file name and (when known) the line number."""

    file: str
    line: int | None = None

    def __str__(self) -> str:
        return self.file if self.line is None else f"{self.file}#L{self.line}"
