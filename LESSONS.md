# Lessons from building repo-chunker (v0.1 -> v1.1)

A real retrospective of what worked and what bit us, recorded for the next contributor.

## What worked
- **Verify-before-keep, every increment.** Each version was only committed after ruff +
  mypy + pytest were green and a benchmark/smoke actually ran. Nothing shipped on faith.
- **De-risk the hard dependency first.** v0.1 shipped Python via the stdlib `ast` (zero
  deps, 100% reliable) behind a one-method `Parser` protocol, proving the architecture and
  the benchmark before taking on tree-sitter grammars in v0.2.
- **Optional extras + graceful degradation.** tree-sitter and FastAPI are extras; if they
  are absent the import fails quietly and the core still works. The core stays dep-free.
- **Make the value claim a test.** The retrieval benchmark is enforced by a CI test, so the
  "AST beats naive" claim cannot silently rot.

## What bit us (and the fix)
- **UTF-8 BOM broke `pyproject.toml`.** Windows PowerShell `Set-Content -Encoding utf8`
  writes a BOM, which Python's `tomllib` rejects ("Invalid statement at 1:1"). Fix: write
  files with `System.Text.UTF8Encoding($false)` (no BOM).
- **A saturated metric looked like success.** The first retrieval metric (overlap-recall)
  read 1.000 for both AST and naive — because a line window trivially overlaps a function.
  Fix: measure what matters — exact-unit retrieval and on-target precision — which exposed
  the real 100%-vs-0% / 100%-vs-34% gap.
- **Agent-tool state leaked into the repo.** A `.claude-flow/` folder got created in the
  project and swept into a commit by `git add -A`. Fix: remove it and gitignore it.

## Where to extend
- Call-graph metadata linking a chunk to the definitions it references.
- A real sentence-transformer benchmark mode (the lexical embedder is a proxy).
- More grammars — any new language is just one `LangSpec`.