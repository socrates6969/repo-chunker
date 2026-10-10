"""Rust and Java coverage for the tree-sitter backend (skipped if not installed)."""
from __future__ import annotations

import pytest

pytest.importorskip("tree_sitter_language_pack")

from repo_chunker import chunk_source  # noqa: E402

RUST = """use std::fmt;

struct Point {
    x: i32,
}

fn hello() -> i32 {
    1
}

impl Point {
    fn mag(&self) -> i32 {
        self.x
    }
}
"""

JAVA = """package p;

import java.util.List;

class Dog {
    String bark() {
        return "woof";
    }
}
"""


def test_rust() -> None:
    kinds = {(c.kind, c.name) for c in chunk_source("a.rs", RUST)}
    assert ("function", "hello") in kinds
    assert ("struct", "Point") in kinds
    assert ("method", "mag") in kinds


def test_java() -> None:
    kinds = {(c.kind, c.name) for c in chunk_source("A.java", JAVA)}
    assert ("class", "Dog") in kinds
    assert ("method", "bark") in kinds