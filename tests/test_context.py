"""Parent-context enrichment."""
from __future__ import annotations

from repo_chunker import add_parent_context, chunk_source

PY = """\
class Calculator:
    def add(self, a, b):
        return a + b

def free(x):
    return x
"""


def test_method_gets_class_signature() -> None:
    chunks = chunk_source("calc.py", PY)
    enriched = add_parent_context(chunks)
    assert len(enriched) == len(chunks)
    method = next(c for c in enriched if c.name == "add")
    assert method.text.startswith("class Calculator:")
    assert "def add(self, a, b):" in method.text
    assert method.metadata["parent_context"] == "class Calculator:"


def test_top_level_unchanged() -> None:
    chunks = chunk_source("calc.py", PY)
    enriched = add_parent_context(chunks)
    free_before = next(c for c in chunks if c.name == "free")
    free_after = next(c for c in enriched if c.name == "free")
    assert free_after.text == free_before.text
    assert "parent_context" not in free_after.metadata


def test_originals_not_mutated() -> None:
    chunks = chunk_source("calc.py", PY)
    original_add = next(c for c in chunks if c.name == "add")
    before = original_add.text
    add_parent_context(chunks)
    assert original_add.text == before            # immutable: untouched