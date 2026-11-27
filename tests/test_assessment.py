from datetime import date

from statuteradar.analysis.assessment import (
    AssessmentRequest,
    CompatibleOption,
    ObligationEvidence,
    assess_case,
)


def obligation(rule_id, jurisdiction, modality, **overrides):
    values = {
        "rule_id": rule_id,
        "instrument": f"Synthetic {jurisdiction} code",
        "jurisdiction": jurisdiction,
        "citation": f"Synthetic citation {rule_id}",
        "source_chunk_id": f"synthetic:{rule_id}",
        "evidence_quote": f"Synthetic quote for {rule_id}.",
        "modality": modality,
        "actor_key": "service",
        "action_key": "delete-record",
        "target_key": "record",
        "operation_key": "account-closure",
        "condition_key": "account-closed",
        "applicability": "applies",
        "applicability_rationale": "Synthetic reviewer confirms applicability.",
        "applicability_reviewer": "synthetic-reviewer",
        "exceptions": (),
        "exceptions_reviewed": True,
    }
    values.update(overrides)
    return ObligationEvidence(**values)


def request(*items, **overrides):
    values = {
        "case_id": "synthetic-case",
        "as_of_date": date(2026, 11, 28),
        "obligations": tuple(items),
        "scope_relation": "same_operation",
        "scope_rationale": "Synthetic scope reviewed.",
        "scope_evidence_quote": "The synthetic case states the same operation.",
        "scope_reviewed_by": "synthetic-reviewer",
        "compatible_option": None,
    }
    values.update(overrides)
    return AssessmentRequest(**values)


def test_exact_reviewed_opposite_modalities_are_flagged_for_human_review():
    result = assess_case(
        request(obligation("a", "EU-X", "MUST"), obligation("b", "IN-X", "MUST_NOT"))
    )

    assert result.label == "CONFLICT"
    assert result.requires_human_review is True
    assert [(pair.rule_id_a, pair.rule_id_b) for pair in result.conflict_pairs] == [("a", "b")]


def test_unreviewed_exceptions_fail_closed():
    result = assess_case(
        request(
            obligation("a", "EU-X", "MUST", exceptions_reviewed=False),
            obligation("b", "IN-X", "MUST_NOT"),
        )
    )

    assert result.label == "NEEDS_REVIEW"


def test_disjoint_scope_is_independent_only_with_review_and_evidence():
    result = assess_case(
        request(
            obligation("a", "EU-X", "MUST"),
            obligation("b", "IN-X", "MUST_NOT"),
            scope_relation="disjoint",
        )
    )

    assert result.label == "INDEPENDENT"
    assert result.requires_human_review is False


def test_one_non_applicable_rule_is_independent_after_review():
    result = assess_case(
        request(
            obligation("a", "EU-X", "MUST", applicability="does_not_apply"),
            obligation("b", "IN-X", "MUST_NOT"),
        )
    )

    assert result.label == "INDEPENDENT"


def test_non_applicable_third_rule_does_not_hide_conflict_between_other_rules():
    result = assess_case(
        request(
            obligation("a", "EU-X", "MUST"),
            obligation("b", "IN-X", "MUST_NOT"),
            obligation("c", "CA-X", "MAY", applicability="does_not_apply"),
        )
    )

    assert result.label == "CONFLICT"
    assert len(result.conflict_pairs) == 1


def test_compatible_requires_reviewed_option_covering_every_rule():
    option = CompatibleOption(
        description="Use the synthetic alternative operation.",
        rationale="Synthetic reviewer supplies a jointly satisfying path.",
        supporting_rule_ids=("a", "b"),
        evidence_quotes=("Synthetic quote A.", "Synthetic quote B."),
        reviewed_by="synthetic-reviewer",
    )
    result = assess_case(
        request(
            obligation("a", "EU-X", "MUST"),
            obligation("b", "IN-X", "MUST_NOT"),
            compatible_option=option,
        )
    )

    assert result.label == "COMPATIBLE"
    assert result.requires_human_review is False


def test_nonidentical_structured_predicates_return_needs_review():
    result = assess_case(
        request(
            obligation("a", "EU-X", "MUST"),
            obligation("b", "IN-X", "MUST_NOT", action_key="retain-record"),
        )
    )

    assert result.label == "NEEDS_REVIEW"
    assert result.requires_human_review is True


def test_same_jurisdiction_opposite_rules_are_not_reported_as_cross_jurisdiction_conflict():
    result = assess_case(
        request(
            obligation("a", "EU-X", "MUST"),
            obligation("b", "EU-X", "MUST_NOT"),
            obligation("c", "IN-X", "MAY", applicability="does_not_apply"),
        )
    )

    assert result.label == "NEEDS_REVIEW"
    assert result.conflict_pairs == ()


def test_malformed_core_values_fail_closed_instead_of_crashing():
    result = assess_case(
        request(
            obligation("a", "EU-X", []),
            obligation("b", "IN-X", "MUST_NOT"),
        )
    )

    assert result.label == "NEEDS_REVIEW"


def test_malformed_request_metadata_fails_closed_instead_of_crashing():
    result = assess_case(
        request(
            obligation("a", "EU-X", "MUST"),
            obligation("b", "IN-X", "MUST_NOT"),
            as_of_date="not-a-date",
        )
    )

    assert result.label == "NEEDS_REVIEW"
    assert result.as_of_date == ""
