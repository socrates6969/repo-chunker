"""Tests for token-budget packing."""
from __future__ import annotations

from repo_chunker import chunk_source
from repo_chunker.pack import pack

THREE = "def a():\n    return 1\n\n\ndef b():\n    return 2\n\n\ndef c():\n    return 3\n"


def test_merges_small_adjacent_into_one() -> None:
    chunks = chunk_source("m.py", THREE)
    assert len(chunks) == 3
    packed = pack(chunks, max_tokens=10_000)
    assert len(packed) == 1
    assert packed[0].kind == "packed"
    assert packed[0].start_line == 1


def test_never_merges_across_files() -> None:
    a = chunk_source("a.py", "def a():\n    return 1\n")
    b = chunk_source("b.py", "def b():\n    return 2\n")
    assert len(pack(a + b, max_tokens=10_000)) == 2


def test_splits_oversized_chunk() -> None:
    body = "\n".join(f"    x{i} = {i}" for i in range(40))
    chunks = chunk_source("big.py", f"def big():\n{body}\n")
    assert len(chunks) == 1
    packed = pack(chunks, max_tokens=5)
    assert len(packed) > 1
    assert all(p.kind.endswith(":split") for p in packed)