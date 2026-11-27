from __future__ import annotations

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from ..ingest.schema import Chunk
from .corpus import embed_text
from .types import Hit

_TOKEN_RE = re.compile(r"[\w]+(?:[-'][\w]+)*", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """A small, deterministic tokenizer that preserves legal terms and numbers."""
    return [token.casefold() for token in _TOKEN_RE.findall(text)]


@dataclass
class BM25Retriever:
    chunks: list[Chunk]
    with_header: bool = True

    def __post_init__(self) -> None:
        if not self.chunks:
            raise ValueError("BM25 needs at least one chunk")
        self._corpus = [tokenize(embed_text(chunk, self.with_header)) for chunk in self.chunks]
        self._index = BM25Okapi(self._corpus)

    def search(self, query: str, k: int = 10, where: dict | None = None) -> list[Hit]:
        if k < 1:
            raise ValueError("k must be at least 1")
        terms = tokenize(query)
        if not terms:
            return []
        scores = self._index.get_scores(terms)
        candidates = []
        for i, (chunk, score) in enumerate(zip(self.chunks, scores)):
            if where and any(getattr(chunk, key, None) != value for key, value in where.items()):
                continue
            candidates.append((i, chunk, float(score)))
        candidates.sort(key=lambda item: (-item[2], item[0]))
        return [Hit(chunk_id=c.chunk_id, score=score, citation=c.citation,
                    instrument=c.instrument, text=c.text, rank=rank)
                for rank, (_, c, score) in enumerate(candidates[:k], 1)]
