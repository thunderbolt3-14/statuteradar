import json
from pathlib import Path

import pytest

from scripts.validate_golden_dataset import validate_cases, validate_conflicts
from scripts.compare_golden_annotations import kappa


ROOT = Path(__file__).resolve().parents[1]


def test_seed_cases_are_valid_drafts_with_dates_unset():
    cases = validate_cases(ROOT / "data" / "golden" / "cases.jsonl")

    assert len(cases) == 10
    assert len({case["case_id"] for case in cases}) == 10
    assert all(case["status"] == "draft" for case in cases)
    assert all(case["label"] is None for case in cases)
    assert all(case["adjudicated_label"] is None for case in cases)
    assert all(case["scenario_as_of_date"] is None for case in cases)


def test_unreviewed_conflict_candidate_stays_unlabeled():
    conflicts = validate_conflicts(ROOT / "data" / "golden" / "conflicts_golden.json")

    assert len(conflicts) == 1
    assert conflicts[0]["is_jointly_unsatisfiable"] is None


def test_labeled_case_requires_scenario_date(tmp_path):
    case = {
        "case_id": "case-x",
        "status": "adjudicated",
        "split": None,
        "scenario": "Example",
        "profile": {
            "organization_established_in": "IN",
            "data_subject_locations": [],
            "data_categories": [],
            "storage_locations": [],
            "transfers": [],
            "children_data": False,
            "sale_or_sharing": False,
        },
        "category": "example",
        "cited_provisions": [{"instrument": "X", "citation": "Section 1"}],
        "gold_predicates": [],
        "label": "COMPATIBLE",
        "annotator_labels": ["COMPATIBLE", "COMPATIBLE"],
        "adjudicated_label": "COMPATIBLE",
        "rationale": "Example rationale",
        "adjudication_rationale": "The example labels agree.",
        "missing_facts": [],
        "scenario_as_of_date": None,
    }
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(case) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="scenario_as_of_date"):
        validate_cases(path)


def test_cohen_kappa_uses_independent_label_counts():
    value, observed, expected = kappa(
        ["CONFLICT", "COMPATIBLE", "INDEPENDENT"],
        ["CONFLICT", "INDEPENDENT", "INDEPENDENT"],
    )

    assert observed == pytest.approx(2 / 3)
    assert expected == pytest.approx(1 / 3)
    assert value == pytest.approx(0.5)


def test_cohen_kappa_is_undefined_when_expected_agreement_is_one():
    value, observed, expected = kappa(["COMPATIBLE"], ["COMPATIBLE"])

    assert value is None
    assert observed == expected == 1
