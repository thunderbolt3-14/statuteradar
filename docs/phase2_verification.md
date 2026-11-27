# Phase 2 verification: retrieval

Status: retrieval pipeline implemented and measured on the current corpus. The benchmark is a held-out test split of 20 independently reviewed queries; due to the small sample size, these scores are preliminary rather than conclusive. Phase 2 is now closed as a project milestone.

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
- Evaluation: 10 single-reviewer development queries and 20 held-out test queries marked `independently_reviewed` in `data/retrieval_eval.json`; macro Hit Rate@5, MRR@5 and Recall@5 are reported for each setup.
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

| Setup (held-out test split, N=20) | Hit Rate@5 | MRR@5 | Recall@5 |
|---|---:|---:|---:|
| Dense (current local rerun) | 0.150 | 0.077 | 0.100 |
| BM25 | 0.100 | 0.035 | 0.075 |
| Hybrid (RRF) | 0.200 | 0.096 | 0.150 |
| Hybrid + cross-encoder | 0.250 | 0.188 | 0.225 |

These metrics are from the 20-query held-out test split and are preliminary; they do not establish general retrieval accuracy. Two runs against the current local index both produced the dense result shown above. The original run recorded in PR #6 reported Dense Hit Rate@5 0.200, MRR@5 0.127 and Recall@5 0.150; the difference should be investigated before comparing systems or making a research claim. The cases are marked as independently reviewed in the dataset and in PR #6, but the repository does not record annotator agreement or an adjudication log.

The tokenizer audit found 5 of 1,554 chunks (0.3%) above the embedding model's 256-word-piece input limit; the longest was 296. The embedding wrapper now handles these using overlapping windows and combines their vectors, rather than allowing Sentence Transformers to truncate their tails. BM25 continues to use the full chunk text. The active collection name was changed to `statute_chunks_windowed`, so rebuilding creates a new collection while preserving the previous `statute_chunks` index.

## Evaluation limitations and next annotation step

The dataset contains 10 development cases marked `single_reviewer` and 20 test cases marked `independently_reviewed`. The evaluation script accepts `--split development`, `--split test`, or `--split all`; test runs include only cases with the independent-review marker. Do not tune retrieval settings against the test split. For stronger research claims, preserve the independent annotation/adjudication record, report inter-annotator agreement if available, and expand the held-out set in a future evaluation.
