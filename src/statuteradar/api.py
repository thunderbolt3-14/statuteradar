"""Versioned local HTTP API for conservative conflict triage (Phase 6)."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

from .analysis.assessment import (
    AssessmentRequest,
    CompatibleOption,
    ObligationEvidence,
    assess_case,
)


class ObligationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(min_length=1)
    instrument: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    citation: str = Field(min_length=1)
    source_chunk_id: str = Field(min_length=1)
    evidence_quote: str = Field(min_length=1)
    modality: Literal["MUST", "MUST_NOT", "MAY"]
    actor_key: str | None = None
    action_key: str = Field(min_length=1, description="Reviewer-normalized action key")
    target_key: str = Field(min_length=1)
    operation_key: str = Field(min_length=1)
    condition_key: str | None = None
    applicability: Literal["applies", "does_not_apply", "unknown"]
    applicability_rationale: str = Field(min_length=1)
    applicability_reviewer: str | None = None
    exceptions: list[str] = Field(default_factory=list)
    exceptions_reviewed: bool = False

    def to_core(self) -> ObligationEvidence:
        return ObligationEvidence(**self.model_dump())


class CompatibleOptionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    supporting_rule_ids: list[str] = Field(
        min_length=1,
        description="Every applicable rule ID, each exactly once.",
    )
    evidence_quotes: list[str] = Field(
        min_length=1,
        description="One quote per supporting_rule_id, in the same order.",
    )
    reviewed_by: str | None = None

    def to_core(self) -> CompatibleOption:
        values = self.model_dump()
        values["supporting_rule_ids"] = tuple(values["supporting_rule_ids"])
        values["evidence_quotes"] = tuple(values["evidence_quotes"])
        return CompatibleOption(**values)


class AssessmentRequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    as_of_date: date
    obligations: list[ObligationInput] = Field(min_length=2)
    scope_relation: Literal["same_operation", "disjoint", "unknown"]
    scope_rationale: str = ""
    scope_evidence_quote: str = ""
    scope_reviewed_by: str | None = None
    compatible_option: CompatibleOptionInput | None = None

    def to_core(self) -> AssessmentRequest:
        return AssessmentRequest(
            case_id=self.case_id,
            as_of_date=self.as_of_date,
            obligations=tuple(item.to_core() for item in self.obligations),
            scope_relation=self.scope_relation,
            scope_rationale=self.scope_rationale,
            scope_evidence_quote=self.scope_evidence_quote,
            scope_reviewed_by=self.scope_reviewed_by,
            compatible_option=(
                self.compatible_option.to_core() if self.compatible_option else None
            ),
        )


class EvidenceResponse(BaseModel):
    rule_id: str
    instrument: str
    jurisdiction: str
    citation: str
    source_chunk_id: str
    evidence_quote: str
    modality: Literal["MUST", "MUST_NOT", "MAY"]
    actor_key: str | None
    action_key: str
    target_key: str
    operation_key: str
    condition_key: str | None
    applicability: Literal["applies", "does_not_apply", "unknown"]
    applicability_rationale: str
    applicability_reviewer: str | None
    exceptions: list[str]
    exceptions_reviewed: bool


class ScopeEvidenceResponse(BaseModel):
    relation: Literal["same_operation", "disjoint", "unknown"]
    rationale: str
    evidence_quote: str
    reviewed_by: str


class AssessmentResponse(BaseModel):
    case_id: str
    as_of_date: str
    label: Literal["CONFLICT", "COMPATIBLE", "INDEPENDENT", "NEEDS_REVIEW"]
    rationale: str
    requires_human_review: bool
    conflict_pairs: list[dict[str, str]]
    evidence_rule_ids: list[str]
    evidence: list[EvidenceResponse]
    scope_evidence: ScopeEvidenceResponse | None
    limitations: list[str]


def create_app() -> FastAPI:
    app = FastAPI(
        title="StatuteRadar Review API",
        version="1.0.0",
        description=(
            "Human-reviewed conflict triage. This API validates supplied structured findings; "
            "it does not determine legal applicability or provide legal advice."
        ),
    )

    @app.get("/health", tags=["operations"])
    def health() -> dict[str, str]:
        return {"status": "ok", "api_version": "1.0.0"}

    @app.post("/api/v1/assess", response_model=AssessmentResponse, tags=["assessment"])
    def assess(payload: AssessmentRequestInput) -> dict:
        result = assess_case(payload.to_core())
        return asdict(result)

    return app


app = create_app()
