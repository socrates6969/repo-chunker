# repo-chunker

**AST-aware semantic code chunking for RAG.** Splits a codebase into *logically complete* units — functions, classes, methods, interfaces, types — instead of arbitrary line or character windows, so a retrieval model receives the exact relevant code, not a function cut in half or a blob of three unrelated ones.

[![ci](https://github.com/socrates6969/repo-chunker/actions/workflows/ci.yml/badge.svg)](https://github.com/socrates6969/repo-chunker/actions)

## Why it is better (measured, not claimed)

`benchmarks/retrieval_eval.py` compares AST chunks to naive line windows on a controlled corpus with a dependency-free lexical embedder:

| metric | AST (repo-chunker) | naive line windows |
|---|---|---|
| exact-unit retrieval @1 | **100%** | 0% |
| top-1 on-target purity | **100%** | 34% |

Both *locate* the region; only AST returns the clean, exact unit. A real sentence-transformer only widens the gap. `benchmarks/boundary_integrity.py` separately shows AST chunks are syntactically complete where naive windows are not.

## Install

```bash
pip install repo-chunker                      # core (Python only, zero deps but typer)
pip install "repo-chunker[treesitter]"        # + JS / TS / TSX / Go
pip install "repo-chunker[service]"           # + FastAPI HTTP service
```

## Use

CLI:

```bash
repo-chunker ./src --output chunks.jsonl --stats
repo-chunker ./src --max-tokens 512 -o chunks.jsonl   # pack to a token budget
```

Library:

```python
from repo_chunker import chunk_repo
from repo_chunker.pack import pack

chunks = list(chunk_repo("./src"))
chunks = pack(chunks, max_tokens=512)   # RAG-ready sizing
for c in chunks:
    print(c.kind, c.name, c.start_line, c.end_line)  # + c.text, c.imports, c.to_dict()
```

HTTP service (body-only; never reads server-side paths):

```bash
repo-chunker-serve        # POST /chunk {path, source}  ·  GET /health
```

## Languages

Python (stdlib `ast`, zero deps) · JavaScript · TypeScript · TSX · Go (tree-sitter, optional).
Adding a language = implementing the one-method `Parser` protocol. See `ARCHITECTURE.md`.

## Features

- Semantic chunks with metadata: kind, name, parent, imports, line span, token estimate.
- **Token-budget packing**: split oversized units, merge tiny adjacent siblings — pluggable token counter.
- CLI, Python API, JSONL output, optional FastAPI service.
- Two benchmarks (retrieval accuracy + boundary integrity), both CI-enforced.

## License

MIT.