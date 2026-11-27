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
        """Encode every token, using overlapping windows for texts over the model limit.

        Sentence Transformers silently truncates long inputs. Windowing keeps the source chunk
        and its ID intact while ensuring that all of its text contributes to its vector.
        Window vectors are weighted by the number of content tokens and normalized afterward.
        """
        if not texts:
            return np.empty((0, 0), dtype="float32")

        limit = self.max_seq_length
        tokenizer = self.model.tokenizer
        special_tokens = tokenizer.num_special_tokens_to_add(pair=False)
        window_size = (limit - special_tokens) if limit else None
        overlap = min(32, max(0, (window_size or 1) // 8))

        windows: list[str] = []
        assignments: list[list[tuple[int, int]]] = []
        previous_tokenizer_limit = getattr(tokenizer, "model_max_length", None)
        if previous_tokenizer_limit is not None:
            # Full source chunks are intentionally tokenized here; avoid warnings while
            # measuring them, then restore the model's normal limit before inference.
            tokenizer.model_max_length = 10**6
        try:
            for text in texts:
                token_ids = tokenizer.encode(text, add_special_tokens=False)
                spans = []
                if window_size and len(token_ids) > window_size:
                    start = 0
                    while start < len(token_ids):
                        piece = token_ids[start:start + window_size]
                        window = tokenizer.decode(piece, skip_special_tokens=True)
                        # Decoding and re-tokenizing can change token boundaries (for example,
                        # around punctuation). Include special tokens in the limit check.
                        while len(tokenizer.encode(window, add_special_tokens=True)) > limit:
                            if len(piece) <= 1:
                                raise ValueError("tokenizer cannot produce a window within max_seq_length")
                            piece = piece[:-1]
                            window = tokenizer.decode(piece, skip_special_tokens=True)
                        if not piece:
                            break
                        spans.append((len(windows), len(piece)))
                        windows.append(window)
                        if start + len(piece) >= len(token_ids):
                            break
                        start += max(1, len(piece) - overlap)
                else:
                    spans.append((len(windows), max(1, len(token_ids))))
                    windows.append(text)
                assignments.append(spans)
        finally:
            if previous_tokenizer_limit is not None:
                tokenizer.model_max_length = previous_tokenizer_limit

        vecs = np.asarray(self.model.encode(
            windows, batch_size=batch_size, normalize_embeddings=True,
            show_progress_bar=len(windows) > 200, convert_to_numpy=True,
        ), dtype="float32")
        out = []
        for spans in assignments:
            weights = np.asarray([count for _, count in spans], dtype="float32")
            combined = np.average(np.stack([vecs[i] for i, _ in spans]), axis=0, weights=weights)
            norm = np.linalg.norm(combined)
            out.append(combined / norm if norm else combined)
        return np.asarray(out, dtype="float32")

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
