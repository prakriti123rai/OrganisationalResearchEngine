from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.action import Action
from app.models.entity import Entity
from app.models.evidence import Evidence
from app.models.execution_history import ExecutionHistory
from app.models.organization import Organization
from app.models.pull_request import PullRequest
from app.models.reasoning_session import ReasoningSession
from app.models.relationship import EntityRelationship
from app.models.repository import Repository
from app.models.user import User
from app.schemas.dashboard import (
    DashboardCounts,
    DashboardGraphPreview,
    DashboardRead,
    OrganizationHealth,
    RecentActivity,
    RecentPrediction,
    RecentPullRequest,
    RecentReasoning,
)
from app.schemas.organization import OrganizationRead
from app.services.exceptions import NotFoundError
from app.services.organizational_graph import GraphSyncError, OrganizationalGraphService


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_organization(self, *, organization_id: str) -> OrganizationRead:
        return OrganizationRead.model_validate(self._require_organization(organization_id))

    def get_dashboard(self, *, organization_id: str) -> DashboardRead:
        organization = self._require_organization(organization_id)
        counts = self._counts(organization_id)
        recent_reasoning = self._recent_reasoning(organization_id)
        recent_predictions = self._recent_predictions(recent_reasoning)
        graph_preview = self._graph_preview(organization_id)
        health = self._health(counts=counts, predictions=recent_predictions)

        return DashboardRead(
            organization=OrganizationRead.model_validate(organization),
            counts=counts,
            health=health,
            recent_pull_requests=self._recent_pull_requests(organization_id),
            recent_reasoning=recent_reasoning,
            recent_predictions=recent_predictions,
            recent_activity=self._recent_activity(organization_id),
            graph_preview=graph_preview,
            metadata={
                "hero_workflow": "Pre-Merge Organizational Reasoning",
                "screen_count": 7,
                "source": "canonical_postgres_and_neo4j",
            },
        )

    def _counts(self, organization_id: str) -> DashboardCounts:
        action_count = self._count(Action, organization_id)
        completed_executions = self.db.scalar(
            select(func.count())
            .select_from(ExecutionHistory)
            .where(
                ExecutionHistory.organization_id == organization_id,
                ExecutionHistory.status == "completed",
            )
        )
        executed_action_ids = set(
            self.db.scalars(
                select(ExecutionHistory.action_id).where(
                    ExecutionHistory.organization_id == organization_id,
                    ExecutionHistory.action_id.is_not(None),
                )
            ).all()
        )
        approved_action_ids = set(
            self.db.scalars(
                select(Action.id).where(
                    Action.organization_id == organization_id,
                    Action.status.in_(["approved", "executed"]),
                )
            ).all()
        )
        pending_execution = len(approved_action_ids - executed_action_ids)

        return DashboardCounts(
            repositories=self._count(Repository, organization_id),
            users=self._count(User, organization_id),
            pull_requests=self._count(PullRequest, organization_id),
            open_pull_requests=self._count(
                PullRequest,
                organization_id,
                PullRequest.status == "open",
            ),
            evidence=self._count(Evidence, organization_id),
            entities=self._count(Entity, organization_id),
            relationships=self._count(EntityRelationship, organization_id),
            reasoning_sessions=self._count(ReasoningSession, organization_id),
            actions=action_count,
            pending_execution=pending_execution,
            completed_executions=completed_executions or 0,
        )

    def _count(self, model: type, organization_id: str, *criteria: Any) -> int:
        statement = (
            select(func.count()).select_from(model).where(model.organization_id == organization_id)
        )
        if criteria:
            statement = statement.where(*criteria)
        return self.db.scalar(statement) or 0

    def _health(
        self,
        *,
        counts: DashboardCounts,
        predictions: list[RecentPrediction],
    ) -> OrganizationHealth:
        coverage_score = min(45, counts.evidence * 4)
        graph_score = min(35, counts.entities + counts.relationships)
        reasoning_score = min(20, counts.reasoning_sessions * 10)
        knowledge_score = min(100, coverage_score + graph_score + reasoning_score)
        high_risk_predictions = [
            prediction for prediction in predictions if prediction.impact == "high"
        ]
        risk_level = "high" if high_risk_predictions else "medium"
        health_score = max(40, knowledge_score - len(high_risk_predictions) * 8)
        return OrganizationHealth(
            status="reasoning_ready",
            health_score=health_score,
            knowledge_score=knowledge_score,
            risk_level=risk_level,
            summary=(
                "ORE has enough seeded evidence, graph context, and completed reasoning "
                "to support the checkout pre-merge workflow."
            ),
        )

    def _recent_pull_requests(self, organization_id: str) -> list[RecentPullRequest]:
        pull_requests = self.db.scalars(
            select(PullRequest)
            .options(selectinload(PullRequest.repository))
            .where(PullRequest.organization_id == organization_id)
            .order_by(PullRequest.updated_at.desc(), PullRequest.id.asc())
            .limit(3)
        ).all()
        return [
            RecentPullRequest(
                id=pull_request.id,
                title=pull_request.title,
                repository=pull_request.repository.name,
                status=pull_request.status,
                updated_at=pull_request.updated_at,
            )
            for pull_request in pull_requests
        ]

    def _recent_reasoning(self, organization_id: str) -> list[RecentReasoning]:
        sessions = self.db.scalars(
            select(ReasoningSession)
            .options(selectinload(ReasoningSession.pull_request))
            .where(ReasoningSession.organization_id == organization_id)
            .order_by(ReasoningSession.created_at.desc(), ReasoningSession.id.asc())
            .limit(5)
        ).all()
        return [
            RecentReasoning(
                id=session.id,
                question=session.question,
                status=session.status,
                impact_level=self._report_field(session.report, "impact_level"),
                confidence=self._report_field(session.report, "confidence"),
                completed_at=session.completed_at,
                pull_request_title=session.pull_request.title if session.pull_request else None,
            )
            for session in sessions
        ]

    def _recent_predictions(
        self,
        recent_reasoning: list[RecentReasoning],
    ) -> list[RecentPrediction]:
        predictions: list[RecentPrediction] = []
        session_ids = [session.id for session in recent_reasoning]
        if not session_ids:
            return predictions

        sessions = self.db.scalars(
            select(ReasoningSession).where(ReasoningSession.id.in_(session_ids))
        ).all()
        for session in sessions:
            report = session.report or {}
            findings = report.get("findings", [])
            if not isinstance(findings, list):
                continue
            for finding in findings[:3]:
                if not isinstance(finding, dict):
                    continue
                predictions.append(
                    RecentPrediction(
                        id=str(finding.get("id", f"prediction-{session.id}")),
                        title=str(finding.get("title", "Reasoning prediction")),
                        summary=str(finding.get("summary", "")),
                        impact=str(finding.get("impact", report.get("impact_level", "medium"))),
                        confidence=str(
                            finding.get("confidence", report.get("confidence", "medium"))
                        ),
                        reasoning_session_id=session.id,
                    )
                )
        return predictions[:5]

    def _recent_activity(self, organization_id: str) -> list[RecentActivity]:
        evidence = self.db.scalars(
            select(Evidence)
            .where(Evidence.organization_id == organization_id)
            .order_by(Evidence.timestamp.desc(), Evidence.id.asc())
            .limit(3)
        ).all()
        executions = self.db.scalars(
            select(ExecutionHistory)
            .where(ExecutionHistory.organization_id == organization_id)
            .order_by(ExecutionHistory.started_at.desc(), ExecutionHistory.id.asc())
            .limit(3)
        ).all()

        activities = [
            RecentActivity(
                id=item.id,
                activity_type="evidence",
                title=item.title,
                summary=item.summary,
                timestamp=item.timestamp,
            )
            for item in evidence
        ]
        activities.extend(
            RecentActivity(
                id=execution.id,
                activity_type="execution",
                title=execution.artifact_title or "Execution completed",
                summary=execution.logs or "Execution history persisted.",
                timestamp=execution.completed_at or execution.started_at,
            )
            for execution in executions
        )
        return sorted(activities, key=lambda activity: activity.timestamp, reverse=True)[:5]

    def _graph_preview(self, organization_id: str) -> DashboardGraphPreview:
        graph_service = OrganizationalGraphService(self.db)
        try:
            graph = graph_service.get_neo4j_graph(
                organization_id=organization_id,
                active_only=True,
                limit=200,
                offset=0,
            )
            if graph.node_count == 0:
                graph_service.sync_to_neo4j(organization_id=organization_id)
                graph = graph_service.get_neo4j_graph(
                    organization_id=organization_id,
                    active_only=True,
                    limit=200,
                    offset=0,
                )
        except GraphSyncError:
            graph = graph_service.get_graph(
                organization_id=organization_id,
                active_only=True,
                limit=200,
                offset=0,
            )
        graph = self._connected_preview(graph)
        return DashboardGraphPreview(
            nodes=graph.nodes,
            edges=graph.edges,
            node_count=graph.node_count,
            edge_count=graph.edge_count,
        )

    def _connected_preview(self, graph):
        priority_node_ids = {"entity-pr-checkout-482"}
        impact_edges = [edge for edge in graph.edges if edge.relationship_type == "affects"]
        for edge in impact_edges:
            priority_node_ids.add(edge.source_entity_id)
            priority_node_ids.add(edge.target_entity_id)

        preview_edges = list(impact_edges)
        for edge in graph.edges:
            if len(preview_edges) >= 16:
                break
            if (
                edge.source_entity_id in priority_node_ids
                or edge.target_entity_id in priority_node_ids
            ) and edge.id not in {preview_edge.id for preview_edge in preview_edges}:
                preview_edges.append(edge)
                priority_node_ids.add(edge.source_entity_id)
                priority_node_ids.add(edge.target_entity_id)

        node_lookup = {node.id: node for node in graph.nodes}
        preview_nodes = [
            node_lookup[node_id] for node_id in priority_node_ids if node_id in node_lookup
        ]
        for node in graph.nodes:
            if len(preview_nodes) >= 12:
                break
            if node.id not in {preview_node.id for preview_node in preview_nodes}:
                preview_nodes.append(node)

        preview_node_ids = {node.id for node in preview_nodes}
        preview_edges = [
            edge
            for edge in preview_edges
            if edge.source_entity_id in preview_node_ids
            and edge.target_entity_id in preview_node_ids
        ]
        graph.nodes = preview_nodes
        graph.edges = preview_edges
        graph.node_count = len(preview_nodes)
        graph.edge_count = len(preview_edges)
        return graph

    def _report_field(self, report: dict[str, Any] | None, key: str) -> str | None:
        if not report:
            return None
        value = report.get(key)
        return str(value) if value is not None else None

    def _require_organization(self, organization_id: str) -> Organization:
        organization = self.db.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError(f"Organization '{organization_id}' was not found.")
        return organization
