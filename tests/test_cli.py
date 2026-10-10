"""CLI behavior: formats, stdin, stdout, context."""
from __future__ import annotations

import json

from typer import Typer
from typer.testing import CliRunner

from repo_chunker.cli import main

app = Typer()
app.command()(main)
runner = CliRunner()

PY = "class C:\n    def m(self):\n        return 1\n\ndef f():\n    return 2\n"
BASE = ["-", "--stdin-name", "x.py", "-o", "-"]


def test_stdin_to_stdout_jsonl() -> None:
    result = runner.invoke(app, BASE, input=PY)
    assert result.exit_code == 0
    rows = [json.loads(ln) for ln in result.stdout.splitlines() if ln.strip()]
    assert {"C", "m", "f"} <= {r["name"] for r in rows}


def test_json_array_format() -> None:
    result = runner.invoke(app, [*BASE, "--format", "json"], input=PY)
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert any(r["name"] == "m" for r in data)


def test_context_flag_prefixes_parent() -> None:
    result = runner.invoke(app, [*BASE, "--format", "json", "--context"], input=PY)
    data = json.loads(result.stdout)
    method = next(r for r in data if r["name"] == "m")
    assert method["text"].startswith("class C:")


def test_bad_format_rejected() -> None:
    result = runner.invoke(app, [*BASE, "--format", "yaml"], input=PY)
    assert result.exit_code != 0


def test_write_to_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    out = tmp_path / "chunks.jsonl"
    src = tmp_path / "x.py"
    src.write_text(PY, encoding="utf-8")
    result = runner.invoke(app, [str(src), "-o", str(out), "--stats"])
    assert result.exit_code == 0
    assert out.exists()
    assert "By kind:" in (result.stderr or "")  # informational output -> stderr