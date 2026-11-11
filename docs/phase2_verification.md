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
- Evaluation: 10 hand-written queries with relevant chunk IDs in `data/retrieval_eval.json`; macro Hit Rate@5, MRR@5 and Recall@5 are reported for each setup.

Build the vector index once before running dense, hybrid or reranked searches:

```powershell
venv\Scripts\python.exe scripts/build_index.py
venv\Scripts\python.exe scripts/search_dense.py "how long to report a data breach" -k 5
venv\Scripts\python.exe scripts/search_dense.py "right to delete my data" --instrument CCPA
venv\Scripts\python.exe scripts/search_hybrid.py "how long to report a data breach" -k 5
venv\Scripts\python.exe scripts/search_hybrid.py "right to delete my data" --instrument CCPA --rerank
venv\Scripts\python.exe scripts/evaluate_retrieval.py
```

## Current results

Full test suite: **40 passed**. Package consistency: `pip check` clean. The dense index contains 1,554 chunks, each represented by a 384-dimensional vector.

| Setup | Hit Rate@5 | MRR@5 | Recall@5 |
|---|---:|---:|---:|
| Dense | 0.800 | 0.553 | 0.650 |
| BM25 | 0.600 | 0.433 | 0.433 |
| Hybrid (RRF) | 0.800 | 0.583 | 0.625 |
| Hybrid + cross-encoder | 0.900 | 0.645 | 0.692 |

These figures describe only this 10-query set and do not establish general retrieval accuracy. The gold labels were created by one reviewer and should be independently checked before making a research claim.

The tokenizer audit found 5 of 1,554 chunks (0.3%) above the embedding model's 256-word-piece input limit; the longest was 296. Sentence Transformers truncates those inputs, so their final words are not represented in the dense vectors. BM25 still indexes the full text. This is a known Phase 1 chunk-length limitation to address before treating dense retrieval as fully lossless.
