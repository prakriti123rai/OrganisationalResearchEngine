from __future__ import annotations

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema
from app.schemas.reasoning_session import ReasoningSessionRead


class ReasoningRunRequest(OrmSchema):
    graph_depth: int = Field(default=2, ge=0, le=3)
    force: bool = False


class ReasoningFinding(OrmSchema):
    id: str
    title: str
    summary: str
    impact: str
    confidence: str
    entity_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    signal_ids: list[str] = Field(default_factory=list)
    assumption_ids: list[str] = Field(default_factory=list)


class ReasoningStep(OrmSchema):
    id: str
    order: int
    section_key: str
    title: str
    reasoning: str
    evidence_ids: list[str] = Field(default_factory=list)
    signal_ids: list[str] = Field(default_factory=list)
    assumption_ids: list[str] = Field(default_factory=list)


class ReasoningResult(OrmSchema):
    schema_version: str = "reasoning_result_v1"
    question: str
    answer: str
    model: str
    provider: str
    impact_level: str
    confidence: str
    findings: list[ReasoningFinding] = Field(default_factory=list)
    reasoning_steps: list[ReasoningStep] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    impacted_entity_ids: list[str] = Field(default_factory=list)
    primary_evidence_ids: list[str] = Field(default_factory=list)
    context_scope: Metadata = Field(default_factory=dict)
    metadata: Metadata = Field(default_factory=dict)


class ReasoningRunRead(OrmSchema):
    organization_id: str
    reasoning_session: ReasoningSessionRead
    result: ReasoningResult
    context_metadata: Metadata = Field(default_factory=dict)
