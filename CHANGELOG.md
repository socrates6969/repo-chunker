# Changelog

## 2.0.0
- **6 new languages** (13 total): C, C++, C#, Ruby, PHP, Kotlin. The tree-sitter
  walker is now container-aware (recurses into namespaces, modules, and declaration
  lists) so nested declarations are found at any depth; new struct/interface/trait/
  enum/property chunk kinds.
- **Markdown chunker** (zero dependencies): header-aware sectioning with ancestor-
  heading parent tracking; code-fence aware.
- **Parent-context enrichment** (`add_parent_context`): prefix child chunks with the
  parent's signature so methods read as self-contained passages for embedding.
- **Incremental cache** (`ChunkCache`): mtime+size keyed; re-chunking skips unchanged
  files. `Chunk.from_dict` round-trips `to_dict()`.
- **CLI**: `--format json|jsonl`, stdin (`-`), stdout (`-o -`), `--context`.
- Release workflow publishes to PyPI via Trusted Publishing (OIDC) on tag.

## 1.1.0
- Added Rust and Java tree-sitter parsers (7 languages total). Added LESSONS.md retrospective.

## 1.0.0
- Token-budget packing (`repo_chunker.pack.pack`): split oversized chunks and merge
  tiny adjacent same-file chunks to a token budget; pluggable token counter.
- CLI `--max-tokens` flag applies packing to output.
- GitHub release workflow (build sdist/wheel on tag).
- First stable API: `chunk_source`, `chunk_file`, `chunk_repo`, `pack`, `Chunk`, `Parser`.

## 0.4.0
- Optional FastAPI service (`repo-chunker-serve`): `POST /chunk`, `GET /health`.
  Body-only by design (no server-side file reads).

## 0.3.0
- Retrieval-accuracy benchmark: exact-unit recall and on-target precision, AST vs naive.

## 0.2.0
- Tree-sitter backend: JavaScript, TypeScript, TSX, Go (optional `treesitter` extra).

## 0.1.0
- Initial release: Python AST chunking, CLI, JSONL, boundary-integrity benchmark.