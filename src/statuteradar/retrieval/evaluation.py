from __future__ import annotations

from collections.abc import Iterable, Sequence

from .types import Hit


def hit_rate_at_k(ranking: Sequence[Hit], relevant_ids: set[str], k: int = 5) -> float:
    _validate_k(k)
    return float(any(hit.chunk_id in relevant_ids for hit in ranking[:k]))


def recall_at_k(ranking: Sequence[Hit], relevant_ids: set[str], k: int = 5) -> float:
    _validate_k(k)
    if not relevant_ids:
        raise ValueError("each evaluation query needs at least one relevant chunk")
    found = {hit.chunk_id for hit in ranking[:k]} & relevant_ids
    return len(found) / len(relevant_ids)


def reciprocal_rank_at_k(ranking: Sequence[Hit], relevant_ids: set[str], k: int = 5) -> float:
    _validate_k(k)
    for rank, hit in enumerate(ranking[:k], 1):
        if hit.chunk_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def aggregate_metrics(rankings: Iterable[Sequence[Hit]], relevant: Iterable[set[str]],
                      k: int = 5) -> dict[str, float]:
    rankings, relevant = list(rankings), list(relevant)
    if len(rankings) != len(relevant):
        raise ValueError("each evaluation query must have one ranking and one gold set")
    pairs = list(zip(rankings, relevant))
    if not pairs:
        raise ValueError("evaluation set must contain at least one query")
    if any(not gold for _, gold in pairs):
        raise ValueError("each evaluation query needs at least one relevant chunk")
    return {
        f"hit_rate@{k}": sum(hit_rate_at_k(r, g, k) for r, g in pairs) / len(pairs),
        f"mrr@{k}": sum(reciprocal_rank_at_k(r, g, k) for r, g in pairs) / len(pairs),
        f"recall@{k}": sum(recall_at_k(r, g, k) for r, g in pairs) / len(pairs),
    }


def _validate_k(k: int) -> None:
    if k < 1:
        raise ValueError("k must be at least 1")
