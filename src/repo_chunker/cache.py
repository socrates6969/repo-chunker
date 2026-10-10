"""Incremental chunk cache: skip files that have not changed since last run.

Re-chunking a repository should not re-parse files that are untouched. ChunkCache
persists each file's chunks keyed by a cheap change signal (modification time + size);
on the next run, unchanged files are served from the cache and only changed or new
files are re-parsed. Hashing every file would mean reading every file, which is the
cost this cache exists to avoid. Files with unsupported extensions are ignored.
"""
from __future__ import annotations

import json
import os
from typing import Any

from .chunker import DEFAULT_IGNORE, chunk_file, supported_extensions
from .models import Chunk


class ChunkCache:
    """A persistent, mtime+size keyed cache of file chunks."""

    def __init__(self, cache_path: str) -> None:
        self.cache_path = cache_path
        self.hits = 0
        self.misses = 0
        self._supported = set(supported_extensions())
        self._entries: dict[str, dict[str, Any]] = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, encoding="utf-8") as handle:
                    self._entries = json.load(handle)
            except (json.JSONDecodeError, OSError):
                self._entries = {}

    @staticmethod
    def _key(path: str) -> str:
        st = os.stat(path)
        return f"{st.st_mtime_ns}:{st.st_size}"

    def chunk_file(self, path: str) -> list[Chunk]:
        """Return chunks for one file, from cache when unchanged.

        Unsupported extensions are ignored (no read, no hit/miss accounting).
        """
        if os.path.splitext(path)[1] not in self._supported:
            return []
        abspath = os.path.abspath(path)
        try:
            key = self._key(path)
        except OSError:
            return chunk_file(path)
        entry = self._entries.get(abspath)
        if entry is not None and entry.get("key") == key:
            self.hits += 1
            return [Chunk.from_dict(d) for d in entry["chunks"]]
        self.misses += 1
        chunks = chunk_file(path)
        self._entries[abspath] = {"key": key, "chunks": [c.to_dict() for c in chunks]}
        return chunks

    def chunk_repo(self, root: str, ignore: set[str] | None = None) -> list[Chunk]:
        """Walk root and return chunks from every supported file, using the cache."""
        skip = DEFAULT_IGNORE if ignore is None else ignore
        out: list[Chunk] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip]
            for filename in filenames:
                out.extend(self.chunk_file(os.path.join(dirpath, filename)))
        return out

    def save(self) -> None:
        """Persist the cache to disk."""
        with open(self.cache_path, "w", encoding="utf-8") as handle:
            json.dump(self._entries, handle)