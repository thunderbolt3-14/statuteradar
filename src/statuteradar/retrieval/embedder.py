from __future__ import annotations

import hashlib
import os
import re
from typing import Protocol

import numpy as np

from .config import EMBEDDING_MODEL

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")   # harmless Windows cache warning


class Embedder(Protocol):
    name: str
    max_seq_length: int | None

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    """Pretrained sentence-transformers model, used as-is (no training or fine-tuning)."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        from sentence_transformers import SentenceTransformer

        self.name = model_name
        self.model = SentenceTransformer(model_name)
        self.max_seq_length: int | None = self.model.max_seq_length

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        vecs = self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True,
                                 show_progress_bar=len(texts) > 200, convert_to_numpy=True)
        return np.asarray(vecs, dtype="float32")

    def token_counts(self, texts: list[str]) -> list[int]:
        """Real word-piece counts (including special tokens), without truncation."""
        tok = self.model.tokenizer
        tok.model_max_length = 10**6          # silence the 'longer than max length' warning
        return [len(ids) for ids in tok(texts, add_special_tokens=True, truncation=False)["input_ids"]]


class HashingEmbedder:
    """Deterministic bag-of-words embedder for TESTS ONLY (needs no model download)."""

    def __init__(self, dim: int = 256):
        self.name, self.dim, self.max_seq_length = f"hashing-{dim}", dim, None

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype="float32")
        for i, t in enumerate(texts):
            for w in re.findall(r"\w+", t.lower()):
                h = int(hashlib.md5(w.encode()).hexdigest(), 16)
                out[i, h % self.dim] += 1.0 if (h >> 64) % 2 else -1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.where(norms == 0, 1, norms)


def make_embedder() -> Embedder:
    """The real model by default. STATUTERADAR_EMBEDDER=hashing gives the offline toy embedder
    (useful to check that the pipeline works when a model download is blocked)."""
    if os.environ.get("STATUTERADAR_EMBEDDER") == "hashing":
        return HashingEmbedder()
    return SentenceTransformerEmbedder()