"""Markdown header-aware chunking."""
from __future__ import annotations

from repo_chunker.chunker import chunk_source
from repo_chunker.markdown_parser import MarkdownParser

DOC = """\
preface text
# Title
intro
## A
body a
### A.1
deep
## B
body b
"""

FENCED = """\
# Doc
```
code
# not a header
```
done
"""


def test_sections_and_parents() -> None:
    chunks = chunk_source("x.md", DOC)
    by_name = {c.name: c for c in chunks}
    assert "<preamble>" in by_name
    assert by_name["Title"].parent is None
    assert by_name["A"].parent == "Title"
    assert by_name["A.1"].parent == "A"       # nested under A, not Title
    assert by_name["B"].parent == "Title"     # sibling of A
    assert by_name["A.1"].metadata["level"] == 3
    assert all(c.kind == "section" for c in chunks)


def test_section_text_is_complete() -> None:
    chunks = chunk_source("x.md", DOC)
    a = next(c for c in chunks if c.name == "A")
    assert a.text.startswith("## A")
    assert "body a" in a.text
    assert "A.1" not in a.text                # subsection is its own chunk


def test_code_fence_hash_is_not_a_header() -> None:
    chunks = chunk_source("x.md", FENCED)
    names = {c.name for c in chunks}
    assert names == {"Doc"}                   # "# not a header" lives inside the fence
    assert "not a header" in chunks[0].text


def test_markdown_extension_registered() -> None:
    assert ".md" in MarkdownParser().extensions
    from repo_chunker.chunker import supported_extensions
    assert ".md" in supported_extensions()