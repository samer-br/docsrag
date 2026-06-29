"""Pydantic models shared across the API and pipeline."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    id: int
    text: str
    source: str
    heading: str = ""

    def label(self) -> str:
        return f"{self.source}" + (f" › {self.heading}" if self.heading else "")


class Citation(BaseModel):
    source: str
    heading: str = ""
    score: float


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int | None = None
    use_graph: bool | None = None


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    contexts: list[Chunk]
    latency_ms: int
