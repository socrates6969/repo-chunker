# repo-chunker

**AST-aware semantic code chunking for RAG.** Splits a codebase into *logically complete* units — whole functions, classes, methods, interfaces, structs — instead of arbitrary line or character windows, so a retrieval model receives the exact relevant code, not a function cut in half or three unrelated ones glued together.

[![ci](https://github.com/socrates6969/repo-chunker/actions/workflows/ci.yml/badge.svg)](https://github.com/socrates6969/repo-chunker/actions)

## Why it is better (measured, not claimed)

`benchmarks/retrieval_eval.py` compares AST chunks to naive line windows on a controlled corpus with a dependency-free lexical embedder:

| metric | AST (repo-chunker) | naive line windows |
|---|---|---|
| exact-unit retrieval @1 | **100%** | 0% |
| top-1 on-target purity | **100%** | 34% |

Both *locate* the region; only AST returns the clean, exact unit. A real sentence-transformer should only widen the gap. `benchmarks/boundary_integrity.py` separately shows AST chunks are syntactically complete where naive windows are not. Both benchmarks are CI-enforced.

## Install

```bash
pip install repo-chunker                      # core: Python + Markdown, zero deps but typer
pip install "repo-chunker[treesitter]"        # + 12 more languages via tree-sitter
pip install "repo-chunker[service]"           # + FastAPI HTTP service
```

## Use

CLI:

```bash
repo-chunker ./src --output chunks.jsonl --stats
repo-chunker ./src --max-tokens 512 -o chunks.jsonl    # pack to a token budget
repo-chunker ./src --context -o chunks.jsonl           # prefix methods with their class
cat file.py | repo-chunker - --stdin-name x.py -o - --format json
```

Library:

```python
from repo_chunker import chunk_repo, add_parent_context, ChunkCache
from repo_chunker.pack import pack

chunks = list(chunk_repo("./src"))
chunks = add_parent_context(chunks)      # methods carry their class signature
chunks = pack(chunks, max_tokens=512)    # RAG-ready sizing
for c in chunks:
    print(c.kind, c.name, c.start_line, c.end_line)   # + c.text, c.imports, c.to_dict()

# Re-chunk a repo cheaply: unchanged files are served from cache.
cache = ChunkCache(".repo-chunker-cache.json")
chunks = cache.chunk_repo("./src"); cache.save()
```

HTTP service (body-only; never reads server-side paths):

```bash
repo-chunker-serve        # POST /chunk {path, source}  .  GET /health
```

## Languages

**13 programming languages, plus Markdown.**

Python (stdlib `ast`, zero deps) and Markdown (header-aware, zero deps) ship in the core.
With the `treesitter` extra: JavaScript, TypeScript, TSX, Go, Rust, Java, C, C++, C#, Ruby, PHP, Kotlin.

Adding a language is implementing the one-method `Parser` protocol (or one `LangSpec` entry for a tree-sitter grammar). See `ARCHITECTURE.md`.

## Features

- Semantic chunks with metadata: kind, name, parent, imports, line span, token estimate.
- **Markdown sectioning**: header-aware, code-fence aware, ancestor-heading parents.
- **Parent-context enrichment**: methods read as self-contained, in-context passages.
- **Token-budget packing**: split oversized units, merge tiny adjacent siblings — pluggable token counter.
- **Incremental cache**: mtime+size keyed; re-chunking skips unchanged files.
- CLI (JSON or JSONL, stdin/stdout, piping), Python API, optional FastAPI service.
- Two CI-enforced benchmarks (retrieval accuracy + boundary integrity).

## License

MIT.