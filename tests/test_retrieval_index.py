"""Index + dense search tests. They use a toy embedder, so no model download is needed."""
import pytest

pytest.importorskip("chromadb")

from statuteradar.ingest.schema import Chunk  # noqa: E402
from statuteradar.retrieval.embedder import HashingEmbedder  # noqa: E402
from statuteradar.retrieval.index import build_index, chunk_meta, dense_search  # noqa: E402


def mk(cid, instrument, text, cit, title=None, phase=None):
    return Chunk(chunk_id=cid, instrument=instrument, jurisdiction="EU", kind="operative", unit_id=cid.split(":")[0],
                 citation=cit, hierarchy=[cit], title=title, text=text, token_count=len(text.split()),
                 commencement_phase=phase, source_file="x", source_sha256="y", char_start=0, char_end=1)


CHUNKS = [
    mk("gdpr:art17", "GDPR", "The data subject shall have the right to erasure of personal data without undue delay", "GDPR Art. 17(1)", "Right to erasure"),
    mk("gdpr:art33", "GDPR", "The controller shall notify the supervisory authority of a personal data breach within 72 hours", "GDPR Art. 33(1)"),
    mk("dpdp:s9", "DPDP", "A Data Fiduciary shall obtain verifiable consent of the parent before processing personal data of a child", "DPDP s.9(1)"),
    mk("ccpa:s1798.105", "CCPA", "A consumer shall have the right to request that a business delete personal information", "CCPA \u00a71798.105(a)"),
    mk("rules:r7", "DPDP-Rules", "intimation of personal data breach to the Board within seventy-two hours", "DPDP-Rules r.7(2)", phase=3),
]


def test_build_and_dense_search_finds_relevant_chunk(tmp_path):
    emb = HashingEmbedder()
    assert build_index(CHUNKS, emb, tmp_path) == 5
    top = dense_search("notify authority of personal data breach within 72 hours", emb, k=3, persist_dir=tmp_path)
    assert top[0].chunk_id == "gdpr:art33"
    assert [h.rank for h in top] == [1, 2, 3]
    assert top[0].score >= top[1].score >= top[2].score


def test_metadata_filter_restricts_results(tmp_path):
    emb = HashingEmbedder()
    build_index(CHUNKS, emb, tmp_path)
    hits = dense_search("personal data breach", emb, k=5, where={"instrument": "DPDP-Rules"}, persist_dir=tmp_path)
    assert [h.chunk_id for h in hits] == ["rules:r7"]


def test_rebuild_replaces_instead_of_duplicating(tmp_path):
    emb = HashingEmbedder()
    build_index(CHUNKS, emb, tmp_path)
    assert build_index(CHUNKS, emb, tmp_path) == 5


def test_chunk_meta_omits_none_values():
    m = chunk_meta(CHUNKS[1])
    assert "title" not in m and "commencement_phase" not in m
    assert chunk_meta(CHUNKS[4])["commencement_phase"] == 3


def test_token_report_flags_chunks_over_the_model_limit():
    from statuteradar.retrieval.diagnostics import token_report

    class Fake:
        name, max_seq_length = "fake", 12

        def token_counts(self, texts):
            return [len(t.split()) for t in texts]

    short = mk("a:1", "GDPR", "one two three", "GDPR Art. 1(1)")
    long_ = mk("a:2", "GDPR", " ".join(["word"] * 40), "GDPR Art. 2(1)")
    report = token_report([short, long_], Fake())
    assert "over the limit (truncated): 1 (50.0%)" in report
    assert "GDPR Art. 2(1)" in report