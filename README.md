# repo-chunker

**AST-aware semantic code chunking for RAG.** Splits a codebase into *logically complete* units — functions, classes, methods — instead of arbitrary line or character windows, so a retrieval model never receives a function cut in half.

[![ci](https://github.com/socrates6969/repo-chunker/actions/workflows/ci.yml/badge.svg)](https://github.com/socrates6969/repo-chunker/actions)

## Why

Most RAG pipelines chunk code by character/line count (e.g. LangChain `RecursiveCharacterTextSplitter`). That routinely slices through the middle of a function, destroying the exact context a model needs. `repo-chunker` parses the code and emits whole semantic units with metadata (imports, parent class, line span), so retrieval returns code that actually makes sense on its own.

The repository ships a **boundary-integrity benchmark** that quantifies this: the share of chunks that are syntactically complete on their own, AST vs naive. (Run it: `python benchmarks/boundary_integrity.py src`.)

## Install

```bash
pip install repo-chunker          # once published
# or, from source:
pip install -e ".[dev]"
```

## Usage

CLI:

```bash
repo-chunker ./src --output chunks.jsonl --stats
```

Library:

```python
from repo_chunker import chunk_repo, chunk_file

for chunk in chunk_repo("./src"):
    print(chunk.kind, chunk.name, chunk.start_line, chunk.end_line)
    # chunk.text, chunk.imports, chunk.parent, chunk.metadata, chunk.token_estimate
```

Each chunk is a frozen dataclass with `to_dict()` for JSONL output, ready to embed.

## Supported languages

- **Python** (v0.1, via the standard-library `ast` — zero native dependencies).
- JavaScript / TypeScript / Go — next, via a pluggable tree-sitter backend (see ARCHITECTURE.md).

## Design

A tiny `Parser` protocol (`parse(path, source) -> list[Chunk]`) with a per-extension registry. v0.1 deliberately ships one language on the stdlib parser to prove the architecture and the eval before taking on tree-sitter grammar builds. See `ARCHITECTURE.md`.

## Roadmap

- tree-sitter backend: JS/TS, Go, Rust, Java
- token-budget packing (merge small siblings up to a tokenizer limit)
- call-graph metadata (link a chunk to the definitions it references)
- optional FastAPI service + Docker image
- retrieval-accuracy benchmark (embed AST vs naive chunks, compare recall)

## License

MIT.
