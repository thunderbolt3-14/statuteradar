from __future__ import annotations

from dataclasses import replace

from .types import Hit


def reciprocal_rank_fusion(rankings: list[list[Hit]], k: int = 60,
                           limit: int | None = None) -> list[Hit]:
    """Fuse ranked lists using RRF; each input list contributes 1 / (k + rank)."""
    if k < 0:
        raise ValueError("RRF k must be non-negative")
    scores: dict[str, float] = {}
    examples: dict[str, Hit] = {}
    first_seen: dict[str, int] = {}
    ordinal = 0
    for ranking in rankings:
        seen: set[str] = set()
        for position, hit in enumerate(ranking, 1):
            if hit.chunk_id in seen:
                continue
            seen.add(hit.chunk_id)
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + position)
            examples.setdefault(hit.chunk_id, hit)
            first_seen.setdefault(hit.chunk_id, ordinal)
            ordinal += 1
    ordered = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], first_seen[chunk_id]))
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        ordered = ordered[:limit]
    return [replace(examples[chunk_id], score=scores[chunk_id], rank=rank)
            for rank, chunk_id in enumerate(ordered, 1)]
