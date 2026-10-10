"""Token-budget packing: size semantic chunks for an embedding/context budget.

Two operations, applied in order:
  1. split any chunk whose token estimate exceeds `max_tokens` into line-granular
     pieces (a very long function becomes several embeddable pieces);
  2. merge consecutive, non-overlapping, same-file chunks whose combined estimate
     stays within `max_tokens` (tiny siblings become one chunk).

The token counter is pluggable; the default is a ~4-chars-per-token estimate.
Packing assumes a flat chunk list and never merges a chunk with one it contains:
a chunk is only merged with another that starts strictly after it ends.
"""
from __future__ import annotations

from collections.abc import Callable

from .models import Chunk

TokenCounter = Callable[[str], int]


def _default_count(text: str) -> int:
    return max(1, len(text) // 4)


def _piece(chunk: Chunk, lines: list[str], start: int, end: int, part: int) -> Chunk:
    return Chunk(
        path=chunk.path,
        language=chunk.language,
        kind=f"{chunk.kind}:split",
        name=f"{chunk.name}#{part}",
        start_line=start,
        end_line=max(start, end),
        text="\n".join(lines),
        parent=chunk.parent,
        imports=chunk.imports,
    )


def _split(chunk: Chunk, max_tokens: int, count: TokenCounter) -> list[Chunk]:
    pieces: list[Chunk] = []
    buf: list[str] = []
    part = 1
    line_no = chunk.start_line
    buf_start = chunk.start_line
    for line in chunk.text.split("\n"):
        if buf and count("\n".join([*buf, line])) > max_tokens:
            pieces.append(_piece(chunk, buf, buf_start, line_no - 1, part))
            part += 1
            buf = [line]
            buf_start = line_no
        else:
            buf.append(line)
        line_no += 1
    if buf:
        pieces.append(_piece(chunk, buf, buf_start, line_no - 1, part))
    return pieces


def _merge(a: Chunk, b: Chunk) -> Chunk:
    return Chunk(
        path=a.path,
        language=a.language,
        kind="packed",
        name=f"{a.name}+{b.name}",
        start_line=a.start_line,
        end_line=b.end_line,
        text=f"{a.text}\n\n{b.text}",
        parent=None,
        imports=tuple(dict.fromkeys((*a.imports, *b.imports))),
        metadata={"packed": True},
    )


def pack(chunks: list[Chunk], max_tokens: int, count: TokenCounter | None = None) -> list[Chunk]:
    """Split oversized chunks, then merge tiny adjacent same-file chunks, to `max_tokens`."""
    counter = count or _default_count
    staged: list[Chunk] = []
    for chunk in chunks:
        if counter(chunk.text) <= max_tokens:
            staged.append(chunk)
        else:
            staged.extend(_split(chunk, max_tokens, counter))
    out: list[Chunk] = []
    for chunk in staged:
        merge = (
            bool(out)
            and out[-1].path == chunk.path
            and chunk.start_line > out[-1].end_line
            and counter(f"{out[-1].text}\n\n{chunk.text}") <= max_tokens
        )
        if merge:
            out[-1] = _merge(out[-1], chunk)
        else:
            out.append(chunk)
    return out