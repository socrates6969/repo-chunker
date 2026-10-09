"""Registry and entry points for chunking files and repositories."""
from __future__ import annotations

import os
from collections.abc import Iterator

from .base import Parser
from .models import Chunk
from .python_parser import PythonParser

_PARSERS: dict[str, Parser] = {}

DEFAULT_IGNORE = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
    ".mypy_cache", ".ruff_cache", ".pytest_cache",
}


def register(parser: Parser) -> None:
    """Register a parser for each of its file extensions."""
    for ext in parser.extensions:
        _PARSERS[ext] = parser


register(PythonParser())


def supported_extensions() -> tuple[str, ...]:
    """Return the file extensions currently supported."""
    return tuple(sorted(_PARSERS))


def chunk_source(path: str, source: str) -> list[Chunk]:
    """Chunk in-memory source (dispatched by the extension of path)."""
    _, ext = os.path.splitext(path)
    parser = _PARSERS.get(ext)
    if parser is None:
        return []
    return parser.parse(path, source)


def chunk_file(path: str) -> list[Chunk]:
    """Read and chunk a single file."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        source = handle.read()
    return chunk_source(path, source)


def chunk_repo(root: str, ignore: set[str] | None = None) -> Iterator[Chunk]:
    """Walk root and yield chunks from every supported file."""
    skip = DEFAULT_IGNORE if ignore is None else ignore
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for filename in filenames:
            yield from chunk_file(os.path.join(dirpath, filename))
