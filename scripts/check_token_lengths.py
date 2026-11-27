"""Measure real word-piece lengths of every chunk against the embedding model's limit."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statuteradar.retrieval.corpus import load_chunks  # noqa: E402
from statuteradar.retrieval.diagnostics import token_report  # noqa: E402
from statuteradar.retrieval.embedder import SentenceTransformerEmbedder  # noqa: E402

print(token_report(load_chunks(), SentenceTransformerEmbedder()))