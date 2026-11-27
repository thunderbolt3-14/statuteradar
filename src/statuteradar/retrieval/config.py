from __future__ import annotations

import os
from pathlib import Path

from ..ingest.config import PROCESSED, ROOT

try:                                    # .env is optional; the defaults below match .env.example
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

CHUNKS_PATH = PROCESSED / "chunks.jsonl"

_chroma = Path(os.environ.get("CHROMA_PERSIST_DIR", "./data/chroma_db"))
CHROMA_DIR = _chroma if _chroma.is_absolute() else ROOT / _chroma   # relative to the repo root, not the cwd

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RERANKER_MODEL = os.environ.get("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
COLLECTION = "statute_chunks_windowed"
