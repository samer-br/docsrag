"""FastAPI entrypoint for DocsRAG."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .config import get_settings
from .rag import RagEngine
from .schemas import AskRequest, AskResponse
from .store import VectorStore

_engine: RagEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine
    index_dir = get_settings().index_dir
    if VectorStore.exists(index_dir):
        _engine = RagEngine.load(index_dir)
    yield


app = FastAPI(title="DocsRAG", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "index_loaded": _engine is not None}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    if _engine is None:
        raise HTTPException(
            status_code=503,
            detail="Index not built. Run `python -m app.ingest` first.",
        )
    return _engine.answer(req.question, top_k=req.top_k, use_graph=req.use_graph)
