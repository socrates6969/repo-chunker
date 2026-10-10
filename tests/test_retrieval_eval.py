"""Test enforcing the core claim: AST chunks retrieve the clean unit; windows don't."""
from __future__ import annotations

from benchmarks.retrieval_eval import evaluate


def test_ast_returns_exact_clean_unit() -> None:
    r = evaluate()
    # AST should return the exact target unit as the top hit, nearly always.
    assert r["ast"]["exact@1"] >= 0.9
    assert r["ast"]["precision@1"] >= 0.9
    # Naive line windows cannot return an exact unit and carry neighbour noise.
    assert r["ast"]["exact@1"] > r["naive"]["exact@1"]
    assert r["ast"]["precision@1"] > r["naive"]["precision@1"]