"""Compare independent Phase 4 labels and calculate Cohen's kappa."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LABELS = {"CONFLICT", "COMPATIBLE", "INDEPENDENT", "NEEDS_REVIEW"}
REQUIRED = {"case_id", "label", "rationale", "missing_facts_json"}
IDENTITY_FIELDS = {
    "scenario",
    "scenario_as_of_date",
    "profile_json",
    "category",
    "cited_provisions_json",
}


def read_packet(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name} needs columns {sorted(REQUIRED)}")
        rows = {}
        for line_number, row in enumerate(reader, start=2):
            case_id = (row.get("case_id") or "").strip()
            if not case_id:
                raise ValueError(f"{path.name}: blank case_id on line {line_number}")
            if case_id in rows:
                raise ValueError(f"{path.name}: duplicate case_id {case_id}")
            label = (row.get("label") or "").strip()
            if label not in LABELS:
                raise ValueError(f"{path.name}: {case_id} has invalid/blank label {label!r}")
            if not (row.get("rationale") or "").strip():
                raise ValueError(f"{path.name}: {case_id} needs a short rationale")
            try:
                missing_facts = json.loads(row.get("missing_facts_json") or "")
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}: {case_id} missing_facts_json is invalid JSON") from exc
            if not isinstance(missing_facts, list) or any(not isinstance(item, str) for item in missing_facts):
                raise ValueError(f"{path.name}: {case_id} missing_facts_json must be a JSON list of strings")
            if label == "NEEDS_REVIEW" and not missing_facts:
                raise ValueError(f"{path.name}: {case_id} NEEDS_REVIEW requires a missing fact or review question")
            rows[case_id] = row
    if not rows:
        raise ValueError(f"{path.name}: packet has no cases")
    return rows


def kappa(labels_a: list[str], labels_b: list[str]) -> tuple[float | None, float, float]:
    n = len(labels_a)
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / n
    counts_a, counts_b = Counter(labels_a), Counter(labels_b)
    categories = set(counts_a) | set(counts_b)
    expected = sum((counts_a[label] / n) * (counts_b[label] / n) for label in categories)
    if expected == 1:
        return None, observed, expected
    return (observed - expected) / (1 - expected), observed, expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-a", type=Path, required=True)
    parser.add_argument("--packet-b", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--disagreements", type=Path, required=True)
    parser.add_argument("--adjudication-template", type=Path, required=True)
    args = parser.parse_args()
    try:
        a, b = read_packet(args.packet_a), read_packet(args.packet_b)
        if set(a) != set(b):
            raise ValueError(
                f"case IDs differ: only A={sorted(set(a) - set(b))}; only B={sorted(set(b) - set(a))}"
            )
        case_ids = sorted(a)
        for case_id in case_ids:
            for field in IDENTITY_FIELDS:
                if a[case_id].get(field) != b[case_id].get(field):
                    raise ValueError(f"{case_id}: annotator packets differ in locked field {field}")
        labels_a = [(a[case_id]["label"] or "").strip() for case_id in case_ids]
        labels_b = [(b[case_id]["label"] or "").strip() for case_id in case_ids]
        agreement, observed, expected = kappa(labels_a, labels_b)
        disagreements = [
            {
                "case_id": case_id,
                "label_a": a[case_id]["label"],
                "rationale_a": a[case_id]["rationale"],
                "label_b": b[case_id]["label"],
                "rationale_b": b[case_id]["rationale"],
            }
            for case_id in case_ids
            if a[case_id]["label"].strip() != b[case_id]["label"].strip()
        ]
        for path in (args.summary, args.disagreements, args.adjudication_template):
            if path.exists():
                raise FileExistsError(f"Refusing to overwrite existing output: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)

        summary: dict[str, Any] = {
            "case_count": len(case_ids),
            "label_categories": sorted(LABELS),
            "annotator_a_distribution": dict(sorted(Counter(labels_a).items())),
            "annotator_b_distribution": dict(sorted(Counter(labels_b).items())),
            "exact_label_agreement": round(observed, 6),
            "cohen_kappa": None if agreement is None else round(agreement, 6),
            "kappa_note": "undefined because expected agreement is 1" if agreement is None else None,
            "disagreement_count": len(disagreements),
            "scope_note": "Label agreement only; predicate-field agreement is not computed until its schema is frozen.",
        }
        args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        fields = ["case_id", "label_a", "rationale_a", "label_b", "rationale_b"]
        with args.disagreements.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(disagreements)
        adjudication_fields = [*fields, "adjudicated_label", "adjudication_rationale"]
        with args.adjudication_template.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=adjudication_fields)
            writer.writeheader()
            for row in disagreements:
                writer.writerow({**row, "adjudicated_label": "", "adjudication_rationale": ""})
    except (OSError, csv.Error, json.JSONDecodeError, ValueError) as exc:
        print(f"Golden annotation comparison failed: {exc}", file=sys.stderr)
        return 1

    print(f"Compared {len(case_ids)} cases; label disagreements={len(disagreements)}.")
    print(f"Exact agreement={summary['exact_label_agreement']}; Cohen's kappa={summary['cohen_kappa']}")
    print(f"Summary: {args.summary}")
    print(f"Disagreements: {args.disagreements}")
    print(f"Adjudication template: {args.adjudication_template}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
