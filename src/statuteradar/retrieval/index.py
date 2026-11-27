from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")   # must be set before chromadb is imported

from ..ingest.schema import Chunk  # noqa: E402
from .config import CHROMA_DIR, COLLECTION  # noqa: E402
from .corpus import embed_text  # noqa: E402
from .embedder import Embedder  # noqa: E402
from .types import Hit  # noqa: E402


def _client(persist_dir: Path):
    import chromadb
    from chromadb.config import Settings

    return chromadb.PersistentClient(path=str(persist_dir), settings=Settings(anonymized_telemetry=False))


def chunk_meta(c: Chunk) -> dict:
    """Chroma metadata may not contain None, so optional fields are simply left out."""
    m = {"chunk_id": c.chunk_id, "instrument": c.instrument, "jurisdiction": c.jurisdiction,
         "kind": c.kind, "unit_id": c.unit_id, "citation": c.citation, "token_count": c.token_count}
    if c.title:
        m["title"] = c.title
    if c.commencement_phase is not None:
        m["commencement_phase"] = c.commencement_phase
    return m


def build_index(chunks: list[Chunk], embedder: Embedder, persist_dir: Path = CHROMA_DIR,
                collection: str = COLLECTION, with_header: bool = True, batch: int = 256) -> int:
    """(Re)build the vector index. 'Training' here only means indexing: embed and store."""
    client = _client(persist_dir)
    try:
        client.delete_collection(collection)
    except Exception:
        pass
    col = client.create_collection(collection, metadata={
        "hnsw:space": "cosine", "embedding_model": embedder.name, "with_header": with_header})
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        vecs = embedder.encode([embed_text(c, with_header) for c in part])
        col.add(ids=[c.chunk_id for c in part], embeddings=vecs.tolist(),
                documents=[c.text for c in part], metadatas=[chunk_meta(c) for c in part])
    return col.count()


def get_collection(persist_dir: Path = CHROMA_DIR, collection: str = COLLECTION):
    return _client(persist_dir).get_collection(collection)


def dense_search(query: str, embedder: Embedder, k: int = 10, where: dict | None = None,
                 persist_dir: Path = CHROMA_DIR, collection: str = COLLECTION) -> list[Hit]:
    col = get_collection(persist_dir, collection)
    q = embedder.encode([query])[0]
    res = col.query(query_embeddings=[q.tolist()], n_results=min(k, col.count()), where=where,
                    include=["documents", "metadatas", "distances"])
    hits = []
    for rank, (doc, meta, dist) in enumerate(zip(res["documents"][0], res["metadatas"][0], res["distances"][0]), 1):
        hits.append(Hit(chunk_id=meta["chunk_id"], score=1.0 - float(dist), citation=meta["citation"],
                        instrument=meta["instrument"], text=doc, rank=rank))
    return hits