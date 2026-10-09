"""Parser protocol: turn source into a list of semantic Chunks."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import Chunk


@runtime_checkable
class Parser(Protocol):
    """A language parser that extracts semantic chunks from source."""

    language: str
    extensions: tuple[str, ...]

    def parse(self, path: str, source: str) -> list[Chunk]:
        """Return the semantic chunks found in source (originating at path)."""
        ...
