"""Incremental chunk cache: hits, misses, invalidation, round-trip fidelity."""
from __future__ import annotations

import time

from repo_chunker import ChunkCache, chunk_file
from repo_chunker.models import Chunk


def test_cold_then_warm(tmp_path) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    (repo / "b.py").write_text("def b():\n    return 2\n", encoding="utf-8")
    cache_file = str(tmp_path / "cache.json")  # outside the walked tree

    cold = ChunkCache(cache_file)
    first = cold.chunk_repo(str(repo))
    cold.save()
    assert cold.misses == 2 and cold.hits == 0

    warm = ChunkCache(cache_file)
    second = warm.chunk_repo(str(repo))
    assert warm.hits == 2 and warm.misses == 0
    assert {c.name for c in first} == {c.name for c in second}


def test_change_invalidates_one_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "repo"
    repo.mkdir()
    f = repo / "a.py"
    f.write_text("def a():\n    return 1\n", encoding="utf-8")
    (repo / "b.py").write_text("def b():\n    return 2\n", encoding="utf-8")
    cache_file = str(tmp_path / "cache.json")
    c1 = ChunkCache(cache_file)
    c1.chunk_repo(str(repo))
    c1.save()

    time.sleep(0.01)
    f.write_text("def a():\n    return 999\n", encoding="utf-8")

    c2 = ChunkCache(cache_file)
    c2.chunk_repo(str(repo))
    assert c2.misses == 1   # only a.py re-parsed
    assert c2.hits == 1     # b.py served from cache


def test_cached_chunks_match_fresh(tmp_path) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "repo"
    repo.mkdir()
    p = repo / "c.py"
    p.write_text("class C:\n    def m(self):\n        return 1\n", encoding="utf-8")
    cache_file = str(tmp_path / "cache.json")
    first = ChunkCache(cache_file)
    first.chunk_repo(str(repo))
    first.save()

    warm = ChunkCache(cache_file)
    cached = warm.chunk_file(str(p))
    fresh = chunk_file(str(p))
    assert [c.to_dict() for c in cached] == [c.to_dict() for c in fresh]


def test_from_dict_round_trip() -> None:
    chunk = Chunk(
        path="x.py", language="python", kind="method", name="m",
        start_line=2, end_line=3, text="def m(self): ...",
        parent="C", imports=("import os",), metadata={"level": 1},
    )
    assert Chunk.from_dict(chunk.to_dict()) == chunk
    assert isinstance(Chunk.from_dict(chunk.to_dict()).imports, tuple)