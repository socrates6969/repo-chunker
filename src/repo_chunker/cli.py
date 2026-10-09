"""Command-line interface for repo-chunker."""
from __future__ import annotations

import json
import os
from typing import Annotated

import typer

from .chunker import chunk_file, chunk_repo, supported_extensions


def main(
    path: Annotated[str, typer.Argument(help="File or repository directory to chunk.")],
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output JSONL path.")
    ] = "chunks.jsonl",
    stats: Annotated[bool, typer.Option("--stats", help="Print a summary.")] = False,
) -> None:
    """Chunk a file or repository into semantic units and write JSONL."""
    chunks = chunk_file(path) if os.path.isfile(path) else list(chunk_repo(path))
    with open(output, "w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_dict()) + "\n")
    typer.echo(f"Wrote {len(chunks)} chunks to {output}")
    if stats:
        by_kind: dict[str, int] = {}
        for chunk in chunks:
            by_kind[chunk.kind] = by_kind.get(chunk.kind, 0) + 1
        typer.echo(f"Supported extensions: {', '.join(supported_extensions())}")
        typer.echo(f"By kind: {by_kind}")


def run() -> None:
    """Entry point for the repo-chunker console script."""
    typer.run(main)


if __name__ == "__main__":
    run()