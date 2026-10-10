"""v2.0 language coverage: C, C++, C#, Ruby, PHP, Kotlin via tree-sitter."""
from __future__ import annotations

import pytest

pytest.importorskip("tree_sitter_language_pack")

from repo_chunker.chunker import chunk_source  # noqa: E402

C_SRC = """\
#include <stdio.h>
struct Point { int x; int y; };
enum Color { RED, GREEN };
typedef int Myint;
int add(int a, int b) { return a + b; }
"""

CPP_SRC = """\
#include <vector>
namespace ns { int helper() { return 1; } }
class Widget {
public:
  void render();
  int size() const { return 0; }
};
struct Pod { int x; };
int add(int a, int b) { return a + b; }
"""

CSHARP_SRC = """\
using System;
namespace App {
  public class Calculator {
    public int Add(int a, int b) { return a + b; }
    public int Value { get; set; }
  }
  public interface IShape { double Area(); }
  public struct Point { public int X; }
  public enum Color { Red, Green }
}
"""

RUBY_SRC = """\
require 'set'
def top_level(a)
  a + 1
end
class Calculator
  def add(a, b)
    a + b
  end
end
module Utils
  def self.helper
  end
end
"""

PHP_SRC = """\
<?php
namespace App;
use Foo\\Bar;
function topLevel($a) { return $a; }
class Calculator {
  public function add($a, $b) { return $a + $b; }
}
interface Shape { public function area(); }
trait T { public function x() {} }
"""

KOTLIN_SRC = """\
package app
import kotlin.math.max
fun topLevel(a: Int): Int = a + 1
class Calculator {
  fun add(a: Int, b: Int): Int = a + b
}
interface Shape { fun area(): Double }
"""


def _pairs(path: str, src: str) -> set[tuple[str, str]]:
    return {(c.kind, c.name) for c in chunk_source(path, src)}


def test_c() -> None:
    pairs = _pairs("x.c", C_SRC)
    assert ("function", "add") in pairs
    assert ("struct", "Point") in pairs
    assert ("enum", "Color") in pairs
    assert ("type", "Myint") in pairs


def test_cpp() -> None:
    pairs = _pairs("x.cpp", CPP_SRC)
    assert ("function", "add") in pairs
    assert ("class", "Widget") in pairs
    assert ("method", "size") in pairs          # inline method, found in class body
    assert ("struct", "Pod") in pairs
    assert ("function", "helper") in pairs       # inside namespace -> container recursion


def test_csharp() -> None:
    pairs = _pairs("x.cs", CSHARP_SRC)           # all nested inside a namespace
    assert ("class", "Calculator") in pairs
    assert ("method", "Add") in pairs
    assert ("property", "Value") in pairs
    assert ("interface", "IShape") in pairs
    assert ("struct", "Point") in pairs
    assert ("enum", "Color") in pairs


def test_ruby() -> None:
    pairs = _pairs("x.rb", RUBY_SRC)
    assert ("function", "top_level") in pairs
    assert ("class", "Calculator") in pairs
    assert ("method", "add") in pairs
    assert ("function", "helper") in pairs       # singleton method inside a module


def test_php() -> None:
    pairs = _pairs("x.php", PHP_SRC)
    assert ("function", "topLevel") in pairs
    assert ("class", "Calculator") in pairs
    assert ("method", "add") in pairs
    assert ("interface", "Shape") in pairs
    assert ("trait", "T") in pairs


def test_kotlin() -> None:
    pairs = _pairs("x.kt", KOTLIN_SRC)
    assert ("function", "topLevel") in pairs
    assert ("class", "Calculator") in pairs
    assert ("method", "add") in pairs


def test_new_extensions_registered() -> None:
    from repo_chunker.chunker import supported_extensions
    exts = supported_extensions()
    for ext in (".c", ".cpp", ".cs", ".rb", ".php", ".kt"):
        assert ext in exts