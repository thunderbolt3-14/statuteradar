"""Fail-closed triage for explicitly reviewed obligation evidence.

This module does not infer legal applicability or semantic equivalence from statute text.
It only applies a narrow decision table to structured findings supplied by a reviewer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal


AssessmentLabel = Literal["CONFLICT", "COMPATIBLE", "INDEPENDENT", "NEEDS_REVIEW"]
Applicability = Literal["applies", "does_not_apply", "unknown"]
ScopeRelation = Literal["same_operation", "disjoint", "unknown"]
Modality = Literal["MUST", "MUST_NOT", "MAY"]


@dataclass(frozen=True)
class ObligationEvidence:
    rule_id: str
    instrument: str
    jurisdiction: str
    citation: str
    source_chunk_id: str
    evidence_quote: str
    modality: Modality
    actor_key: str | None
    action_key: str
    target_key: str
    operation_key: str
    condition_key: str | None
    applicability: Applicability
    applicability_rationale: str
    applicability_reviewer: str | None
    exceptions: tuple[str, ...] = ()
    exceptions_reviewed: bool = False


@dataclass(frozen=True)
class CompatibleOption:
    description: str
    rationale: str
    supporting_rule_ids: tuple[str, ...]
    evidence_quotes: tuple[str, ...]
    reviewed_by: str | None


@dataclass(frozen=True)
class AssessmentRequest:
    case_id: str
    as_of_date: date
    obligations: tuple[ObligationEvidence, ...]
    scope_relation: ScopeRelation
    scope_rationale: str
    scope_evidence_quote: str
    scope_reviewed_by: str | None
    compatible_option: CompatibleOption | None = None


@dataclass(frozen=True)
class ConflictPair:
    rule_id_a: str
    rule_id_b: str
    reason: str


@dataclass(frozen=True)
class EvidenceRecord:
    rule_id: str
    instrument: str
    jurisdiction: str
    citation: str
    source_chunk_id: str
    evidence_quote: str
    modality: Modality
    actor_key: str | None
    action_key: str
    target_key: str
    operation_key: str
    condition_key: str | None
    applicability: Applicability
    applicability_rationale: str
    applicability_reviewer: str | None
    exceptions: tuple[str, ...]
    exceptions_reviewed: bool


@dataclass(frozen=True)
class ScopeEvidenceRecord:
    relation: ScopeRelation
    rationale: str
    evidence_quote: str
    reviewed_by: str


@dataclass(frozen=True)
class AssessmentResult:
    case_id: str
    as_of_date: str
    label: AssessmentLabel
    rationale: str
    requires_human_review: bool
    conflict_pairs: tuple[ConflictPair, ...] = ()
    evidence_rule_ids: tuple[str, ...] = ()
    evidence: tuple[EvidenceRecord, ...] = ()
    scope_evidence: ScopeEvidenceRecord | None = None
    limitations: tuple[str, ...] = field(
        default=(
            "This result validates supplied structured findings; it does not determine legal applicability.",
            "NEEDS_REVIEW is the default when the submitted facts do not prove a supported outcome.",
        )
    )


def _valid_obligation(item: ObligationEvidence) -> bool:
    if not isinstance(item, ObligationEvidence):
        return False
    required_text_values = (
        item.rule_id,
        item.instrument,
        item.jurisdiction,
        item.citation,
        item.source_chunk_id,
        item.evidence_quote,
        item.action_key,
        item.target_key,
        item.operation_key,
        item.applicability_rationale,
    )
    required_text = all(
        isinstance(value, str) and value.strip() for value in required_text_values
    )
    valid_enums = (
        isinstance(item.modality, str)
        and item.modality in {"MUST", "MUST_NOT", "MAY"}
        and isinstance(item.applicability, str)
        and item.applicability in {"applies", "does_not_apply", "unknown"}
    )
    valid_optional_text = (
        item.actor_key is None
        or (isinstance(item.actor_key, str) and bool(item.actor_key.strip()))
    ) and (
        item.condition_key is None
        or (isinstance(item.condition_key, str) and bool(item.condition_key.strip()))
    )
    valid_reviewer = item.applicability_reviewer is None or (
        isinstance(item.applicability_reviewer, str)
        and bool(item.applicability_reviewer.strip())
    )
    valid_exceptions = isinstance(item.exceptions, (list, tuple)) and all(
        isinstance(value, str) and value.strip() for value in item.exceptions
    )
    return (
        required_text
        and valid_enums
        and valid_optional_text
        and valid_reviewer
        and valid_exceptions
        and isinstance(item.exceptions_reviewed, bool)
    )


def _result(
    request: AssessmentRequest,
    label: AssessmentLabel,
    rationale: str,
    *,
    review: bool,
    conflict_pairs: tuple[ConflictPair, ...] = (),
    evidence_ids: tuple[str, ...] | None = None,
) -> AssessmentResult:
    case_id = request.case_id if isinstance(request.case_id, str) else ""
    as_of_date = (
        request.as_of_date.isoformat() if isinstance(request.as_of_date, date) else ""
    )
    evidence = tuple(
        EvidenceRecord(
            rule_id=item.rule_id,
            instrument=item.instrument,
            jurisdiction=item.jurisdiction,
            citation=item.citation,
            source_chunk_id=item.source_chunk_id,
            evidence_quote=item.evidence_quote,
            modality=item.modality,
            actor_key=item.actor_key,
            action_key=item.action_key,
            target_key=item.target_key,
            operation_key=item.operation_key,
            condition_key=item.condition_key,
            applicability=item.applicability,
            applicability_rationale=item.applicability_rationale,
            applicability_reviewer=item.applicability_reviewer,
            exceptions=tuple(item.exceptions),
            exceptions_reviewed=item.exceptions_reviewed,
        )
        for item in request.obligations
        if _valid_obligation(item)
    )
    default_evidence_ids = tuple(item.rule_id for item in evidence)
    scope_evidence = None
    if (
        isinstance(request.scope_relation, str)
        and request.scope_relation in {"same_operation", "disjoint", "unknown"}
        and isinstance(request.scope_rationale, str)
        and request.scope_rationale.strip()
        and isinstance(request.scope_evidence_quote, str)
        and request.scope_evidence_quote.strip()
        and isinstance(request.scope_reviewed_by, str)
        and request.scope_reviewed_by.strip()
    ):
        scope_evidence = ScopeEvidenceRecord(
            relation=request.scope_relation,
            rationale=request.scope_rationale,
            evidence_quote=request.scope_evidence_quote,
            reviewed_by=request.scope_reviewed_by,
        )
    return AssessmentResult(
        case_id=case_id,
        as_of_date=as_of_date,
        label=label,
        rationale=rationale,
        requires_human_review=review,
        conflict_pairs=conflict_pairs,
        evidence_rule_ids=(
            evidence_ids if evidence_ids is not None else default_evidence_ids
        ),
        evidence=evidence,
        scope_evidence=scope_evidence,
    )


def assess_case(request: AssessmentRequest) -> AssessmentResult:
    """Return a narrow triage result; unresolved or unsupported cases fail closed."""
    if not isinstance(request, AssessmentRequest):
        raise TypeError("request must be an AssessmentRequest")
    if (
        not isinstance(request.case_id, str)
        or not request.case_id.strip()
        or not isinstance(request.as_of_date, date)
        or not isinstance(request.obligations, (tuple, list))
        or not request.obligations
    ):
        return _result(
            request,
            "NEEDS_REVIEW",
            "Case ID and obligation evidence are required.",
            review=True,
        )

    if not isinstance(request.scope_relation, str) or request.scope_relation not in {
        "same_operation",
        "disjoint",
        "unknown",
    }:
        return _result(
            request,
            "NEEDS_REVIEW",
            "Scope relation has an unsupported value.",
            review=True,
        )

    if not all(_valid_obligation(item) for item in request.obligations):
        return _result(
            request,
            "NEEDS_REVIEW",
            "Evidence is incomplete or contains duplicate rule IDs.",
            review=True,
        )
    rule_ids = [item.rule_id for item in request.obligations]
    if len(set(rule_ids)) != len(rule_ids):
        return _result(
            request,
            "NEEDS_REVIEW",
            "Evidence is incomplete or contains duplicate rule IDs.",
            review=True,
        )

    if len({item.jurisdiction for item in request.obligations}) < 2:
        return _result(
            request,
            "NEEDS_REVIEW",
            "Cross-jurisdiction evidence from at least two jurisdictions is required.",
            review=True,
        )

    if (
        request.scope_relation == "unknown"
        or not isinstance(request.scope_rationale, str)
        or not request.scope_rationale.strip()
    ):
        return _result(
            request,
            "NEEDS_REVIEW",
            "The case's operational overlap has not been established.",
            review=True,
        )
    if (
        not isinstance(request.scope_evidence_quote, str)
        or not request.scope_evidence_quote.strip()
        or not isinstance(request.scope_reviewed_by, str)
        or not request.scope_reviewed_by.strip()
    ):
        return _result(
            request,
            "NEEDS_REVIEW",
            "Scope findings need a supporting quote and reviewer identity.",
            review=True,
        )

    if request.scope_relation == "disjoint":
        return _result(
            request,
            "INDEPENDENT",
            "A reviewer found the cited rules address disjoint operations or scopes.",
            review=False,
            evidence_ids=tuple(rule_ids),
        )

    unresolved = [
        item
        for item in request.obligations
        if item.applicability == "unknown"
        or not isinstance(item.applicability_reviewer, str)
        or not item.applicability_reviewer.strip()
    ]
    if unresolved:
        return _result(
            request,
            "NEEDS_REVIEW",
            "Applicability is unknown or unreviewed for one or more rules.",
            review=True,
        )

    applicable = [
        item for item in request.obligations if item.applicability == "applies"
    ]
    if len(applicable) < 2:
        return _result(
            request,
            "INDEPENDENT",
            "Fewer than two reviewed, applicable rules from distinct jurisdictions constrain this case.",
            review=False,
            evidence_ids=tuple(rule_ids),
        )
    if len({item.jurisdiction for item in applicable}) < 2:
        return _result(
            request,
            "NEEDS_REVIEW",
            "Multiple applicable rules are from one jurisdiction; this cross-jurisdiction triage cannot classify them as independent.",
            review=True,
            evidence_ids=tuple(rule_ids),
        )

    option = request.compatible_option
    if option is not None:
        if not isinstance(option, CompatibleOption):
            return _result(
                request,
                "NEEDS_REVIEW",
                "The proposed compatible option is malformed.",
                review=True,
            )
        if (
            isinstance(option.description, str)
            and option.description.strip()
            and isinstance(option.rationale, str)
            and option.rationale.strip()
            and isinstance(option.reviewed_by, str)
            and option.reviewed_by.strip()
            and isinstance(option.supporting_rule_ids, (list, tuple))
            and all(
                isinstance(value, str) and value.strip()
                for value in option.supporting_rule_ids
            )
            and len(set(option.supporting_rule_ids)) == len(option.supporting_rule_ids)
            and set(option.supporting_rule_ids) == {item.rule_id for item in applicable}
            and isinstance(option.evidence_quotes, (list, tuple))
            and len(option.evidence_quotes) == len(option.supporting_rule_ids)
            and all(
                isinstance(quote, str) and quote.strip()
                for quote in option.evidence_quotes
            )
            and all(item.exceptions_reviewed for item in applicable)
        ):
            return _result(
                request,
                "COMPATIBLE",
                f"A reviewer supplied a concrete jointly satisfying option: {option.description}",
                review=False,
                evidence_ids=tuple(rule_ids),
            )
        return _result(
            request,
            "NEEDS_REVIEW",
            "The proposed compatible option lacks review or evidence for every rule.",
            review=True,
        )

    conflicts: list[ConflictPair] = []
    for index, left in enumerate(applicable):
        for right in applicable[index + 1 :]:
            same_predicate = (
                left.jurisdiction != right.jurisdiction
                and left.actor_key is not None
                and left.actor_key == right.actor_key
                and left.action_key == right.action_key
                and left.target_key == right.target_key
                and left.operation_key == right.operation_key
                and left.condition_key == right.condition_key
            )
            opposite_modalities = {left.modality, right.modality} == {
                "MUST",
                "MUST_NOT",
            }
            exceptions_cleared = (
                left.exceptions_reviewed
                and right.exceptions_reviewed
                and not left.exceptions
                and not right.exceptions
            )
            if same_predicate and opposite_modalities and exceptions_cleared:
                conflicts.append(
                    ConflictPair(
                        left.rule_id,
                        right.rule_id,
                        "Same reviewed actor/action/target/operation/condition has opposite MUST and MUST_NOT modalities, with exceptions reviewed and none recorded.",
                    )
                )

    if conflicts:
        return _result(
            request,
            "CONFLICT",
            "A structured contradiction was found in the reviewed inputs. Confirm legal interpretation and completeness before relying on it.",
            review=True,
            conflict_pairs=tuple(conflicts),
        )

    return _result(
        request,
        "NEEDS_REVIEW",
        "No contradiction or reviewed satisfying option was proven by the submitted structured evidence.",
        review=True,
    )
