"""Benchmark: do chunks parse on their own? AST chunks vs naive line windows.

A chunk that cuts a function in half is useless context for a model, so we
measure the share of chunks that are syntactically complete on their own.
"""
from __future__ import annotations

import ast
import sys
import textwrap
from pathlib import Path

from repo_chunker import chunk_file


def naive_line_chunks(source: str, window: int = 40) -> list[str]:
    lines = source.splitlines()
    return ["\n".join(lines[i : i + window]) for i in range(0, len(lines), window)]


def parses(snippet: str) -> bool:
    try:
        ast.parse(textwrap.dedent(snippet))
        return True
    except SyntaxError:
        return False


def main(root: str = "src") -> int:
    files = list(Path(root).rglob("*.py"))
    ast_total = ast_ok = naive_total = naive_ok = 0
    for file in files:
        source = file.read_text(encoding="utf-8", errors="replace")
        for chunk in chunk_file(str(file)):
            ast_total += 1
            ast_ok += int(parses(chunk.text))
        for window in naive_line_chunks(source):
            if window.strip():
                naive_total += 1
                naive_ok += int(parses(window))

    def pct(a: int, b: int) -> float:
        return 100.0 * a / b if b else 0.0

    ast_pct = pct(ast_ok, ast_total)
    naive_pct = pct(naive_ok, naive_total)
    print(f"files scanned: {len(files)}")
    print(f"AST chunks:   {ast_ok}/{ast_total} parse standalone = {ast_pct:.1f}%")
    print(f"Naive chunks: {naive_ok}/{naive_total} parse standalone = {naive_pct:.1f}%")
    print(f"Boundary-integrity lift: +{ast_pct - naive_pct:.1f} pts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "src"))