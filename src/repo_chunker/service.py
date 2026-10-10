"""Optional FastAPI service exposing the chunker over HTTP.

Requires the `service` extra (fastapi, uvicorn). Security by design: the service
chunks source sent in the request body and never reads server-side file paths,
so there is no path-traversal or arbitrary-file-read surface. `path` is a label
only, echoed back on each chunk.
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from . import __version__
from .chunker import chunk_source, supported_extensions


class ChunkRequest(BaseModel):
    path: str = Field(default="snippet", description="Label for the source; not read from disk.")
    source: str = Field(description="The source code to chunk.")


def create_app() -> FastAPI:
    app = FastAPI(title="repo-chunker", version=__version__)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "version": __version__,
            "extensions": list(supported_extensions()),
        }

    @app.post("/chunk")
    def chunk(req: ChunkRequest) -> dict[str, object]:
        chunks = chunk_source(req.path, req.source)
        return {"count": len(chunks), "chunks": [c.to_dict() for c in chunks]}

    return app


app = create_app()


def run() -> None:
    """Entry point for the `repo-chunker-serve` console script."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()