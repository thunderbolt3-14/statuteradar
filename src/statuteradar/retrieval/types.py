from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Hit:
    """One retrieval result. `score` is only comparable within one retriever."""

    chunk_id: str
    score: float
    citation: str
    instrument: str
    text: str
    rank: int = 0            # 1-based position in the result list