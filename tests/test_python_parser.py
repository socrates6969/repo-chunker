"""Tests for the Python AST parser and the chunk contract."""
from __future__ import annotations

import ast
import textwrap

from repo_chunker import chunk_source

SAMPLE = """import os
from typing import List


def top_level(x: int) -> int:
    return x + 1


class Greeter:
    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self) -> str:
        return f"hi {self.name}"
"""


def test_extracts_semantic_units() -> None:
    kinds = {(c.kind, c.name) for c in chunk_source("sample.py", SAMPLE)}
    assert ("function", "top_level") in kinds
    assert ("class", "Greeter") in kinds
    assert ("method", "__init__") in kinds
    assert ("method", "greet") in kinds


def test_methods_carry_parent_and_imports() -> None:
    chunks = chunk_source("sample.py", SAMPLE)
    greet = next(c for c in chunks if c.name == "greet")
    assert greet.parent == "Greeter"
    assert "os" in greet.imports
    assert "typing.List" in greet.imports


def test_every_chunk_is_syntactically_complete() -> None:
    for chunk in chunk_source("sample.py", SAMPLE):
        ast.parse(textwrap.dedent(chunk.text))


def test_unknown_extension_returns_nothing() -> None:
    assert chunk_source("notes.txt", "hello world") == []
