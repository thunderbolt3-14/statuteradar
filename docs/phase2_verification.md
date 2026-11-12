# Phase 2 verification: retrieval

Status: retrieval pipeline implemented and measured on the current corpus. The benchmark is a small, hand-written development set; it is not an independent or statistically conclusive evaluation.

## Runtime note

Use standalone CPython 3.12 on Windows for the ChromaDB HNSW extension. The project venv had been created from Anaconda's Python 3.12.10, which loaded the Anaconda standard library while using pip-installed HNSW wheels. In that runtime, HNSW vector insertion crashed with Windows access violation `0xC0000005`, including on synthetic vectors. Reinstalling the same wheel and changing `PATH` did not fix it. Rebasing the existing venv in place onto standalone CPython 3.12.10 fixed insertion; the venv and its installed packages were retained.

For a fresh checkout, install standalone Python with uv, create a venv from that interpreter, then install `requirements.txt`:

```powershell
uv python install 3.12.10 --install-dir .python --no-registry
.python\cpython-3.12.10-windows-x86_64-none\python.exe -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

The `.python/` runtime is ignored by Git. Requirements pin ChromaDB 0.5.15, chroma-hnswlib 0.7.6, and NumPy 1.26.4.

## Retrieval components

- Dense retrieval: Sentence Transformers `all-MiniLM-L6-v2` with Chroma cosine search.
- Sparse retrieval: BM25 over legal terms, numbers, citations and provision text.
- Hybrid retrieval: Reciprocal Rank Fusion with the standard `k = 60` constant.
- Reranking: `cross-encoder/ms-marco-MiniLM-L-6-v2` reranks the top 30 fused candidates.
- Evaluation: 20 hand-written development queries with relevant chunk IDs in `data/retrieval_eval.json`; macro Hit Rate@5, MRR@5 and Recall@5 are reported for each setup. No independently reviewed test split is available yet.
- Long embedding inputs: text exceeding MiniLM's 256-token limit is encoded as overlapping token windows and the window vectors are combined, preserving the original chunk ID and all text for dense retrieval. These vectors use the `statute_chunks_windowed` collection; the previous `statute_chunks` collection is retained.

Build the vector index once before running dense, hybrid or reranked searches:

```powershell
venv\Scripts\python.exe scripts/build_index.py
venv\Scripts\python.exe scripts/search_dense.py "how long to report a data breach" -k 5
venv\Scripts\python.exe scripts/search_dense.py "right to delete my data" --instrument CCPA
venv\Scripts\python.exe scripts/search_hybrid.py "how long to report a data breach" -k 5
venv\Scripts\python.exe scripts/search_hybrid.py "right to delete my data" --instrument CCPA --rerank
venv\Scripts\python.exe scripts/evaluate_retrieval.py --split development
```

## Current results

Full test suite: **41 passed**. Package consistency: `pip check` clean. The dense index contains 1,554 chunks, each represented by a 384-dimensional vector.

| Setup | Hit Rate@5 | MRR@5 | Recall@5 |
|---|---:|---:|---:|
| Dense | 0.200 | 0.127 | 0.150 |
| BM25 | 0.100 | 0.035 | 0.075 |
| Hybrid (RRF) | 0.200 | 0.096 | 0.150 |
| Hybrid + cross-encoder | 0.250 | 0.188 | 0.225 |

These figures describe only this 20-query set and do not establish general retrieval accuracy. The gold labels were created by one reviewer and should be independently checked before making a research claim. Repeated dense runs on rebuilt indexes varied (Hit Rate@5 0.7–0.8; MRR@5 0.487–0.553; Recall@5 0.600–0.650), so treat the current scores as preliminary and verify repeatability before drawing a comparison.

The tokenizer audit found 5 of 1,554 chunks (0.3%) above the embedding model's 256-word-piece input limit; the longest was 296. The embedding wrapper now handles these using overlapping windows and combines their vectors, rather than allowing Sentence Transformers to truncate their tails. BM25 continues to use the full chunk text. The active collection name was changed to `statute_chunks_windowed`, so rebuilding creates a new collection while preserving the previous `statute_chunks` index.

## Evaluation limitations and next annotation step

The current 20-query set is a development set from one reviewer; do not treat its scores as an independent test result. The evaluation script accepts `--split development`, `--split test`, or `--split all`. The existing cases are explicitly marked `single_reviewer`. Add new cases only after a second reviewer has checked the query and relevant provision IDs; mark those cases `independently_reviewed`, assign them to `test`, and do not tune against them. Until that review is complete, `--split test` intentionally has no eligible cases and exits with a clear message. The next evaluation improvement therefore requires independent legal/provision annotation, not generated labels.
