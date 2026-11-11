from __future__ import annotations

from collections import defaultdict
from statistics import mean

from ..ingest.schema import Chunk
from .corpus import embed_text


def _pct(values: list[int], q: float) -> int:
    v = sorted(values)
    return v[min(len(v) - 1, int(len(v) * q))]


def token_report(chunks: list[Chunk], embedder, with_header: bool = True) -> str:
    """Measure real word-piece lengths against the embedding model's input limit.

    Anything longer than max_seq_length is silently truncated by the model, i.e. the end of the
    chunk would not be represented in its embedding. This checks the Phase 1 budget estimate.
    """
    limit = embedder.max_seq_length
    full = embedder.token_counts([embed_text(c, with_header) for c in chunks])
    plain = embedder.token_counts([c.text for c in chunks])
    ratio = mean(p / max(c.token_count, 1) for p, c in zip(plain, chunks))

    by = defaultdict(list)
    for n, c in zip(full, chunks):
        by[c.instrument].append(n)
    over = sorted(((n, c) for n, c in zip(full, chunks) if limit and n > limit), key=lambda x: -x[0])

    out = [f"model: {embedder.name}   max_seq_length: {limit}   header in embedded text: {with_header}",
           f"chunks: {len(chunks)}   over the limit (truncated): {len(over)} ({100 * len(over) / len(chunks):.1f}%)",
           f"measured word-pieces per Phase-1 'approx token' (text only): {ratio:.2f}   (Phase 1 assumed ~1.2-1.3)",
           "", f"{'instrument':<12}{'chunks':>7}{'mean':>7}{'p95':>6}{'max':>6}{'over':>6}"]
    for inst, vals in by.items():
        out.append(f"{inst:<12}{len(vals):>7}{mean(vals):>7.0f}{_pct(vals, 0.95):>6}{max(vals):>6}"
                   f"{sum(1 for v in vals if limit and v > limit):>6}")
    if over:
        out += ["", "longest truncated chunks (word-pieces):"]
        out += [f"  {n:>4}  {c.citation}  [{c.chunk_id}]" for n, c in over[:10]]
    return "\n".join(out)