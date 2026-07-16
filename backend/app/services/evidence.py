from __future__ import annotations

from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models.assumption import Assumption
from app.models.entity import Entity
from app.models.evidence import Evidence
from app.models.organization import Organization
from app.models.organizational_signal import OrganizationalSignal
from app.models.relationship import EntityRelationship
from app.models.user import User
from app.schemas.evidence import EvidenceCreate, EvidenceRead
from app.services.exceptions import NotFoundError, ValidationError


class EvidenceConflictError(ValidationError):
    """Raised when evidence cannot be created because its id already exists."""


class EvidenceNotFoundError(NotFoundError):
    """Raised when evidence is absent from an organization."""


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_evidence(
        self,
        *,
        organization_id: str,
        evidence_type: Optional[str] = None,
        source: Optional[str] = None,
        author_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        relationship_id: Optional[str] = None,
        signal_id: Optional[str] = None,
        assumption_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EvidenceRead]:
        self._require_organization(organization_id)

        statement = self._base_evidence_select().where(Evidence.organization_id == organization_id)

        if evidence_type is not None:
            statement = statement.where(Evidence.evidence_type == evidence_type)
        if source is not None:
            statement = statement.where(Evidence.source == source)
        if author_id is not None:
            self._require_user(organization_id, author_id)
            statement = statement.where(Evidence.author_id == author_id)
        if entity_id is not None:
            self._require_entity(organization_id, entity_id)
            statement = statement.where(Evidence.referenced_entities.any(Entity.id == entity_id))
        if relationship_id is not None:
            self._require_relationship(organization_id, relationship_id)
            statement = statement.where(
                Evidence.supported_relationships.any(EntityRelationship.id == relationship_id)
            )
        if signal_id is not None:
            self._require_signal(organization_id, signal_id)
            statement = statement.where(
                Evidence.supported_signals.any(OrganizationalSignal.id == signal_id)
            )
        if assumption_id is not None:
            self._require_assumption(organization_id, assumption_id)
            statement = statement.where(
                Evidence.supported_assumptions.any(Assumption.id == assumption_id)
            )

        records = (
            self.db.scalars(
                statement.order_by(Evidence.timestamp.desc(), Evidence.ingested_at.desc())
                .limit(limit)
                .offset(offset)
            )
            .unique()
            .all()
        )
        return [self._to_read(record) for record in records]

    def get_evidence(self, *, organization_id: str, evidence_id: str) -> EvidenceRead:
        self._require_organization(organization_id)
        evidence = self._get_evidence_record(organization_id, evidence_id)
        if evidence is None:
            raise EvidenceNotFoundError(f"Evidence '{evidence_id}' was not found.")
        return self._to_read(evidence)

    def create_evidence(self, *, organization_id: str, payload: EvidenceCreate) -> EvidenceRead:
        self._require_organization(organization_id)
        if payload.organization_id != organization_id:
            raise ValidationError("Evidence organization_id must match the organization path.")
        if self.db.get(Evidence, payload.id) is not None:
            raise EvidenceConflictError(f"Evidence '{payload.id}' already exists.")
        if payload.author_id is not None:
            self._require_user(organization_id, payload.author_id)

        evidence = Evidence(
            id=payload.id,
            organization_id=payload.organization_id,
            author_id=payload.author_id,
            evidence_type=payload.evidence_type,
            source=payload.source,
            source_reference=payload.source_reference,
            title=payload.title,
            summary=payload.summary,
            timestamp=payload.timestamp,
            extra_metadata=payload.extra_metadata,
        )

        evidence.referenced_entities = [
            self._require_entity(organization_id, entity_id)
            for entity_id in payload.referenced_entity_ids
        ]
        evidence.supported_relationships = [
            self._require_relationship(organization_id, relationship_id)
            for relationship_id in payload.supported_relationship_ids
        ]
        evidence.supported_signals = [
            self._require_signal(organization_id, signal_id)
            for signal_id in payload.supported_signal_ids
        ]
        evidence.supported_assumptions = [
            self._require_assumption(organization_id, assumption_id)
            for assumption_id in payload.supported_assumption_ids
        ]

        self.db.add(evidence)
        self.db.commit()

        persisted = self._get_evidence_record(organization_id, payload.id)
        if persisted is None:
            raise EvidenceNotFoundError(f"Evidence '{payload.id}' was not found after creation.")
        return self._to_read(persisted)

    def _base_evidence_select(self) -> Select[tuple[Evidence]]:
        return select(Evidence).options(
            selectinload(Evidence.referenced_entities),
            selectinload(Evidence.supported_relationships),
            selectinload(Evidence.supported_signals),
            selectinload(Evidence.supported_assumptions),
        )

    def _get_evidence_record(self, organization_id: str, evidence_id: str) -> Optional[Evidence]:
        return self.db.scalars(
            self._base_evidence_select().where(
                Evidence.id == evidence_id,
                Evidence.organization_id == organization_id,
            )
        ).one_or_none()

    def _require_organization(self, organization_id: str) -> Organization:
        organization = self.db.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError(f"Organization '{organization_id}' was not found.")
        return organization

    def _require_user(self, organization_id: str, user_id: str) -> User:
        user = self.db.get(User, user_id)
        if user is None or user.organization_id != organization_id:
            raise NotFoundError(
                f"User '{user_id}' was not found in organization '{organization_id}'."
            )
        return user

    def _require_entity(self, organization_id: str, entity_id: str) -> Entity:
        entity = self.db.get(Entity, entity_id)
        if entity is None or entity.organization_id != organization_id:
            raise NotFoundError(
                f"Entity '{entity_id}' was not found in organization '{organization_id}'."
            )
        return entity

    def _require_relationship(
        self,
        organization_id: str,
        relationship_id: str,
    ) -> EntityRelationship:
        relationship = self.db.get(EntityRelationship, relationship_id)
        if relationship is None or relationship.organization_id != organization_id:
            raise NotFoundError(
                f"Relationship '{relationship_id}' was not found in "
                f"organization '{organization_id}'."
            )
        return relationship

    def _require_signal(self, organization_id: str, signal_id: str) -> OrganizationalSignal:
        signal = self.db.get(OrganizationalSignal, signal_id)
        if signal is None or signal.organization_id != organization_id:
            raise NotFoundError(
                f"Signal '{signal_id}' was not found in organization '{organization_id}'."
            )
        return signal

    def _require_assumption(self, organization_id: str, assumption_id: str) -> Assumption:
        assumption = self.db.get(Assumption, assumption_id)
        if assumption is None or assumption.organization_id != organization_id:
            raise NotFoundError(
                f"Assumption '{assumption_id}' was not found in organization '{organization_id}'."
            )
        return assumption

    def _to_read(self, evidence: Evidence) -> EvidenceRead:
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
