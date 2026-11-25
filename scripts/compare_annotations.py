"""Compare the two blinded Phase 3 annotation packets without editing them."""

from __future__ import annotations

import csv
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET_A = ROOT / "data" / "annotations" / "annotation_packet_filled_nagasai.csv"
PACKET_B = ROOT / "data" / "annotations" / "annotation_packet_rahul.csv"
MASTER = ROOT / "data" / "annotation_packet.csv"
DISAGREEMENTS = ROOT / "data" / "annotations" / "annotation_disagreements.csv"
SUMMARY = ROOT / "data" / "annotations" / "annotation_comparison_summary.json"
IDENTITY_COLUMNS = {"chunk_id", "source_text", "instrument", "citation", "title"}
REQUIRED_COLUMNS = {"chunk_id", "source_text"}
KAPPA_FIELDS = {"outcome"}
NOTE_FIELD = "uncertainty_notes"


def normalize(value: str | None) -> str:
    """Normalize casing and whitespace only; preserve wording and punctuation."""
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def load_packet(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required annotation file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        if not REQUIRED_COLUMNS.issubset(columns):
            raise ValueError(f"{path.name} must include chunk_id and source_text columns")
        records: dict[str, dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            chunk_id = (row.get("chunk_id") or "").strip()
            if not chunk_id:
                raise ValueError(f"{path.name}: blank chunk_id on CSV line {line_number}")
            if chunk_id in records:
                raise ValueError(f"{path.name}: duplicate chunk_id {chunk_id!r}")
            records[chunk_id] = row
    return columns, records


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    count = len(pairs)
    observed = sum(left == right for left, right in pairs) / count
    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    expected = sum(
        (left_counts[label] / count) * (right_counts[label] / count)
        for label in left_counts.keys() | right_counts.keys()
    )
    if expected == 1:
        return None
    return round((observed - expected) / (1 - expected), 4)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-a", type=Path, default=PACKET_A)
    parser.add_argument("--packet-b", type=Path, default=PACKET_B)
    parser.add_argument("--master", type=Path, default=MASTER,
                        help="optional full source packet used to verify source text")
    parser.add_argument("--manifest", type=Path,
                        help="optional JSON manifest whose case IDs must match both packets")
    parser.add_argument("--disagreements", type=Path, default=DISAGREEMENTS)
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    args = parser.parse_args()
    try:
        columns_a, annotator_a = load_packet(args.packet_a)
        columns_b, annotator_b = load_packet(args.packet_b)
        master = load_packet(args.master)[1] if args.master else {}

        if set(annotator_a) != set(annotator_b):
            raise ValueError("Annotator files have different chunk_id sets")
        if master and not set(annotator_a).issubset(master):
            raise ValueError("One or more annotator chunk IDs are absent from the master packet")
        if args.manifest:
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            manifest_ids = {case["chunk_id"] for case in manifest["cases"]}
            if set(annotator_a) != manifest_ids:
                raise ValueError("Annotator chunk IDs do not match the manifest")

        fields_a = set(columns_a) - IDENTITY_COLUMNS
        fields_b = set(columns_b) - IDENTITY_COLUMNS
        if fields_a != fields_b:
            raise ValueError("Annotator files have different annotation columns")
        annotation_fields = [
            c for c in columns_a if c not in IDENTITY_COLUMNS and c != NOTE_FIELD
        ]
        annotated_a = {
            chunk_id for chunk_id, row in annotator_a.items()
            if any(normalize(row.get(field)) for field in annotation_fields)
        }
        annotated_b = {
            chunk_id for chunk_id, row in annotator_b.items()
            if any(normalize(row.get(field)) for field in annotation_fields)
        }
        jointly_annotated = annotated_a & annotated_b
        note_differences = sum(
            normalize(annotator_a[chunk_id].get(NOTE_FIELD))
            != normalize(annotator_b[chunk_id].get(NOTE_FIELD))
            for chunk_id in jointly_annotated
        )

        disagreement_rows: list[dict[str, str]] = []
        summary: dict[str, object] = {
            "annotator_a_file": str(args.packet_a),
            "annotator_b_file": str(args.packet_b),
            "total_chunks_in_packet": len(annotator_a),
            "chunks_with_annotations_a": len(annotated_a),
            "chunks_with_annotations_b": len(annotated_b),
            "chunks_annotated_by_both": len(jointly_annotated),
            "normalization": "trim/collapse whitespace and casefold; punctuation is preserved",
            "fields": {},
            "cohen_kappa": {},
            "uncertainty_note_differences_not_counted_as_label_disagreements": note_differences,
            "disagreement_count": 0,
        }

        for chunk_id in sorted(annotator_a):
            row_a, row_b = annotator_a[chunk_id], annotator_b[chunk_id]
            source = (row_a.get("source_text") or "").strip()
            if (row_b.get("source_text") or "").strip() != source:
                raise ValueError(f"Source text differs between annotators for {chunk_id}")
            if master and (master[chunk_id].get("source_text") or "").strip() != source:
                raise ValueError(f"Source text differs from master for {chunk_id}")

        for field in annotation_fields:
            both_blank = both_filled = exact_match = different = a_only = b_only = 0
            labelled_pairs: list[tuple[str, str]] = []
            for chunk_id in sorted(annotator_a):
                row_a, row_b = annotator_a[chunk_id], annotator_b[chunk_id]
                source = (row_a.get("source_text") or "").strip()
                raw_a, raw_b = row_a.get(field, "") or "", row_b.get(field, "") or ""
                norm_a, norm_b = normalize(raw_a), normalize(raw_b)
                if not norm_a and not norm_b:
                    both_blank += 1
                    continue
                if norm_a and norm_b:
                    both_filled += 1
                    labelled_pairs.append((norm_a, norm_b))
                    if norm_a == norm_b:
                        exact_match += 1
                    else:
                        different += 1
                elif norm_a:
                    a_only += 1
                    different += 1
                else:
                    b_only += 1
                    different += 1

                if norm_a != norm_b:
                    disagreement_rows.append(
                        {
                            "chunk_id": chunk_id,
                            "field": field,
                            "source_text": source,
                            "annotator_a": raw_a,
                            "annotator_b": raw_b,
                            "adjudicated_value": "",
                            "adjudication_note": "",
                        }
                    )

            field_result: dict[str, object] = {
                "both_blank": both_blank,
                "both_filled": both_filled,
                "exact_match_when_both_filled": exact_match,
                "different_or_one_sided": different,
                "annotator_a_only": a_only,
                "annotator_b_only": b_only,
                "exact_agreement_rate_when_both_filled": (
                    round(exact_match / both_filled, 4) if both_filled else None
                ),
            }
            if field in KAPPA_FIELDS:
                field_result["cohen_kappa"] = cohen_kappa(labelled_pairs)
                summary["cohen_kappa"][field] = field_result["cohen_kappa"]
            summary["fields"][field] = field_result

        summary["disagreement_count"] = len(disagreement_rows)
        args.disagreements.parent.mkdir(parents=True, exist_ok=True)
        with args.disagreements.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "chunk_id", "field", "source_text", "annotator_a", "annotator_b",
                    "adjudicated_value", "adjudication_note",
                ],
            )
            writer.writeheader()
            writer.writerows(disagreement_rows)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        print(
            f"Compared {len(jointly_annotated)} jointly annotated chunks "
            f"across {len(annotation_fields)} label fields "
            f"({len(annotator_a)} total packet rows)."
        )
        print(f"Field-level disagreements needing adjudication: {len(disagreement_rows)}")
        for field, result in summary["fields"].items():
            print(
                f"{field}: exact agreement among jointly filled="
                f"{result['exact_agreement_rate_when_both_filled']}; "
                f"one-sided/different={result['different_or_one_sided']}"
            )
        print(f"Disagreements: {args.disagreements}")
        print(f"Summary: {args.summary}")
        return 0
    except (OSError, csv.Error, ValueError) as exc:
        print(f"Annotation comparison failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
