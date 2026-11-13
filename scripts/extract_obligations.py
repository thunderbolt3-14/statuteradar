"""Extract grounded obligations from one corpus chunk.

Git Bash example (local model):
LLM_PROVIDER=ollama OLLAMA_EXTRACTION_MODEL=qwen2.5:3b \
  venv/Scripts/python.exe scripts/extract_obligations.py dpdp:s8:p7:pta
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from statuteradar.extraction.extractor import extract_chunk  # noqa: E402
from statuteradar.extraction.providers import ExtractionProviderError, make_provider  # noqa: E402
from statuteradar.retrieval.corpus import load_chunks  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("chunk_id", help="exact chunk ID from data/processed/chunks.jsonl")
parser.add_argument("--output", type=Path, help="optional path for the JSON result; defaults to stdout")
args = parser.parse_args()

chunks = load_chunks()
chunk = next((item for item in chunks if item.chunk_id == args.chunk_id), None)
if chunk is None:
    parser.error(f"unknown chunk ID: {args.chunk_id}")

try:
    result = extract_chunk(chunk, make_provider())
except (ExtractionProviderError, ValueError) as exc:
    parser.exit(1, f"extraction failed: {exc}\n")

serialized = result.model_dump_json(indent=2)
if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized + "\n", encoding="utf-8")
    print(f"saved extraction to {args.output}")
else:
    print(serialized)
