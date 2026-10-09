"""Core data model: a semantic code Chunk."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Chunk:
    """A logically complete unit of code (function, class, method, module)."""

    path: str
    language: str
    kind: str
    name: str
    start_line: int
    end_line: int
    text: str
    parent: str | None = None
    imports: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (JSONL-friendly)."""
        result: dict[str, Any] = asdict(self)
        return result

    @property
    def token_estimate(self) -> int:
        """Rough token count (~4 chars per token). Replace with a real tokenizer later."""
        return max(1, len(self.text) // 4)
