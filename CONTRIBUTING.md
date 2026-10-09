# Contributing

1. `pip install -e ".[dev]"`
2. `ruff check src tests benchmarks` and `ruff format src tests benchmarks`
3. `mypy src/repo_chunker`
4. `pytest -q`
5. `python benchmarks/boundary_integrity.py src`

Adding a language: implement the `Parser` protocol (`language`, `extensions`,
`parse`) and `register()` it. Include tests that assert every emitted chunk is
syntactically complete.
