from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ..ingest.schema import Instrument

Modality = Literal["MUST", "MUST_NOT", "MAY"]


class CandidateObligation(BaseModel):
    """Fields the model may extract from one provision chunk."""

    model_config = ConfigDict(extra="forbid")

    modality: Modality = Field(description="Duty, prohibition, or permission/right")
    actor: str | None = Field(description="Person or entity named in the text; null only if unstated")
    action: str = Field(min_length=1, description="Action or omission stated in the provision")
    data_category: str | None = Field(default=None, description="Data category named in the text; null if unstated")
    condition: str | None = Field(default=None, description="Trigger or circumstance stated in the text")
    constraint: str | None = Field(default=None, description="Deadline, retention period, or other stated limit")
    exceptions: list[str] = Field(default_factory=list)
    evidence_quote: str = Field(min_length=1, description="Verbatim supporting text from the supplied chunk")
    extraction_confidence: int = Field(ge=0, le=100,
                                       description="Uncalibrated model self-assessment on a 0-100 scale")


class CandidateQualifier(BaseModel):
    """A source-grounded exception or scope effect, including exception-only clauses."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["exception", "scope"]
    text: str = Field(min_length=1, description="What the exception or scope clause does")
    applies_to: str | None = Field(default=None, description="Rule/right this clause qualifies, if stated")
    condition: str | None = Field(default=None, description="Stated circumstance that activates this effect")
    evidence_quote: str = Field(min_length=1, description="Verbatim supporting text")
    extraction_confidence: int = Field(ge=0, le=100,
                                       description="Uncalibrated model self-assessment on a 0-100 scale")


class ObligationsFound(BaseModel):
    """Output shape when one or more obligations were extracted."""

    model_config = ConfigDict(extra="forbid")

    outcome: Literal["obligations"]
    obligations: list[CandidateObligation] = Field(min_length=1)
    qualifiers: list[CandidateQualifier] = Field(default_factory=list)
    no_obligation_reason: None = None


class NoObligationsFound(BaseModel):
    """Output shape when the chunk contains no standalone obligation."""

    model_config = ConfigDict(extra="forbid")

    outcome: Literal["no_obligation"]
    obligations: list[CandidateObligation] = Field(max_length=0)
    qualifiers: list[CandidateQualifier] = Field(default_factory=list)
    no_obligation_reason: str = Field(min_length=1)


ExtractionPayload = Annotated[
    Union[ObligationsFound, NoObligationsFound], Field(discriminator="outcome")
]
EXTRACTION_PAYLOAD_ADAPTER = TypeAdapter(ExtractionPayload)


class ObligationRecord(CandidateObligation):
    """Validated obligation with provenance assigned by StatuteRadar."""

    predicate_id: str
    source_chunk_id: str
    citation: str
    instrument: Instrument


class QualifierRecord(CandidateQualifier):
    predicate_id: str
    source_chunk_id: str
    citation: str
    instrument: Instrument


class ExtractionBatch(BaseModel):
    source_chunk_id: str
    citation: str
    instrument: Instrument
    obligations: list[ObligationRecord]
    qualifiers: list[QualifierRecord] = Field(default_factory=list)
    no_obligation_reason: str | None = None
