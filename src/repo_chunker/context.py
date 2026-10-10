"""Parent-context enrichment.

A method chunk in isolation (`add(a, b)`) loses the class it belongs to, which
hurts both embedding quality and human review. ``add_parent_context`` returns new
chunks in which every chunk that has a ``parent`` is prefixed with its parent's
signature line, so each unit reads as a self-contained, in-context passage. The
original chunks are left untouched (chunks are immutable); the prefix is also
recorded in ``metadata["parent_context"]`` for downstream use.
"""
from __future__ import annotations

from dataclasses import replace

from .models import Chunk


def add_parent_context(chunks: list[Chunk]) -> list[Chunk]:
    """Prefix each child chunk with its parent's signature line.

    Chunks without a resolvable parent in the same file are returned unchanged.
    """
    index: dict[tuple[str, str], Chunk] = {(c.path, c.name): c for c in chunks}
    result: list[Chunk] = []
    for chunk in chunks:
        parent = index.get((chunk.path, chunk.parent)) if chunk.parent else None
        signature = _signature(parent) if parent is not None else ""
        if signature:
            metadata = {**chunk.metadata, "parent_context": signature}
            result.append(replace(chunk, text=f"{signature}\n{chunk.text}", metadata=metadata))
        else:
            result.append(chunk)
    return result


def _signature(parent: Chunk) -> str:
    for line in parent.text.splitlines():
        if line.strip():
            return line.rstrip()
    return ""