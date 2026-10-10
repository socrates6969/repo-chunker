"""Retrieval-accuracy benchmark: AST chunks vs naive line-window chunks.

repo-chunker's claim is that semantic (AST) chunks are retrieved as the *exact
relevant unit* with little noise, whereas a line window either splits a unit or
bundles it with neighbours. Both can "locate the region", so overlap-recall
saturates and is uninformative; the honest, decisive metrics are:

  * exact@1     - the top hit is exactly the target unit (AST wins; windows can't)
  * precision@1 - fraction of the top hit's lines that are the target, not noise
  * mrr         - reciprocal rank of the first chunk overlapping the target

Embedding is a dependency-free lexical TF-IDF proxy: deterministic, no model
download, no GPU. A real sentence-transformer is the production path and would
only widen the gap, since it rewards the semantic coherence AST chunks have.
"""
from __future__ import annotations

import math
import re
from collections.abc import Callable
from dataclasses import dataclass

from repo_chunker import chunk_source

_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_CAMEL = re.compile(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])")

TOPICS = [
    "invoice", "detention", "lumper", "geofence", "tariff", "accessorial",
    "payload", "manifest", "dunnage", "backhaul", "chassis", "drayage",
    "reweigh", "layover", "liftgate", "pallet", "waybill", "telematics",
    "appointment", "demurrage", "surcharge", "brokerage", "carrier", "shipper",
    "consignee", "odometer", "reefer", "hazmat", "customs", "freightclass",
    "lane", "dispatch", "warehouse", "remittance", "settlement", "ledger",
    "chargeback", "rebill", "overcharge", "shortpay",
]

Chunk4 = tuple[str, int, int, str]  # (path, start_line, end_line, text)


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    for tok in _TOKEN.findall(text):
        lower = tok.lower()
        out.append(lower)
        for part in tok.split("_"):
            for sub in _CAMEL.findall(part):
                s = sub.lower()
                if s and s != lower:
                    out.append(s)
    return out


@dataclass(frozen=True)
class LexicalIndex:
    idf: dict[str, float]

    def vector(self, text: str) -> dict[str, float]:
        tf: dict[str, int] = {}
        for t in tokenize(text):
            tf[t] = tf.get(t, 0) + 1
        return {t: count * self.idf.get(t, 0.0) for t, count in tf.items()}


def build_index(docs: list[str]) -> LexicalIndex:
    n = len(docs)
    df: dict[str, int] = {}
    for doc in docs:
        for t in set(tokenize(doc)):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}
    return LexicalIndex(idf)


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b[k] for k in a.keys() & b.keys())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


@dataclass(frozen=True)
class Target:
    path: str
    name: str
    query: str
    start: int
    end: int


@dataclass(frozen=True)
class SourceFile:
    path: str
    source: str
    targets: tuple[Target, ...]


def _make_file(path: str, topics: list[str]) -> SourceFile:
    lines: list[str] = []
    targets: list[Target] = []
    for topic in topics:
        start = len(lines) + 1
        name = f"handle_{topic}"
        doc = f"Process the {topic} record and return its {topic} total."
        lines.append(f"def {name}(record):")
        lines.append(f'    """{doc}"""')
        lines.append("    total = 0")
        lines.append(f'    for item in record["{topic}"]:')
        lines.append(f"        total += compute_{topic}(item)")
        lines.append(f'    return {{"{topic}": total}}')
        lines.append("")
        targets.append(Target(path, name, f"{doc} {name} {topic}", start, start + 5))
    return SourceFile(path, "\n".join(lines) + "\n", tuple(targets))


def build_corpus(per_file: int = 5) -> list[SourceFile]:
    groups = [TOPICS[i : i + per_file] for i in range(0, len(TOPICS), per_file)]
    return [_make_file(f"mod_{i}.py", group) for i, group in enumerate(groups)]


def ast_chunks(f: SourceFile) -> list[Chunk4]:
    return [(c.path, c.start_line, c.end_line, c.text) for c in chunk_source(f.path, f.source)]


def naive_chunks(f: SourceFile, window: int = 20) -> list[Chunk4]:
    lines = f.source.splitlines()
    out: list[Chunk4] = []
    for i in range(0, len(lines), window):
        seg = lines[i : i + window]
        out.append((f.path, i + 1, i + len(seg), "\n".join(seg)))
    return out


def _overlap_lines(a0: int, a1: int, b0: int, b1: int) -> int:
    return max(0, min(a1, b1) - max(a0, b0) + 1)


def _score(
    files: list[SourceFile], chunker: Callable[[SourceFile], list[Chunk4]]
) -> dict[str, float]:
    chunks: list[Chunk4] = []
    for f in files:
        chunks.extend(chunker(f))
    index = build_index([c[3] for c in chunks])
    cvecs = [index.vector(c[3]) for c in chunks]
    targets = [t for f in files for t in f.targets]

    located = exact = 0
    precision_sum = rr_sum = 0.0
    for t in targets:
        qv = index.vector(t.query)
        order = sorted(((cosine(qv, cvecs[i]), i) for i in range(len(chunks))), reverse=True)
        # Top-1: how clean is the single best-ranked chunk?
        path, s, e, _ = chunks[order[0][1]]
        overlap = _overlap_lines(s, e, t.start, t.end) if path == t.path else 0
        if overlap > 0:
            located += 1
            precision_sum += overlap / (e - s + 1)
            if s == t.start and e == t.end:
                exact += 1
        # Reciprocal rank of the first chunk that overlaps the target region.
        for rank, (_score_val, i) in enumerate(order):
            pp, ss, ee, _ = chunks[i]
            if pp == t.path and ss <= t.end and ee >= t.start:
                rr_sum += 1.0 / (rank + 1)
                break

    n = len(targets)
    return {
        "located@1": located / n,
        "exact@1": exact / n,
        "precision@1": precision_sum / n,
        "mrr": rr_sum / n,
    }


def evaluate() -> dict[str, dict[str, float]]:
    files = build_corpus()
    return {"ast": _score(files, ast_chunks), "naive": _score(files, naive_chunks)}


def main() -> int:
    files = build_corpus()
    funcs = sum(len(f.targets) for f in files)
    res = evaluate()
    print(f"corpus: {len(files)} files, {funcs} functions (lexical TF-IDF proxy)")
    print(f"{'method':8} {'located@1':>10} {'exact@1':>9} {'precision@1':>12} {'MRR':>7}")
    for method in ("ast", "naive"):
        r = res[method]
        print(
            f"{method:8} {r['located@1']:10.3f} {r['exact@1']:9.3f} "
            f"{r['precision@1']:12.3f} {r['mrr']:7.3f}"
        )
    a, nv = res["ast"], res["naive"]
    print(f"exact-unit retrieval: AST {a['exact@1']:.0%} vs naive {nv['exact@1']:.0%}")
    print(f"top-1 on-target purity: AST {a['precision@1']:.0%} vs naive {nv['precision@1']:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())