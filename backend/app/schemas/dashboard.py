from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import OrmSchema
from app.schemas.graph import GraphEdgeRead, GraphNodeRead
from app.schemas.organization import OrganizationRead


class DashboardCounts(OrmSchema):
    repositories: int
    users: int
    pull_requests: int
    open_pull_requests: int
    evidence: int
    entities: int
    relationships: int
    reasoning_sessions: int
    actions: int
    pending_execution: int
    completed_executions: int


class OrganizationHealth(OrmSchema):
    status: str
    health_score: int
    knowledge_score: int
    risk_level: str
    summary: str


class RecentPullRequest(OrmSchema):
    id: str
    title: str
    repository: str
    status: str
    updated_at: datetime


class RecentReasoning(OrmSchema):
    id: str
    question: str
    status: str
    impact_level: str | None = None
    confidence: str | None = None
    completed_at: datetime | None = None
    pull_request_title: str | None = None


class RecentPrediction(OrmSchema):
    id: str
    title: str
    summary: str
    impact: str
    confidence: str
    reasoning_session_id: str


class RecentActivity(OrmSchema):
    id: str
    activity_type: str
    title: str
    summary: str
    timestamp: datetime


class DashboardGraphPreview(OrmSchema):
    nodes: list[GraphNodeRead] = Field(default_factory=list)
    edges: list[GraphEdgeRead] = Field(default_factory=list)
    node_count: int
    edge_count: int


class DashboardRead(OrmSchema):
    organization: OrganizationRead
    counts: DashboardCounts
    health: OrganizationHealth
    recent_pull_requests: list[RecentPullRequest] = Field(default_factory=list)
    recent_reasoning: list[RecentReasoning] = Field(default_factory=list)
    recent_predictions: list[RecentPrediction] = Field(default_factory=list)
    recent_activity: list[RecentActivity] = Field(default_factory=list)
    graph_preview: DashboardGraphPreview
    metadata: dict[str, Any] = Field(default_factory=dict)
