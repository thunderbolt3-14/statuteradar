"""Compare dense, BM25, hybrid, and hybrid-plus-cross-encoder retrieval."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from statuteradar.retrieval.bm25 import BM25Retriever  # noqa: E402
from statuteradar.retrieval.corpus import load_chunks  # noqa: E402
from statuteradar.retrieval.embedder import make_embedder  # noqa: E402
from statuteradar.retrieval.evaluation import aggregate_metrics  # noqa: E402
from statuteradar.retrieval.index import dense_search  # noqa: E402
from statuteradar.retrieval.reranker import CrossEncoderReranker  # noqa: E402
from statuteradar.retrieval.search import hybrid_search, hybrid_reranked_search  # noqa: E402

K = 5
CANDIDATES = 30
cases = json.loads((ROOT / "data" / "retrieval_eval.json").read_text(encoding="utf-8"))
chunks = load_chunks()
known_ids = {chunk.chunk_id for chunk in chunks}
unknown = {chunk_id for case in cases for chunk_id in case["relevant_ids"]} - known_ids
if unknown:
    raise ValueError(f"evaluation set refers to unknown chunk IDs: {sorted(unknown)}")
bm25 = BM25Retriever(chunks)
embedder = make_embedder()
reranker = CrossEncoderReranker()

runs = {"dense": [], "BM25": [], "hybrid": [], "hybrid + reranker": []}
gold = []
for case in cases:
    query, relevant = case["query"], set(case["relevant_ids"])
    runs["dense"].append(dense_search(query, embedder, k=K))
    runs["BM25"].append(bm25.search(query, k=K))
    runs["hybrid"].append(hybrid_search(query, embedder, bm25, k=K,
                                         candidate_k=CANDIDATES))
    runs["hybrid + reranker"].append(hybrid_reranked_search(
        query, embedder, bm25, reranker, k=K, candidate_k=CANDIDATES))
    gold.append(relevant)

print(f"queries: {len(cases)} | Hit Rate / MRR / Recall at {K} | "
      f"candidates before reranking: {CANDIDATES}")
print(f"{'setup':<20}{'Hit Rate':>11}{'MRR':>10}{'Recall':>11}")
for name, rankings in runs.items():
    metrics = aggregate_metrics(rankings, gold, k=K)
    print(f"{name:<20}{metrics[f'hit_rate@{K}']:>11.3f}"
          f"{metrics[f'mrr@{K}']:>10.3f}{metrics[f'recall@{K}']:>11.3f}")
