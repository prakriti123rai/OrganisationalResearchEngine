from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.schemas.assumption import AssumptionRead
from app.schemas.base import Metadata, OrmSchema
from app.schemas.evidence import EvidenceRead
from app.schemas.graph import GraphEdgeRead, GraphNodeRead
from app.schemas.organizational_signal import OrganizationalSignalRead
from app.schemas.pull_request import PullRequestRead
from app.schemas.reasoning_session import ReasoningSessionRead


class ReasoningContextScope(OrmSchema):
    focus_entity_id: Optional[str] = None
    graph_depth: int
    entity_ids: list[str] = Field(default_factory=list)
    relationship_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    signal_ids: list[str] = Field(default_factory=list)
    assumption_ids: list[str] = Field(default_factory=list)


class ReasoningContextSection(OrmSchema):
    key: str
    title: str
    summary: str
    entity_ids: list[str] = Field(default_factory=list)
    relationship_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    signal_ids: list[str] = Field(default_factory=list)
    assumption_ids: list[str] = Field(default_factory=list)


class ReasoningContextRead(OrmSchema):
    organization_id: str
    question: str
    pattern: Optional[str] = None
    reasoning_session: Optional[ReasoningSessionRead] = None
    pull_request: PullRequestRead
    scope: ReasoningContextScope
    nodes: list[GraphNodeRead] = Field(default_factory=list)
    edges: list[GraphEdgeRead] = Field(default_factory=list)
    evidence: list[EvidenceRead] = Field(default_factory=list)
    signals: list[OrganizationalSignalRead] = Field(default_factory=list)
    assumptions: list[AssumptionRead] = Field(default_factory=list)
    sections: list[ReasoningContextSection] = Field(default_factory=list)
    context_metadata: Metadata = Field(default_factory=dict)
