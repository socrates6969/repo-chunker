"""Python parser using the standard-library AST (no external grammar needed)."""
from __future__ import annotations

import ast

from .models import Chunk

_FuncOrClass = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


class PythonParser:
    """Extract functions, classes, and methods from Python source via ast."""

    language: str = "python"
    extensions: tuple[str, ...] = (".py",)

    def parse(self, path: str, source: str) -> list[Chunk]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        lines = source.splitlines()
        imports = _collect_imports(tree)
        chunks: list[Chunk] = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                chunks.append(_make_chunk(path, lines, node, "function", imports, None))
            elif isinstance(node, ast.ClassDef):
                chunks.append(_make_chunk(path, lines, node, "class", imports, None))
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef | ast.AsyncFunctionDef):
                        chunks.append(_make_chunk(path, lines, sub, "method", imports, node.name))
        return chunks


def _collect_imports(tree: ast.Module) -> tuple[str, ...]:
    out: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            out.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            out.extend(f"{module}.{alias.name}" if module else alias.name for alias in node.names)
    return tuple(out)


def _make_chunk(
    path: str,
    lines: list[str],
    node: _FuncOrClass,
    kind: str,
    imports: tuple[str, ...],
    parent: str | None,
) -> Chunk:
    start = node.lineno
    if node.decorator_list:
        start = min(start, min(dec.lineno for dec in node.decorator_list))
    end = node.end_lineno or node.lineno
    text = "\n".join(lines[start - 1 : end])
    return Chunk(
        path=path,
        language="python",
        kind=kind,
        name=node.name,
        start_line=start,
        end_line=end,
        text=text,
        parent=parent,
        imports=imports,
    )