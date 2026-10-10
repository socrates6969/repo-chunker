# Changelog

## 0.3.0 (unreleased)
- Retrieval-accuracy benchmark (`benchmarks/retrieval_eval.py`): embeds AST chunks
  vs naive line-window chunks with a dependency-free lexical TF-IDF proxy and reports
  recall@1/3/5 and MRR. CI-enforced by a test asserting AST >= naive.

## 0.2.0
- Tree-sitter backend: JavaScript, TypeScript, TSX, Go, behind the Parser protocol.
  Optional `treesitter` extra; degrades to Python-only if not installed.

## 0.1.0
- Initial release: Python AST chunking (functions, classes, methods) with
  import/parent metadata. CLI, library API, JSONL output, boundary-integrity benchmark.