"""Markdown chunker: header-aware sectioning, pure standard library.

Documentation is a major RAG use case. Splitting a Markdown file by ATX headers
yields sections that are logically complete — a heading and the prose beneath it —
with each section's ancestor heading recorded as its parent, so retrieval returns a
coherent passage instead of an arbitrary line window. Fenced code blocks are
respected: a `#` inside a ``` or ~~~ fence is never treated as a heading.
"""
from __future__ import annotations

import re

from .models import Chunk

_HEADER = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE = re.compile(r"^\s*(```+|~~~+)")


class MarkdownParser:
    """Chunk Markdown into sections by heading, implementing the Parser protocol."""

    language = "markdown"
    extensions: tuple[str, ...] = (".md", ".markdown")

    def parse(self, path: str, source: str) -> list[Chunk]:
        lines = source.splitlines()
        headers = self._headers(lines)
        chunks: list[Chunk] = []

        # Preamble: any content before the first heading.
        first = headers[0][0] if headers else len(lines)
        if any(line.strip() for line in lines[:first]):
            chunks.append(self._section(path, "<preamble>", None, 0, 1, first, lines))

        stack: list[tuple[int, str]] = []
        for idx, (line_no, level, title) in enumerate(headers):
            end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
            while stack and stack[-1][0] >= level:
                stack.pop()
            parent = stack[-1][1] if stack else None
            chunks.append(self._section(path, title, parent, level, line_no, end, lines))
            stack.append((level, title))
        return chunks

    @staticmethod
    def _headers(lines: list[str]) -> list[tuple[int, int, str]]:
        found: list[tuple[int, int, str]] = []
        fence: str | None = None
        for i, line in enumerate(lines):
            m = _FENCE.match(line)
            if m is not None:
                marker = m.group(1)[0]
                if fence is None:
                    fence = marker
                elif marker == fence:
                    fence = None
                continue
            if fence is not None:
                continue
            h = _HEADER.match(line)
            if h is not None:
                found.append((i, len(h.group(1)), h.group(2).strip()))
        return found

    @staticmethod
    def _section(
        path: str, title: str, parent: str | None,
        level: int, start: int, end: int, lines: list[str],
    ) -> Chunk:
        return Chunk(
            path=path,
            language="markdown",
            kind="section",
            name=title or "<untitled>",
            start_line=start + 1,
            end_line=end,
            text="\n".join(lines[start:end]).strip("\n"),
            parent=parent,
            metadata={"level": level} if level else {},
        )