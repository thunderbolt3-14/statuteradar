"""Embed data/processed/chunks.jsonl and (re)build the Chroma index.

python scripts/build_index.py              # with the provision header in the embedded text
python scripts/build_index.py --no-header  # text only (for the ablation in the Phase 2 evaluation)
"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statuteradar.retrieval.config import CHROMA_DIR, COLLECTION  # noqa: E402
from statuteradar.retrieval.corpus import load_chunks  # noqa: E402
from statuteradar.retrieval.embedder import make_embedder  # noqa: E402
from statuteradar.retrieval.index import build_index  # noqa: E402

with_header = "--no-header" not in sys.argv
chunks = load_chunks()
print(f"loaded {len(chunks)} chunks; loading the embedding model (the first run downloads it)...")
emb = make_embedder()
t0 = time.time()
n = build_index(chunks, emb, with_header=with_header)
print(f"indexed {n} chunks | model: {emb.name} | dim: {emb.encode(['x']).shape[1]} | header: {with_header}")
print(f"collection '{COLLECTION}' saved at {CHROMA_DIR}  ({time.time() - t0:.0f}s)")