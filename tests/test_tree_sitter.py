"""Tests for the tree-sitter multi-language backend (skipped if not installed)."""
from __future__ import annotations

import pytest

pytest.importorskip("tree_sitter_language_pack")

from repo_chunker import chunk_source  # noqa: E402

JS = """import {a} from "x";

function greet(name) {
  return "hi " + name;
}

class Dog {
  bark() {
    return "woof";
  }
}
"""

TS = """interface Shape {
  area(): number;
}

function area(s: Shape): number {
  return s.area();
}
"""

GO = """package main

import "fmt"

type Point struct {
  X int
}

func Hello() string {
  return "hi"
}
"""


def test_javascript() -> None:
    kinds = {(c.kind, c.name) for c in chunk_source("a.js", JS)}
    assert ("function", "greet") in kinds
    assert ("class", "Dog") in kinds
    assert ("method", "bark") in kinds
    greet = next(c for c in chunk_source("a.js", JS) if c.name == "greet")
    assert greet.language == "javascript"
    assert greet.path == "a.js"


def test_typescript_interface() -> None:
    kinds = {(c.kind, c.name) for c in chunk_source("a.ts", TS)}
    assert ("interface", "Shape") in kinds
    assert ("function", "area") in kinds


def test_go() -> None:
    kinds = {(c.kind, c.name) for c in chunk_source("a.go", GO)}
    assert ("function", "Hello") in kinds
    assert ("type", "Point") in kinds