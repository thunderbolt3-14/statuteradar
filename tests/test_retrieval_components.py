from statuteradar.retrieval.bm25 import BM25Retriever, tokenize
from statuteradar.retrieval.evaluation import (
    aggregate_metrics,
    hit_rate_at_k,
    reciprocal_rank_at_k,
    recall_at_k,
)
from statuteradar.retrieval.fusion import reciprocal_rank_fusion
from statuteradar.retrieval.reranker import CrossEncoderReranker
from statuteradar.retrieval.types import Hit
from test_retrieval_index import CHUNKS


def hit(chunk_id, rank=1, score=0.0):
    return Hit(chunk_id=chunk_id, score=score, citation=chunk_id,
               instrument="GDPR", text=chunk_id, rank=rank)


def test_tokenize_preserves_legal_words_and_numbers():
    assert tokenize("Data Fiduciary: 72-hours; section 8(6)") == [
        "data", "fiduciary", "72-hours", "section", "8", "6"
    ]


def test_bm25_ranks_exact_terms_and_applies_metadata_filter():
    retriever = BM25Retriever(CHUNKS)
    hits = retriever.search("breach authority 72 hours", k=3)
    assert hits[0].chunk_id == "gdpr:art33"
    filtered = retriever.search("personal data breach", k=5,
                                where={"instrument": "DPDP-Rules"})
    assert [h.chunk_id for h in filtered] == ["rules:r7"]


def test_rrf_combines_rankings_and_deduplicates_within_each_run():
    fused = reciprocal_rank_fusion([
        [hit("a", 1), hit("a", 2), hit("b", 3)],
        [hit("b", 1), hit("c", 2)],
    ], k=60)
    assert [h.chunk_id for h in fused] == ["b", "a", "c"]
    assert fused[0].score == 1 / 63 + 1 / 61
    assert [h.rank for h in fused] == [1, 2, 3]


def test_retrieval_metrics_at_k():
    ranking = [hit("a"), hit("gold"), hit("b")]
    gold = {"gold", "also-gold"}
    assert hit_rate_at_k(ranking, gold, 2) == 1.0
    assert reciprocal_rank_at_k(ranking, gold, 2) == 0.5
    assert recall_at_k(ranking, gold, 2) == 0.5
    assert aggregate_metrics([ranking], [gold], 2) == {
        "hit_rate@2": 1.0, "mrr@2": 0.5, "recall@2": 0.5
    }


def test_reranker_sorts_by_cross_encoder_scores():
    reranker = object.__new__(CrossEncoderReranker)

    class FakeModel:
        def predict(self, pairs, show_progress_bar=False):
            return [0.2, 0.9]

    reranker.model = FakeModel()
    ranked = reranker.rerank("question", [hit("lower"), hit("higher")])
    assert [h.chunk_id for h in ranked] == ["higher", "lower"]
    assert [h.rank for h in ranked] == [1, 2]
