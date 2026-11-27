from __future__ import annotations

from dataclasses import replace

from .config import RERANKER_MODEL
from .types import Hit


class CrossEncoderReranker:
    """Score query and provision together, for reranking a short candidate list."""

    def __init__(self, model_name: str = RERANKER_MODEL):
        from sentence_transformers import CrossEncoder

        self.name = model_name
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list[Hit], top_k: int | None = None) -> list[Hit]:
        if not candidates:
            return []
        pairs = [(query, hit.text) for hit in candidates]
        scores = self.model.predict(pairs, show_progress_bar=False)
        ranked = sorted(zip(candidates, scores), key=lambda pair: float(pair[1]), reverse=True)
        if top_k is not None:
            if top_k < 1:
                raise ValueError("top_k must be at least 1")
            ranked = ranked[:top_k]
        return [replace(hit, score=float(score), rank=rank)
                for rank, (hit, score) in enumerate(ranked, 1)]
