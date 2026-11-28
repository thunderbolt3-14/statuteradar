"""Create separate, blank Phase 4 label packets for two independent annotators."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from validate_golden_dataset import validate_cases


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "data" / "golden" / "cases.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "golden" / "annotations"
FIELDS = [
    "case_id",
    "scenario",
    "scenario_as_of_date",
    "profile_json",
    "category",
    "cited_provisions_json",
    "label",
    "rationale",
    "missing_facts_json",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    try:
        cases = validate_cases(args.cases)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        outputs = [args.output_dir / "annotator_a.csv", args.output_dir / "annotator_b.csv"]
        existing = [path for path in outputs if path.exists()]
        if existing:
            raise FileExistsError("Refusing to overwrite: " + ", ".join(map(str, existing)))

        rows = []
        for case in cases:
            rows.append(
                {
                    "case_id": case["case_id"],
                    "scenario": case["scenario"],
                    "scenario_as_of_date": case["scenario_as_of_date"] or "",
                    "profile_json": json.dumps(case["profile"], ensure_ascii=False),
                    "category": case["category"],
                    "cited_provisions_json": json.dumps(case["cited_provisions"], ensure_ascii=False),
                    "label": "",
                    "rationale": "",
                    "missing_facts_json": "",
                }
            )
        for path in outputs:
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
        print(f"Created two independent annotation packets with {len(rows)} cases each.")
        print("The predicate schema is intentionally omitted until Persons A and B agree on it.")
        for path in outputs:
            print(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
        return 0
    except (OSError, csv.Error, json.JSONDecodeError, ValueError) as exc:
        print(f"Could not prepare golden annotation packets: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
