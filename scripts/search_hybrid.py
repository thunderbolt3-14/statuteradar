"""Search with dense, BM25, or fused retrieval; optionally rerank the shortlist."""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statuteradar.retrieval.bm25 import BM25Retriever  # noqa: E402
from statuteradar.retrieval.corpus import load_chunks  # noqa: E402
from statuteradar.retrieval.embedder import make_embedder  # noqa: E402
from statuteradar.retrieval.reranker import CrossEncoderReranker  # noqa: E402
from statuteradar.retrieval.search import hybrid_search, hybrid_reranked_search  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("query")
parser.add_argument("-k", type=int, default=5)
parser.add_argument("--candidates", type=int, default=30)
parser.add_argument("--instrument", choices=["GDPR", "DPDP", "DPDP-Rules", "CCPA"])
parser.add_argument("--bm25-only", action="store_true")
parser.add_argument("--rerank", action="store_true", help="rerank the hybrid shortlist with the cross-encoder")
args = parser.parse_args()

chunks = load_chunks()
bm25 = BM25Retriever(chunks)
where = {"instrument": args.instrument} if args.instrument else None
if args.bm25_only:
    hits = bm25.search(args.query, k=args.k, where=where)
elif args.rerank:
    hits = hybrid_reranked_search(args.query, make_embedder(), bm25,
                                  CrossEncoderReranker(), k=args.k,
                                  candidate_k=args.candidates, where=where)
else:
    hits = hybrid_search(args.query, make_embedder(), bm25, k=args.k,
                         candidate_k=args.candidates, where=where)

for hit in hits:
    print(f"\n#{hit.rank}  {hit.score:.4f}  {hit.citation}   [{hit.chunk_id}]\n    "
          f"{hit.text[:220]}{' ...' if len(hit.text) > 220 else ''}")
