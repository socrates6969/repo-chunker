"""repo-chunker: AST-aware semantic code chunking for RAG."""
from __future__ import annotations

from .base import Parser
from .chunker import chunk_file, chunk_repo, chunk_source, register, supported_extensions
from .context import add_parent_context
from .models import Chunk

__version__ = "0.1.0"
__all__ = [
    "add_parent_context",
    "Chunk",
    "Parser",
    "chunk_file",
    "chunk_repo",
    "chunk_source",
    "register",
    "supported_extensions",
    "__version__",
]
