"""Build a reviewed JSONL candidate from two packets and adjudication rows.

This tool writes a new output file and never edits the source packets or cases file.
It does not certify legal correctness; a separate reviewer must inspect the result.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.compare_golden_annotations import IDENTITY_FIELDS, LABELS, read_packet
from scripts.validate_golden_dataset import validate_cases


ADJUDICATION_FIELDS = {
    "case_id",
    "label_a",
    "rationale_a",
    "label_b",
    "rationale_b",
    "adjudicated_label",
    "adjudication_rationale",
}


def read_adjudication(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not ADJUDICATION_FIELDS.issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name} is missing required adjudication columns")
        for line_number, row in enumerate(reader, start=2):
            case_id = (row.get("case_id") or "").strip()
            if not case_id:
                raise ValueError(f"{path.name}: blank case_id on line {line_number}")
            if case_id in rows:
                raise ValueError(f"{path.name}: duplicate adjudication for {case_id}")
            rows[case_id] = row
    return rows


def finalize_records(
    cases: list[dict],
    packet_a: dict[str, dict[str, str]],
    packet_b: dict[str, dict[str, str]],
    adjudications: dict[str, dict[str, str]],
) -> list[dict]:
    case_by_id = {case["case_id"]: case for case in cases}
    if set(case_by_id) != set(packet_a) or set(case_by_id) != set(packet_b):
        raise ValueError("case IDs must match exactly across cases.jsonl and both annotator packets")
    if not set(adjudications).issubset(case_by_id):
        raise ValueError("adjudication file contains unknown case IDs")

    output = []
    dataset_dates: set[str] = set()
    for case_id, original in case_by_id.items():
        a, b = packet_a[case_id], packet_b[case_id]
        for field in IDENTITY_FIELDS:
            if a.get(field) != b.get(field):
                raise ValueError(f"{case_id}: annotator packets differ in locked field {field}")
        if a.get("scenario") != original["scenario"]:
            raise ValueError(f"{case_id}: scenario differs from canonical case file")
        try:
            profile_a = json.loads(a.get("profile_json") or "")
            citations_a = json.loads(a.get("cited_provisions_json") or "")
        except json.JSONDecodeError as exc:
            raise ValueError(f"{case_id}: profile/citations must be valid JSON") from exc
        if (
            profile_a != original["profile"]
            or citations_a != original["cited_provisions"]
            or a.get("category") != original["category"]
        ):
            raise ValueError(f"{case_id}: category, profile, or citations differ from canonical case file")
        try:
            scenario_date = date.fromisoformat((a.get("scenario_as_of_date") or "").strip())
        except ValueError as exc:
            raise ValueError(f"{case_id}: scenario_as_of_date must be an ISO date") from exc
        if original["scenario_as_of_date"] not in (None, scenario_date.isoformat()):
            raise ValueError(f"{case_id}: packet scenario date differs from canonical case file")
        dataset_dates.add(scenario_date.isoformat())

        label_a = (a.get("label") or "").strip()
        label_b = (b.get("label") or "").strip()
        if label_a not in LABELS or label_b not in LABELS:
            raise ValueError(f"{case_id}: annotator labels must be completed before finalization")
        try:
            missing_a = json.loads(a.get("missing_facts_json") or "")
            missing_b = json.loads(b.get("missing_facts_json") or "")
        except json.JSONDecodeError as exc:
            raise ValueError(f"{case_id}: missing_facts_json must be a JSON list") from exc
        for label, missing in ((label_a, missing_a), (label_b, missing_b)):
            if not isinstance(missing, list) or any(not isinstance(item, str) for item in missing):
                raise ValueError(f"{case_id}: missing_facts_json must be a JSON list of strings")
            if label == "NEEDS_REVIEW" and not missing:
                raise ValueError(f"{case_id}: NEEDS_REVIEW requires a specific missing fact")

        adjudication = adjudications.get(case_id)
        if label_a != label_b and adjudication is None:
            raise ValueError(f"{case_id}: annotator disagreement needs an adjudication row")
        if adjudication is not None:
            if adjudication["label_a"].strip() != label_a or adjudication["label_b"].strip() != label_b:
                raise ValueError(f"{case_id}: adjudication row does not match the source packets")
            adjudicated_label = (adjudication.get("adjudicated_label") or "").strip()
            adjudication_rationale = (adjudication.get("adjudication_rationale") or "").strip()
            if adjudicated_label not in LABELS or not adjudication_rationale:
                raise ValueError(f"{case_id}: adjudicated label and rationale are required")
        else:
            adjudicated_label = label_a
            adjudication_rationale = "Both annotators independently selected the same label."

        annotator_missing_facts = [sorted(set(missing_a)), sorted(set(missing_b))]
        missing_facts = sorted(set(missing_a) | set(missing_b))
        if adjudicated_label != "NEEDS_REVIEW" and missing_facts:
            if adjudication is None or not adjudication_rationale:
                raise ValueError(f"{case_id}: resolving annotated missing facts requires explicit adjudication")
            missing_facts = []

        if adjudication is None:
            adjudication_rationale = "Consensus; see the two annotator rationales."
            rationale = (
                f"Annotator A: {a['rationale'].strip()}\n"
                f"Annotator B: {b['rationale'].strip()}"
            )
        else:
            rationale = adjudication_rationale

        record = deepcopy(original)
        record.update(
            {
                "status": "needs_review" if adjudicated_label == "NEEDS_REVIEW" else "adjudicated",
                "split": None,
                "scenario_as_of_date": scenario_date.isoformat(),
                "label": adjudicated_label,
                "annotator_labels": [label_a, label_b],
                "annotator_rationales": [a["rationale"].strip(), b["rationale"].strip()],
                "adjudicated_label": adjudicated_label,
                "rationale": rationale,
                "adjudication_rationale": adjudication_rationale,
                "annotator_missing_facts": annotator_missing_facts,
                "missing_facts": missing_facts if adjudicated_label == "NEEDS_REVIEW" else [],
            }
        )
        output.append(record)

    if len(dataset_dates) != 1:
        raise ValueError("all cases must use one consistent scenario_as_of_date")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "data" / "golden" / "cases.jsonl")
    parser.add_argument("--packet-a", type=Path, required=True)
    parser.add_argument("--packet-b", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise FileExistsError(f"Refusing to overwrite existing output: {args.output}")
        cases = validate_cases(args.cases)
        result = finalize_records(
            cases,
            read_packet(args.packet_a),
            read_packet(args.packet_b),
            read_adjudication(args.adjudication),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in result),
            encoding="utf-8",
        )
    except (OSError, csv.Error, json.JSONDecodeError, ValueError) as exc:
        print(f"Could not finalize golden annotations: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {len(result)} reviewed case records to {args.output}")
    print("Run validate_golden_dataset.py on the output before review or scoring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
