# Architecture

## Principle: AI reads structure, code guarantees boundaries

`repo-chunker` turns source into semantic `Chunk`s. The contract is a one-method
protocol:

    Parser.parse(path: str, source: str) -> list[Chunk]

A per-extension registry (`register`, `chunk_source`, `chunk_file`, `chunk_repo`)
dispatches files to the right parser. Adding a language = adding a `Parser`.

## Why Python-first on the stdlib AST (v0.1)

The hard dependency for multi-language support is tree-sitter grammars, which are
fiddly to build/ship (especially on Windows). To de-risk, v0.1 ships Python via
the standard-library `ast` module: zero native deps, deterministic, 100% reliable.
This proves the architecture AND the differentiating benchmark before we take on
grammar builds. The `Parser` protocol means the tree-sitter backend drops in
without touching the registry or the data model.

## Data model

`Chunk` (frozen dataclass): path, language, kind (function|class|method), name,
start_line, end_line, text, parent, imports, metadata, token_estimate. `to_dict()`
emits JSONL ready to embed.

## The benchmark is the product proof

`benchmarks/boundary_integrity.py` measures the share of chunks that parse on
their own, AST vs naive line windows. A good chunker should approach 100%; naive
splitting does not. This metric is the honest, measurable claim behind the tool.

## Roadmap

1. tree-sitter backend (JS/TS, Go, Rust, Java) behind the same `Parser` protocol.
2. token-budget packing: merge small sibling nodes up to a tokenizer limit.
3. call-graph metadata linking chunks to referenced definitions.
4. FastAPI `/chunk` service + Docker image for drop-in deployment.
5. retrieval-accuracy benchmark: embed AST vs naive chunks, compare recall@k.
