"""Validate the Phase 4 scenario file without treating draft labels as gold."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "data" / "golden" / "cases.jsonl"
DEFAULT_CONFLICTS = ROOT / "data" / "golden" / "conflicts_golden.json"
ALLOWED_LABELS = {"CONFLICT", "COMPATIBLE", "INDEPENDENT", "NEEDS_REVIEW"}
ALLOWED_STATUSES = {"draft", "needs_review", "adjudicated"}
PROFILE_KEYS = {
    "organization_established_in",
    "data_subject_locations",
    "data_categories",
    "storage_locations",
    "transfers",
    "children_data",
    "sale_or_sharing",
}


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_cases(path: Path) -> list[dict[str, Any]]:
    records = []
    seen: set[str] = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        _expect(isinstance(case, dict), f"{path}:{line_no}: each JSONL line must be an object")

        case_id = case.get("case_id")
        _expect(isinstance(case_id, str) and case_id.strip(), f"{path}:{line_no}: missing case_id")
        _expect(case_id not in seen, f"{path}:{line_no}: duplicate case_id {case_id}")
        seen.add(case_id)

        for key in ("status", "split", "scenario", "profile", "category", "cited_provisions",
                    "gold_predicates", "label", "annotator_labels", "adjudicated_label",
                    "rationale", "missing_facts", "scenario_as_of_date"):
            _expect(key in case, f"{case_id}: missing required key {key}")

        _expect(isinstance(case["status"], str) and case["status"] in ALLOWED_STATUSES,
                f"{case_id}: unsupported status {case['status']!r}")
        _expect(case["split"] is None or (isinstance(case["split"], str) and case["split"] in {"dev", "test"}),
                f"{case_id}: split must be dev, test, or null")

        _expect(isinstance(case["scenario"], str) and case["scenario"].strip(),
                f"{case_id}: scenario must be non-empty text")
        profile = case["profile"]
        _expect(isinstance(profile, dict), f"{case_id}: profile must be an object")
        _expect(PROFILE_KEYS.issubset(profile), f"{case_id}: profile missing keys {sorted(PROFILE_KEYS - set(profile))}")
        for key in ("data_subject_locations", "data_categories", "storage_locations", "transfers"):
            _expect(isinstance(profile[key], list), f"{case_id}: profile.{key} must be a list")
        for key in ("children_data", "sale_or_sharing"):
            _expect(isinstance(profile[key], bool), f"{case_id}: profile.{key} must be boolean")

        citations = case["cited_provisions"]
        _expect(isinstance(citations, list) and citations, f"{case_id}: cited_provisions must be a non-empty list")
        for index, citation in enumerate(citations, start=1):
            _expect(isinstance(citation, dict) and isinstance(citation.get("instrument"), str)
                    and isinstance(citation.get("citation"), str),
                    f"{case_id}: cited_provisions[{index}] needs instrument and citation strings")

        _expect(isinstance(case["gold_predicates"], list), f"{case_id}: gold_predicates must be a list")
        _expect(isinstance(case["annotator_labels"], list), f"{case_id}: annotator_labels must be a list")
        _expect(isinstance(case["missing_facts"], list)
                and all(isinstance(item, str) for item in case["missing_facts"]),
                f"{case_id}: missing_facts must be a list of strings")

        scenario_date = case["scenario_as_of_date"]
        if scenario_date is not None:
            _expect(isinstance(scenario_date, str), f"{case_id}: scenario_as_of_date must be ISO date text or null")
            try:
                date.fromisoformat(scenario_date)
            except ValueError as exc:
                raise ValueError(f"{case_id}: invalid scenario_as_of_date {scenario_date!r}") from exc

        for key in ("label", "adjudicated_label"):
            label = case[key]
            _expect(label is None or (isinstance(label, str) and label in ALLOWED_LABELS),
                    f"{case_id}: unsupported {key} {label!r}")
        if case["label"] is not None or case["adjudicated_label"] is not None:
            _expect(scenario_date is not None,
                    f"{case_id}: do not label a case until scenario_as_of_date is specified")
        if case["status"] == "draft":
            _expect(case["label"] is None and case["adjudicated_label"] is None,
                    f"{case_id}: draft case cannot carry a gold/adjudicated label")
            _expect(case["split"] is None, f"{case_id}: draft case cannot be assigned to a scored split")
        elif case["status"] == "needs_review":
            _expect(case["label"] == "NEEDS_REVIEW" and case["adjudicated_label"] == "NEEDS_REVIEW",
                    f"{case_id}: needs_review case must carry NEEDS_REVIEW labels")
            _expect(bool(case["missing_facts"]),
                    f"{case_id}: needs_review case must list missing facts")
            _expect(isinstance(case["rationale"], str) and case["rationale"].strip(),
                    f"{case_id}: needs_review case must include a rationale")
            _expect(isinstance(case["adjudication_rationale"], str)
                    and case["adjudication_rationale"].strip(),
                    f"{case_id}: needs_review case must include an adjudication rationale")
            _expect(isinstance(case["annotator_labels"], list) and len(case["annotator_labels"]) == 2
                    and all(isinstance(label, str) and label in ALLOWED_LABELS
                            for label in case["annotator_labels"]),
                    f"{case_id}: needs_review case must preserve both annotator labels")
            _expect(case["split"] is None,
                    f"{case_id}: needs_review case cannot be assigned to a scored split")
        elif case["status"] == "adjudicated":
            _expect(case["adjudicated_label"] in {"CONFLICT", "COMPATIBLE", "INDEPENDENT"},
                    f"{case_id}: adjudicated case needs a final outcome label")
            _expect(case["label"] == case["adjudicated_label"],
                    f"{case_id}: label must match adjudicated_label")
            _expect(not case["missing_facts"],
                    f"{case_id}: adjudicated outcome cannot retain unresolved missing facts")
            _expect(isinstance(case["rationale"], str) and case["rationale"].strip(),
                    f"{case_id}: adjudicated case must include a rationale")
            _expect(isinstance(case["adjudication_rationale"], str)
                    and case["adjudication_rationale"].strip(),
                    f"{case_id}: adjudicated case must include an adjudication rationale")
            _expect(isinstance(case["annotator_labels"], list) and len(case["annotator_labels"]) == 2
                    and all(isinstance(label, str) and label in ALLOWED_LABELS
                            for label in case["annotator_labels"]),
                    f"{case_id}: adjudicated case must preserve both annotator labels")
        records.append(case)

    _expect(records, f"{path}: no case records found")
    return records


def validate_conflicts(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    _expect(isinstance(data, list), f"{path}: expected a JSON list")
    for index, conflict in enumerate(data, start=1):
        _expect(isinstance(conflict, dict), f"{path}: item {index} must be an object")
        _expect(isinstance(conflict.get("conflict_id"), str), f"{path}: item {index} missing conflict_id")
        value = conflict.get("is_jointly_unsatisfiable")
        _expect(value is None or isinstance(value, bool),
                f"{path}: {conflict['conflict_id']} is_jointly_unsatisfiable must be boolean or null")
        review_status = conflict.get("review_status", "")
        _expect(isinstance(review_status, str),
                f"{path}: {conflict['conflict_id']} review_status must be text")
        if review_status.startswith("candidate"):
            _expect(value is None, f"{path}: candidate {conflict['conflict_id']} must remain unlabeled")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--conflicts", type=Path, default=DEFAULT_CONFLICTS)
    args = parser.parse_args()
    try:
        cases = validate_cases(args.cases)
        conflicts = validate_conflicts(args.conflicts)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Golden dataset validation failed: {exc}", file=sys.stderr)
        return 1
    drafts = sum(case["status"] == "draft" for case in cases)
    print(f"Validated {len(cases)} scenario(s); {drafts} draft, {len(conflicts)} conflict candidate(s).")
    print("No draft labels were counted as gold; scenario dates and independent review remain required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
