from __future__ import annotations

import json
from typing import Optional

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.graph.enums import EntityLabel, GraphRelationshipType
from app.graph.schema import initialize_graph_schema
from app.models.entity import Entity
from app.models.organization import Organization
from app.models.relationship import EntityRelationship
from app.schemas.graph import GraphEdgeRead, GraphNodeRead, GraphSyncRead, OrganizationalGraphRead
from app.services.exceptions import NotFoundError, ValidationError


class GraphSyncError(ValidationError):
    """Raised when Neo4j cannot persist the organizational graph."""


ENTITY_LABELS: dict[str, EntityLabel] = {
    "organization": EntityLabel.ORGANIZATION,
    "team": EntityLabel.TEAM,
    "person": EntityLabel.PERSON,
    "repository": EntityLabel.REPOSITORY,
    "service": EntityLabel.SERVICE,
    "pull_request": EntityLabel.PULL_REQUEST,
    "feature": EntityLabel.FEATURE,
    "document": EntityLabel.DOCUMENT,
    "rfc": EntityLabel.RFC,
    "runbook": EntityLabel.RUNBOOK,
    "incident": EntityLabel.INCIDENT,
    "deployment": EntityLabel.DEPLOYMENT,
    "external_dependency": EntityLabel.EXTERNAL_DEPENDENCY,
}

RELATIONSHIP_TYPES: dict[str, GraphRelationshipType] = {
    "owns": GraphRelationshipType.OWNS,
    "maintains": GraphRelationshipType.MAINTAINS,
    "contributes_to": GraphRelationshipType.CONTRIBUTES_TO,
    "reviews": GraphRelationshipType.REVIEWS,
    "depends_on": GraphRelationshipType.DEPENDS_ON,
    "uses": GraphRelationshipType.USES,
    "documents": GraphRelationshipType.DOCUMENTS,
    "implements": GraphRelationshipType.IMPLEMENTS,
    "relates_to": GraphRelationshipType.RELATES_TO,
    "responded_to": GraphRelationshipType.RESPONDED_TO,
    "deploys": GraphRelationshipType.DEPLOYS,
    "affects": GraphRelationshipType.AFFECTS,
}


class OrganizationalGraphService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_graph(
        self,
        *,
        organization_id: str,
        entity_type: Optional[str] = None,
        relationship_type: Optional[str] = None,
        active_only: bool = True,
        limit: int = 200,
        offset: int = 0,
    ) -> OrganizationalGraphRead:
        self._require_organization(organization_id)
        if entity_type is not None and entity_type not in ENTITY_LABELS:
            raise ValidationError(f"Entity type '{entity_type}' is not graphable.")
        if relationship_type is not None and relationship_type not in RELATIONSHIP_TYPES:
            raise ValidationError(f"Relationship type '{relationship_type}' is not graphable.")

        entities = self._list_entities(
            organization_id=organization_id,
            entity_type=entity_type,
            limit=limit,
            offset=offset,
        )
        entity_ids = {entity.id for entity in entities}
        relationships = self._list_relationships(
            organization_id=organization_id,
            relationship_type=relationship_type,
            active_only=active_only,
            entity_ids=entity_ids,
        )

        nodes = [self._node_to_read(entity) for entity in entities]
        edges = [self._edge_to_read(relationship) for relationship in relationships]
        return OrganizationalGraphRead(
            organization_id=organization_id,
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges),
        )

    def sync_to_neo4j(self, *, organization_id: str) -> GraphSyncRead:
        graph = self.get_graph(
            organization_id=organization_id,
            active_only=False,
            limit=10_000,
            offset=0,
        )

        settings = get_settings()
        try:
            initialize_graph_schema()
            driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            try:
                with driver.session() as session:
                    session.execute_write(self._replace_graph, graph)
            finally:
                driver.close()
        except (Neo4jError, ServiceUnavailable, OSError) as exc:
            raise GraphSyncError(f"Neo4j graph sync failed: {exc}") from exc

        return GraphSyncRead(
            organization_id=organization_id,
            nodes_synced=graph.node_count,
            edges_synced=graph.edge_count,
        )

    def _list_entities(
        self,
        *,
        organization_id: str,
        entity_type: Optional[str],
        limit: int,
        offset: int,
    ) -> list[Entity]:
        statement = (
            select(Entity)
            .options(selectinload(Entity.supporting_evidence))
            .where(Entity.organization_id == organization_id)
            .order_by(Entity.entity_type.asc(), Entity.display_name.asc())
            .limit(limit)
            .offset(offset)
        )
        if entity_type is not None:
            statement = statement.where(Entity.entity_type == entity_type)
        return list(self.db.scalars(statement).unique().all())

    def _list_relationships(
        self,
        *,
        organization_id: str,
        relationship_type: Optional[str],
        active_only: bool,
        entity_ids: set[str],
    ) -> list[EntityRelationship]:
        if not entity_ids:
            return []

        statement = (
            select(EntityRelationship)
            .options(
                selectinload(EntityRelationship.supporting_evidence),
                selectinload(EntityRelationship.supporting_signals),
            )
            .where(
                EntityRelationship.organization_id == organization_id,
                EntityRelationship.source_entity_id.in_(entity_ids),
                EntityRelationship.target_entity_id.in_(entity_ids),
            )
            .order_by(EntityRelationship.relationship_type.asc(), EntityRelationship.id.asc())
        )
        if relationship_type is not None:
            statement = statement.where(EntityRelationship.relationship_type == relationship_type)
        if active_only:
            statement = statement.where(EntityRelationship.active.is_(True))
        return list(self.db.scalars(statement).unique().all())

    def _require_organization(self, organization_id: str) -> Organization:
        organization = self.db.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError(f"Organization '{organization_id}' was not found.")
        return organization

    def _node_to_read(self, entity: Entity) -> GraphNodeRead:
        return GraphNodeRead(
            id=entity.id,
            organization_id=entity.organization_id,
            entity_type=entity.entity_type,
            label=self._entity_label(entity.entity_type).value,
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
            graph_relationship_type=self._relationship_type(relationship.relationship_type).value,
            provenance=relationship.provenance,
            strength=relationship.strength,
            active=relationship.active,
            extra_metadata=relationship.extra_metadata,
            supporting_evidence_ids=sorted(
                evidence.id for evidence in relationship.supporting_evidence
            ),
            supporting_signal_ids=sorted(signal.id for signal in relationship.supporting_signals),
        )

    def _entity_label(self, entity_type: str) -> EntityLabel:
        return ENTITY_LABELS.get(entity_type, EntityLabel.DOCUMENT)

    def _relationship_type(self, relationship_type: str) -> GraphRelationshipType:
        return RELATIONSHIP_TYPES.get(relationship_type, GraphRelationshipType.RELATES_TO)

    def _replace_graph(self, transaction, graph: OrganizationalGraphRead) -> None:
        node_ids = [node.id for node in graph.nodes]
        edge_ids = [edge.id for edge in graph.edges]

        transaction.run(
            """
            MATCH ()-[r]->()
            WHERE r.organization_id = $organization_id AND NOT r.id IN $edge_ids
            DELETE r
            """,
            organization_id=graph.organization_id,
            edge_ids=edge_ids,
        )
        transaction.run(
            """
            MATCH (n)
            WHERE n.organization_id = $organization_id AND NOT n.id IN $node_ids
            DETACH DELETE n
            """,
            organization_id=graph.organization_id,
            node_ids=node_ids,
        )

        for node in graph.nodes:
            transaction.run(
                f"""
                MERGE (n:{node.label} {{id: $id}})
                SET n.organization_id = $organization_id,
                    n.entity_type = $entity_type,
                    n.display_name = $display_name,
                    n.description = $description,
                    n.status = $status,
                    n.metadata_json = $metadata_json,
                    n.supporting_evidence_ids = $supporting_evidence_ids
                """,
                id=node.id,
                organization_id=node.organization_id,
                entity_type=node.entity_type,
                display_name=node.display_name,
                description=node.description,
                status=node.status,
                metadata_json=self._metadata_json(node.extra_metadata),
                supporting_evidence_ids=node.supporting_evidence_ids,
            )

        for edge in graph.edges:
            transaction.run(
                f"""
                MATCH (source {{id: $source_entity_id}})
                MATCH (target {{id: $target_entity_id}})
                MERGE (source)-[r:{edge.graph_relationship_type} {{id: $id}}]->(target)
                SET r.organization_id = $organization_id,
                    r.relationship_type = $relationship_type,
                    r.provenance = $provenance,
                    r.strength = $strength,
                    r.active = $active,
                    r.metadata_json = $metadata_json,
                    r.supporting_evidence_ids = $supporting_evidence_ids,
                    r.supporting_signal_ids = $supporting_signal_ids
                """,
                id=edge.id,
                organization_id=edge.organization_id,
                source_entity_id=edge.source_entity_id,
                target_entity_id=edge.target_entity_id,
                relationship_type=edge.relationship_type,
                provenance=edge.provenance,
                strength=edge.strength,
                active=edge.active,
                metadata_json=self._metadata_json(edge.extra_metadata),
                supporting_evidence_ids=edge.supporting_evidence_ids,
                supporting_signal_ids=edge.supporting_signal_ids,
            )

    def _metadata_json(self, metadata: dict) -> str:
        return json.dumps(metadata, sort_keys=True)
