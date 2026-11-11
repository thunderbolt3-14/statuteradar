from __future__ import annotations

from .bm25 import BM25Retriever
from .fusion import reciprocal_rank_fusion
from .index import dense_search
from .reranker import CrossEncoderReranker
from .types import Hit


def hybrid_search(query: str, embedder, bm25: BM25Retriever, k: int = 10,
                  candidate_k: int = 30, where: dict | None = None) -> list[Hit]:
    dense = dense_search(query, embedder, k=candidate_k, where=where)
    sparse = bm25.search(query, k=candidate_k, where=where)
    return reciprocal_rank_fusion([dense, sparse], k=60, limit=k)


def hybrid_reranked_search(query: str, embedder, bm25: BM25Retriever,
                           reranker: CrossEncoderReranker, k: int = 10,
                           candidate_k: int = 30, where: dict | None = None) -> list[Hit]:
    candidates = hybrid_search(query, embedder, bm25, k=candidate_k,
                               candidate_k=candidate_k, where=where)
    return reranker.rerank(query, candidates, top_k=k)
