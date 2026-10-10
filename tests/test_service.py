"""Tests for the FastAPI service (skipped if the `service` extra is absent)."""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from repo_chunker.service import create_app  # noqa: E402

client = TestClient(create_app())


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert ".py" in body["extensions"]


def test_chunk_python() -> None:
    resp = client.post("/chunk", json={"path": "a.py", "source": "def f(x):\n    return x\n"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    first = body["chunks"][0]
    assert first["name"] == "f"
    assert first["path"] == "a.py"


def test_chunk_rejects_missing_source() -> None:
    resp = client.post("/chunk", json={"path": "a.py"})
    assert resp.status_code == 422  # validation error, no source