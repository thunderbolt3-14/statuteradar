from __future__ import annotations

from pathlib import Path

from ..ingest.schema import Chunk
from .config import CHUNKS_PATH


def load_chunks(path: Path = CHUNKS_PATH) -> list[Chunk]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found - run `python scripts/run_ingest.py` (Phase 1) first")
    return [Chunk.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def context_header(c: Chunk) -> str:
    """Short label put in front of the text so the embedding 'knows' which law and provision it is."""
    return f"{c.citation} - {c.title}" if c.title else c.citation


def embed_text(c: Chunk, with_header: bool = True) -> str:
    return f"{context_header(c)}\n{c.text}" if with_header else c.text