"""Quick look at dense (vector-only) retrieval.

python scripts/search_dense.py "how long to report a data breach" -k 5
python scripts/search_dense.py "right to delete my data" --instrument GDPR
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statuteradar.retrieval.embedder import make_embedder  # noqa: E402
from statuteradar.retrieval.index import dense_search  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("query")
ap.add_argument("-k", type=int, default=5)
ap.add_argument("--instrument", choices=["GDPR", "DPDP", "DPDP-Rules", "CCPA"])
a = ap.parse_args()

hits = dense_search(a.query, make_embedder(), k=a.k, where={"instrument": a.instrument} if a.instrument else None)
for h in hits:
    print(f"\n#{h.rank}  {h.score:.3f}  {h.citation}   [{h.chunk_id}]\n    {h.text[:220]}{' ...' if len(h.text) > 220 else ''}")