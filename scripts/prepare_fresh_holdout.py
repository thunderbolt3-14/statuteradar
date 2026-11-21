"""Create two blinded, source-only annotation packets for a fresh Phase 3 holdout.

The selected cases are a fixed, targeted diagnostic sample: four operative provisions from each
of GDPR, DPDP, DPDP Rules, and CCPA. This is not a random or statistically representative sample.
The script excludes every case already used by the Phase 3 development evaluation.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
EXISTING_EVAL = ROOT / "data" / "extraction_eval.json"
MASTER_PACKET = ROOT / "data" / "annotation_packet.csv"
OUT_DIR = ROOT / "data" / "annotations"
MANIFEST = OUT_DIR / "phase3_fresh_holdout_manifest.json"
PACKET_A = OUT_DIR / "phase3_holdout_annotator_a.csv"
PACKET_B = OUT_DIR / "phase3_holdout_annotator_b.csv"

SELECTED_IDS = [
    # GDPR: a duty, a right, a consent rule, and a carve-out.
    "gdpr:art32:p4",
    "gdpr:art15:p2",
    "gdpr:art7:p2",
    "gdpr:art22:p2",
    # DPDP Act: processor use, data principal right, exemption, and scope.
    "dpdp:s8:p2",
    "dpdp:s11:p1",
    "dpdp:s17:p1:ptc",
    "dpdp:s3:pta",
    # DPDP Rules: publication duty, transfer rule, exemption, and SDF obligation.
    "dpdp_rules:r9",
    "dpdp_rules:r15",
    "dpdp_rules:r16",
    "dpdp_rules:r13:p1",
    # CCPA: consumer right, contract safeguard, service provider limits, prohibition/exception.
    "ccpa:s1798.105:pa",
    "ccpa:s1798.100:pd:pt5",
    "ccpa:s1798.135:pf",
    "ccpa:s1798.148:pa:pt3",
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
        existing = json.loads(EXISTING_EVAL.read_text(encoding="utf-8"))
        reused_ids = {case["chunk_id"] for case in existing["cases"]}
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
        print("Do not tune prompts or run model evaluation on these cases until both packets are adjudicated.")
        return 0
    except (OSError, csv.Error, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Could not prepare fresh held-out packets: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
