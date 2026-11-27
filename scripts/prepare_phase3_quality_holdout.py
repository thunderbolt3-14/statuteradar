"""Create blinded, source-only packets for the Phase 3 quality holdout v2.

The fixed sample is targeted and balanced across four instruments. It is diagnostic, not random
or representative. Both prior Phase 3 evaluation datasets are excluded.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
EXISTING_EVALS = [
    ROOT / "data" / "extraction_eval.json",
    ROOT / "data" / "extraction_eval_fresh_holdout.json",
]
MASTER_PACKET = ROOT / "data" / "annotation_packet.csv"
OUT_DIR = ROOT / "data" / "annotations"
MANIFEST = OUT_DIR / "phase3_quality_holdout_v2_manifest.json"
PACKET_A = OUT_DIR / "phase3_quality_holdout_v2_annotator_a.csv"
PACKET_B = OUT_DIR / "phase3_quality_holdout_v2_annotator_b.csv"

SELECTED_IDS = [
    # GDPR: response deadlines, design duty, consent withdrawal, and objection right.
    "gdpr:art12:p3",
    "gdpr:art25:p1",
    "gdpr:art7:p3",
    "gdpr:art21:p1",
    # DPDP Act: lawful-use permission, fiduciary responsibility, conditional accuracy,
    # and clear consent-request information.
    "dpdp:s4:p1",
    "dpdp:s8:p1",
    "dpdp:s8:p3",
    "dpdp:s6:p3",
    # DPDP Rules: standalone notice, optional registration, breach intimation, and child consent.
    "dpdp_rules:r3:pta",
    "dpdp_rules:r4:p1",
    "dpdp_rules:r7:p1",
    "dpdp_rules:r10:p1",
    # CCPA: collection notice, deletion-right disclosure, access right, and opt-out link.
    "ccpa:s1798.100:pa:pt1",
    "ccpa:s1798.105:pb",
    "ccpa:s1798.110:pa",
    "ccpa:s1798.135:pa:pt1",
]

ANNOTATION_COLUMNS = [
    "chunk_id",
    "instrument",
    "citation",
    "title",
    "source_text",
    "outcome",
    "modality",
    "actor",
    "action",
    "data_category",
    "condition_constraint_exception",
    "scope_qualifier",
    "evidence_quote",
    "uncertainty_notes",
]


def main() -> int:
    try:
        reused_ids = set()
        for eval_path in EXISTING_EVALS:
            existing = json.loads(eval_path.read_text(encoding="utf-8"))
            reused_ids.update(case["chunk_id"] for case in existing["cases"])
        duplicates = reused_ids.intersection(SELECTED_IDS)
        if duplicates:
            raise ValueError(f"Selected IDs overlap the existing evaluation: {sorted(duplicates)}")
        if len(SELECTED_IDS) != len(set(SELECTED_IDS)):
            raise ValueError("Selected ID list contains duplicates")

        chunks: dict[str, dict] = {}
        for line in CHUNKS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item["chunk_id"] in SELECTED_IDS:
                chunks[item["chunk_id"]] = item
        missing = set(SELECTED_IDS) - set(chunks)
        if missing:
            raise ValueError(f"Selected chunks missing from processed corpus: {sorted(missing)}")

        with MASTER_PACKET.open("r", encoding="utf-8-sig", newline="") as handle:
            master_rows = {row["chunk_id"]: row for row in csv.DictReader(handle)}
        rows: list[dict[str, str]] = []
        manifest_cases = []
        for chunk_id in SELECTED_IDS:
            item = chunks[chunk_id]
            if item.get("kind") != "operative":
                raise ValueError(f"{chunk_id} is not an operative provision")
            if chunk_id not in master_rows:
                raise ValueError(f"{chunk_id} is missing from the master annotation packet")
            source_text = item["text"]
            if (master_rows[chunk_id].get("source_text") or "").strip() != source_text.strip():
                raise ValueError(f"Source text mismatch between chunks and master for {chunk_id}")
            rows.append(
                {
                    "chunk_id": chunk_id,
                    "instrument": item["instrument"],
                    "citation": item["citation"],
                    "title": item.get("title") or "",
                    "source_text": source_text,
                    **{column: "" for column in ANNOTATION_COLUMNS[5:]},
                }
            )
            manifest_cases.append(
                {
                    "chunk_id": chunk_id,
                    "split": "test",
                    "instrument": item["instrument"],
                    "citation": item["citation"],
                }
            )

        counts = Counter(chunks[chunk_id]["instrument"] for chunk_id in SELECTED_IDS)
        if counts != Counter({"GDPR": 4, "DPDP": 4, "DPDP-Rules": 4, "CCPA": 4}):
            raise ValueError(f"Sample is not balanced across the four instruments: {dict(counts)}")

        outputs = [MANIFEST, PACKET_A, PACKET_B]
        existing_outputs = [path for path in outputs if path.exists()]
        if existing_outputs:
            raise FileExistsError(
                "Refusing to overwrite existing fresh-holdout files: "
                + ", ".join(str(path.relative_to(ROOT)) for path in existing_outputs)
            )

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        manifest = {
            "title": "StatuteRadar Phase 3 fresh held-out annotation sample",
            "version": 1,
            "sampling": "Targeted diagnostic sample, four operative provisions per instrument; not random or representative.",
            "excludes_existing_evaluation_ids": True,
            "cases": manifest_cases,
        }
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for path in (PACKET_A, PACKET_B):
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=ANNOTATION_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)

        print(f"Created {len(rows)} source-only cases: {dict(counts)}")
        print(f"Manifest: {MANIFEST.relative_to(ROOT)}")
        print(f"Annotator A packet: {PACKET_A.relative_to(ROOT)}")
        print(f"Annotator B packet: {PACKET_B.relative_to(ROOT)}")
        print("Both packets contain the same cases and blank annotation fields.")
        print("Keep annotators independent; do not tune or run models on these cases before adjudication.")
        return 0
    except (OSError, csv.Error, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Could not prepare fresh held-out packets: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
