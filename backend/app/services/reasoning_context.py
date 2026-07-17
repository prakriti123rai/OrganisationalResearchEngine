from __future__ import annotations

from collections import deque
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.assumption import Assumption
from app.models.entity import Entity
from app.models.evidence import Evidence
from app.models.organization import Organization
from app.models.organizational_signal import OrganizationalSignal
from app.models.pull_request import PullRequest
from app.models.reasoning_session import ReasoningSession
from app.models.relationship import EntityRelationship
from app.schemas.assumption import AssumptionRead
from app.schemas.evidence import EvidenceRead
from app.schemas.graph import GraphEdgeRead, GraphNodeRead
from app.schemas.organizational_signal import OrganizationalSignalRead
from app.schemas.pull_request import PullRequestRead
from app.schemas.reasoning_context import (
    ReasoningContextRead,
    ReasoningContextScope,
    ReasoningContextSection,
)
from app.schemas.reasoning_session import ReasoningSessionRead
from app.services.exceptions import NotFoundError, ValidationError
from app.services.organizational_graph import ENTITY_LABELS, RELATIONSHIP_TYPES

DEFAULT_CONTEXT_DEPTH = 2
MAX_CONTEXT_DEPTH = 3


class ReasoningContextService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build_for_session(
        self,
        *,
        organization_id: str,
        reasoning_session_id: str,
        graph_depth: int = DEFAULT_CONTEXT_DEPTH,
    ) -> ReasoningContextRead:
        self._validate_depth(graph_depth)
        self._require_organization(organization_id)
        session = self._get_reasoning_session(organization_id, reasoning_session_id)
        if session.pull_request_id is None:
            raise ValidationError(
                f"Reasoning session '{reasoning_session_id}' is not linked to a pull request."
            )

        return self._build_context(
            organization_id=organization_id,
            pull_request_id=session.pull_request_id,
            question=session.question,
            pattern=session.pattern,
            reasoning_session=session,
            graph_depth=graph_depth,
        )

    def build_for_pull_request(
        self,
        *,
        organization_id: str,
        pull_request_id: str,
        question: Optional[str] = None,
        pattern: Optional[str] = "pull_request_impact",
        graph_depth: int = DEFAULT_CONTEXT_DEPTH,
    ) -> ReasoningContextRead:
        self._validate_depth(graph_depth)
        self._require_organization(organization_id)
        pull_request = self._get_pull_request(organization_id, pull_request_id)
        resolved_question = (
            question or f"What organizational impact could {pull_request.title} have?"
        )

        return self._build_context(
            organization_id=organization_id,
            pull_request_id=pull_request_id,
            question=resolved_question,
            pattern=pattern,
            reasoning_session=None,
            graph_depth=graph_depth,
        )

    def _build_context(
        self,
        *,
        organization_id: str,
        pull_request_id: str,
        question: str,
        pattern: Optional[str],
        reasoning_session: Optional[ReasoningSession],
        graph_depth: int,
    ) -> ReasoningContextRead:
        pull_request = self._get_pull_request(organization_id, pull_request_id)
        focus_entity_id = self._focus_entity_id(pull_request)
        if focus_entity_id is not None:
            self._require_entity(organization_id, focus_entity_id)

        graph = self._context_graph(
            organization_id=organization_id,
            focus_entity_id=focus_entity_id,
            graph_depth=graph_depth,
        )
        entity_ids = {entity.id for entity in graph["entities"]}
        relationship_ids = {relationship.id for relationship in graph["relationships"]}

        evidence_records = self._context_evidence(
            organization_id=organization_id,
            pull_request_id=pull_request_id,
            entity_ids=entity_ids,
            relationship_ids=relationship_ids,
        )
        evidence_ids = {evidence.id for evidence in evidence_records}

        signal_records = self._context_signals(
            organization_id=organization_id,
            entity_ids=entity_ids,
            relationship_ids=relationship_ids,
            evidence_ids=evidence_ids,
        )
        signal_ids = {signal.id for signal in signal_records}

        assumption_records = self._context_assumptions(
            organization_id=organization_id,
            entity_ids=entity_ids,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
        )
        assumption_ids = {assumption.id for assumption in assumption_records}

        sections = self._sections(
            relationships=graph["relationships"],
            evidence=evidence_records,
            signals=signal_records,
            assumptions=assumption_records,
        )

        return ReasoningContextRead(
            organization_id=organization_id,
            question=question,
            pattern=pattern,
            reasoning_session=(
                ReasoningSessionRead.model_validate(reasoning_session)
                if reasoning_session is not None
                else None
            ),
            pull_request=PullRequestRead.model_validate(pull_request),
            scope=ReasoningContextScope(
                focus_entity_id=focus_entity_id,
                graph_depth=graph_depth,
                entity_ids=sorted(entity_ids),
                relationship_ids=sorted(relationship_ids),
                evidence_ids=sorted(evidence_ids),
                signal_ids=sorted(signal_ids),
                assumption_ids=sorted(assumption_ids),
            ),
            nodes=[self._node_to_read(entity) for entity in graph["entities"]],
            edges=[self._edge_to_read(relationship) for relationship in graph["relationships"]],
            evidence=[self._evidence_to_read(evidence) for evidence in evidence_records],
            signals=[self._signal_to_read(signal) for signal in signal_records],
            assumptions=[self._assumption_to_read(assumption) for assumption in assumption_records],
            sections=sections,
            context_metadata={
                "builder": "deterministic_v1",
                "source": "canonical_postgres",
                "graph_depth": graph_depth,
                "focus_pull_request_id": pull_request_id,
                "focus_entity_id": focus_entity_id,
            },
        )

    def _context_graph(
        self,
        *,
        organization_id: str,
        focus_entity_id: Optional[str],
        graph_depth: int,
    ) -> dict[str, list]:
        if focus_entity_id is None:
            return {"entities": [], "relationships": []}

        visited = {focus_entity_id}
        queue: deque[tuple[str, int]] = deque([(focus_entity_id, 0)])
        relationship_ids: set[str] = set()

        while queue:
            entity_id, depth = queue.popleft()
            if depth >= graph_depth:
                continue

            relationships = self._relationships_touching_entity(organization_id, entity_id)
            for relationship in relationships:
                relationship_ids.add(relationship.id)
                for next_entity_id in (
                    relationship.source_entity_id,
                    relationship.target_entity_id,
                ):
                    if next_entity_id not in visited:
                        visited.add(next_entity_id)
                        queue.append((next_entity_id, depth + 1))

        entities = self._entities_by_ids(organization_id, visited)
        relationships = self._relationships_by_ids(organization_id, relationship_ids)
        return {"entities": entities, "relationships": relationships}

    def _context_evidence(
        self,
        *,
        organization_id: str,
        pull_request_id: str,
        entity_ids: set[str],
        relationship_ids: set[str],
    ) -> list[Evidence]:
        statement = self._base_evidence_select().where(Evidence.organization_id == organization_id)
        criteria = [Evidence.extra_metadata["pull_request_id"].as_string() == pull_request_id]

        if entity_ids:
            criteria.append(Evidence.referenced_entities.any(Entity.id.in_(entity_ids)))
        if relationship_ids:
            criteria.append(
                Evidence.supported_relationships.any(EntityRelationship.id.in_(relationship_ids))
            )

        return list(
            self.db.scalars(
                statement.where(or_(*criteria)).order_by(
                    Evidence.timestamp.desc(), Evidence.ingested_at.desc()
                )
            )
            .unique()
            .all()
        )

    def _context_signals(
        self,
        *,
        organization_id: str,
        entity_ids: set[str],
        relationship_ids: set[str],
        evidence_ids: set[str],
    ) -> list[OrganizationalSignal]:
        statement = self._base_signal_select().where(
            OrganizationalSignal.organization_id == organization_id
        )
        criteria = []
        if entity_ids:
            criteria.append(OrganizationalSignal.subject_entity_id.in_(entity_ids))
        if relationship_ids:
            criteria.append(
                OrganizationalSignal.supporting_relationships.any(
                    EntityRelationship.id.in_(relationship_ids)
                )
            )
        if evidence_ids:
            criteria.append(
                OrganizationalSignal.supporting_evidence.any(Evidence.id.in_(evidence_ids))
            )
        if not criteria:
            return []

        return list(
            self.db.scalars(
                statement.where(or_(*criteria)).order_by(
                    OrganizationalSignal.confidence.asc(),
                    OrganizationalSignal.signal_type.asc(),
                    OrganizationalSignal.id.asc(),
                )
            )
            .unique()
            .all()
        )

    def _context_assumptions(
        self,
        *,
        organization_id: str,
        entity_ids: set[str],
        signal_ids: set[str],
        evidence_ids: set[str],
    ) -> list[Assumption]:
        statement = self._base_assumption_select().where(
            Assumption.organization_id == organization_id,
            Assumption.status == "active",
        )
        criteria = []
        if entity_ids:
            criteria.append(Assumption.subject_entity_id.in_(entity_ids))
        if signal_ids:
            criteria.append(
                Assumption.supporting_signals.any(OrganizationalSignal.id.in_(signal_ids))
            )
        if evidence_ids:
            criteria.append(Assumption.supporting_evidence.any(Evidence.id.in_(evidence_ids)))
        if not criteria:
            return []

        return list(
            self.db.scalars(
                statement.where(or_(*criteria)).order_by(
                    Assumption.confidence.asc(),
                    Assumption.assumption_type.asc(),
                    Assumption.id.asc(),
                )
            )
            .unique()
            .all()
        )

    def _sections(
        self,
        *,
        relationships: list[EntityRelationship],
        evidence: list[Evidence],
        signals: list[OrganizationalSignal],
        assumptions: list[Assumption],
    ) -> list[ReasoningContextSection]:
        sections = [
            self._relationship_section(
                key="ownership",
                title="Ownership",
                relationship_types={"owns", "maintains"},
                relationships=relationships,
                signals=signals,
                assumptions=assumptions,
            ),
            self._relationship_section(
                key="dependencies",
                title="Dependencies",
                relationship_types={"affects", "depends_on", "uses"},
                relationships=relationships,
                signals=signals,
                assumptions=assumptions,
            ),
            self._relationship_section(
                key="reviewers",
                title="Reviewers",
                relationship_types={"reviews", "contributes_to"},
                relationships=relationships,
                signals=signals,
                assumptions=assumptions,
            ),
            self._relationship_section(
                key="operational_readiness",
                title="Operational Readiness",
                relationship_types={"deploys", "responded_to", "documents"},
                relationships=relationships,
                signals=signals,
                assumptions=assumptions,
            ),
        ]
        sections.append(
            ReasoningContextSection(
                key="evidence",
                title="Evidence",
                summary=f"{len(evidence)} evidence records support this context.",
                evidence_ids=sorted(evidence_record.id for evidence_record in evidence),
            )
        )
        return sections

    def _relationship_section(
        self,
        *,
        key: str,
        title: str,
        relationship_types: set[str],
        relationships: list[EntityRelationship],
        signals: list[OrganizationalSignal],
        assumptions: list[Assumption],
    ) -> ReasoningContextSection:
        matching_relationships = [
            relationship
            for relationship in relationships
            if relationship.relationship_type in relationship_types
        ]
        relationship_ids = {relationship.id for relationship in matching_relationships}
        entity_ids = {
            entity_id
            for relationship in matching_relationships
            for entity_id in (relationship.source_entity_id, relationship.target_entity_id)
        }
        evidence_ids = {
            evidence.id
            for relationship in matching_relationships
            for evidence in relationship.supporting_evidence
        }
        matching_signals = [
            signal
            for signal in signals
            if signal.subject_entity_id in entity_ids
            or any(
                relationship.id in relationship_ids
                for relationship in signal.supporting_relationships
            )
        ]
        signal_ids = {signal.id for signal in matching_signals}
        matching_assumptions = [
            assumption
            for assumption in assumptions
            if assumption.subject_entity_id in entity_ids
            or any(signal.id in signal_ids for signal in assumption.supporting_signals)
        ]
        assumption_ids = {assumption.id for assumption in matching_assumptions}
        evidence_ids.update(
            evidence.id for signal in matching_signals for evidence in signal.supporting_evidence
        )
        evidence_ids.update(
            evidence.id
            for assumption in matching_assumptions
            for evidence in assumption.supporting_evidence
        )

        return ReasoningContextSection(
            key=key,
            title=title,
            summary=(
                f"{len(matching_relationships)} relationships, {len(matching_signals)} "
                f"signals, and {len(matching_assumptions)} assumptions."
            ),
            entity_ids=sorted(entity_ids),
            relationship_ids=sorted(relationship_ids),
            evidence_ids=sorted(evidence_ids),
            signal_ids=sorted(signal_ids),
            assumption_ids=sorted(assumption_ids),
        )

    def _base_evidence_select(self):
        return select(Evidence).options(
            selectinload(Evidence.referenced_entities),
            selectinload(Evidence.supported_relationships),
            selectinload(Evidence.supported_signals),
            selectinload(Evidence.supported_assumptions),
        )

    def _base_signal_select(self):
        return select(OrganizationalSignal).options(
            selectinload(OrganizationalSignal.supporting_relationships),
            selectinload(OrganizationalSignal.supporting_evidence),
        )

    def _base_assumption_select(self):
        return select(Assumption).options(
            selectinload(Assumption.supporting_signals),
            selectinload(Assumption.supporting_evidence),
        )

    def _relationships_touching_entity(
        self, organization_id: str, entity_id: str
    ) -> list[EntityRelationship]:
        return list(
            self.db.scalars(
                select(EntityRelationship)
                .options(
                    selectinload(EntityRelationship.supporting_evidence),
                    selectinload(EntityRelationship.supporting_signals),
                )
                .where(
                    EntityRelationship.organization_id == organization_id,
                    EntityRelationship.active.is_(True),
                    or_(
                        EntityRelationship.source_entity_id == entity_id,
                        EntityRelationship.target_entity_id == entity_id,
                    ),
                )
                .order_by(EntityRelationship.relationship_type.asc(), EntityRelationship.id.asc())
            )
            .unique()
            .all()
        )

    def _entities_by_ids(self, organization_id: str, entity_ids: set[str]) -> list[Entity]:
        if not entity_ids:
            return []
        return list(
            self.db.scalars(
                select(Entity)
                .options(selectinload(Entity.supporting_evidence))
                .where(Entity.organization_id == organization_id, Entity.id.in_(entity_ids))
                .order_by(Entity.entity_type.asc(), Entity.display_name.asc())
            )
            .unique()
            .all()
        )

    def _relationships_by_ids(
        self, organization_id: str, relationship_ids: set[str]
    ) -> list[EntityRelationship]:
        if not relationship_ids:
            return []
        return list(
            self.db.scalars(
                select(EntityRelationship)
                .options(
                    selectinload(EntityRelationship.supporting_evidence),
                    selectinload(EntityRelationship.supporting_signals),
                )
                .where(
                    EntityRelationship.organization_id == organization_id,
                    EntityRelationship.id.in_(relationship_ids),
                )
                .order_by(EntityRelationship.relationship_type.asc(), EntityRelationship.id.asc())
            )
            .unique()
            .all()
        )

    def _get_reasoning_session(
        self, organization_id: str, reasoning_session_id: str
    ) -> ReasoningSession:
        reasoning_session = self.db.get(ReasoningSession, reasoning_session_id)
        if reasoning_session is None or reasoning_session.organization_id != organization_id:
            raise NotFoundError(
                f"Reasoning session '{reasoning_session_id}' was not found in "
                f"organization '{organization_id}'."
            )
        return reasoning_session

    def _get_pull_request(self, organization_id: str, pull_request_id: str) -> PullRequest:
        pull_request = self.db.scalars(
            select(PullRequest)
            .options(
                selectinload(PullRequest.repository),
                selectinload(PullRequest.author),
            )
            .where(
                PullRequest.id == pull_request_id,
                PullRequest.organization_id == organization_id,
            )
        ).one_or_none()
        if pull_request is None:
            raise NotFoundError(
                f"Pull request '{pull_request_id}' was not found in "
                f"organization '{organization_id}'."
            )
        return pull_request

    def _require_entity(self, organization_id: str, entity_id: str) -> Entity:
        entity = self.db.get(Entity, entity_id)
        if entity is None or entity.organization_id != organization_id:
            raise NotFoundError(
                f"Entity '{entity_id}' was not found in organization '{organization_id}'."
            )
        return entity

    def _require_organization(self, organization_id: str) -> Organization:
        organization = self.db.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError(f"Organization '{organization_id}' was not found.")
        return organization

    def _validate_depth(self, graph_depth: int) -> None:
        if graph_depth < 0 or graph_depth > MAX_CONTEXT_DEPTH:
            raise ValidationError(
                f"graph_depth must be between 0 and {MAX_CONTEXT_DEPTH}, got {graph_depth}."
            )

    def _focus_entity_id(self, pull_request: PullRequest) -> Optional[str]:
        entity_id = pull_request.extra_metadata.get("entity_id")
        return entity_id if isinstance(entity_id, str) else None

    def _node_to_read(self, entity: Entity) -> GraphNodeRead:
        return GraphNodeRead(
            id=entity.id,
            organization_id=entity.organization_id,
            entity_type=entity.entity_type,
            label=ENTITY_LABELS.get(entity.entity_type, ENTITY_LABELS["document"]).value,
            display_name=entity.display_name,
            description=entity.description,
            status=entity.status,
            extra_metadata=entity.extra_metadata,
            supporting_evidence_ids=sorted(evidence.id for evidence in entity.supporting_evidence),
        )

    def _edge_to_read(self, relationship: EntityRelationship) -> GraphEdgeRead:
        return GraphEdgeRead(
            id=relationship.id,
            organization_id=relationship.organization_id,
            source_entity_id=relationship.source_entity_id,
            target_entity_id=relationship.target_entity_id,
            relationship_type=relationship.relationship_type,
            graph_relationship_type=RELATIONSHIP_TYPES.get(
                relationship.relationship_type, RELATIONSHIP_TYPES["relates_to"]
            ).value,
            provenance=relationship.provenance,
            strength=relationship.strength,
            active=relationship.active,
            extra_metadata=relationship.extra_metadata,
            supporting_evidence_ids=sorted(
                evidence.id for evidence in relationship.supporting_evidence
            ),
            supporting_signal_ids=sorted(signal.id for signal in relationship.supporting_signals),
        )

    def _evidence_to_read(self, evidence: Evidence) -> EvidenceRead:
        return EvidenceRead(
            id=evidence.id,
            organization_id=evidence.organization_id,
            author_id=evidence.author_id,
            evidence_type=evidence.evidence_type,
            source=evidence.source,
            source_reference=evidence.source_reference,
            title=evidence.title,
            summary=evidence.summary,
            timestamp=evidence.timestamp,
            extra_metadata=evidence.extra_metadata,
            ingested_at=evidence.ingested_at,
            referenced_entity_ids=sorted(entity.id for entity in evidence.referenced_entities),
            supported_relationship_ids=sorted(
                relationship.id for relationship in evidence.supported_relationships
            ),
            supported_signal_ids=sorted(signal.id for signal in evidence.supported_signals),
            supported_assumption_ids=sorted(
                assumption.id for assumption in evidence.supported_assumptions
            ),
        )

    def _signal_to_read(self, signal: OrganizationalSignal) -> OrganizationalSignalRead:
        return OrganizationalSignalRead.model_validate(signal)

    def _assumption_to_read(self, assumption: Assumption) -> AssumptionRead:
        return AssumptionRead.model_validate(assumption)
