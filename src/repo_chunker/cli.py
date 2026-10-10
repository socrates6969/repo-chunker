"""Command-line interface for repo-chunker."""
from __future__ import annotations

import json
import os
import sys
from typing import Annotated

import typer

from .chunker import chunk_file, chunk_repo, chunk_source, supported_extensions
from .context import add_parent_context
from .models import Chunk
from .pack import pack


def _collect(path: str, stdin_name: str) -> list[Chunk]:
    if path == "-":
        return chunk_source(stdin_name, sys.stdin.read())
    if os.path.isfile(path):
        return chunk_file(path)
    return list(chunk_repo(path))


def _serialize(chunks: list[Chunk], fmt: str) -> str:
    rows = [c.to_dict() for c in chunks]
    if fmt == "json":
        return json.dumps(rows, indent=2)
    return "\n".join(json.dumps(row) for row in rows)


def main(
    path: Annotated[
        str, typer.Argument(help="File or repo directory to chunk, or '-' for stdin.")
    ],
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output path, or '-' for stdout.")
    ] = "chunks.jsonl",
    fmt: Annotated[
        str, typer.Option("--format", help="Output format: 'jsonl' or 'json'.")
    ] = "jsonl",
    max_tokens: Annotated[
        int, typer.Option("--max-tokens", help="If > 0, pack chunks up to this token budget.")
    ] = 0,
    context: Annotated[
        bool, typer.Option("--context", help="Prefix each child chunk with its parent signature.")
    ] = False,
    stdin_name: Annotated[
        str, typer.Option("--stdin-name", help="Filename used to pick a parser when reading stdin.")
    ] = "stdin.py",
    stats: Annotated[bool, typer.Option("--stats", help="Print a summary to stderr.")] = False,
) -> None:
    """Chunk a file, repository, or stdin into semantic units."""
    if fmt not in ("jsonl", "json"):
        raise typer.BadParameter("format must be 'jsonl' or 'json'")
    chunks = _collect(path, stdin_name)
    if context:
        chunks = add_parent_context(chunks)
    if max_tokens > 0:
        chunks = pack(chunks, max_tokens)

    payload = _serialize(chunks, fmt)
    if output == "-":
        sys.stdout.write(payload + "\n" if payload else "")
    else:
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(payload + ("\n" if payload and fmt == "jsonl" else ""))
        typer.echo(f"Wrote {len(chunks)} chunks to {output}", err=True)

    if stats:
        by_kind: dict[str, int] = {}
        for chunk in chunks:
            by_kind[chunk.kind] = by_kind.get(chunk.kind, 0) + 1
        typer.echo(f"Supported extensions: {', '.join(supported_extensions())}", err=True)
        typer.echo(f"By kind: {by_kind}", err=True)


def run() -> None:
    """Entry point for the repo-chunker console script."""
    typer.run(main)


if __name__ == "__main__":
    run()