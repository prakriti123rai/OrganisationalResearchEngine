from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema


class GraphNodeRead(OrmSchema):
    id: str
    organization_id: str
    entity_type: str
    label: str
    display_name: str
    description: Optional[str] = None
    status: str
    extra_metadata: Metadata = Field(default_factory=dict)
    supporting_evidence_ids: list[str] = Field(default_factory=list)


class GraphEdgeRead(OrmSchema):
    id: str
    organization_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    graph_relationship_type: str
    provenance: str
    strength: str
    active: bool
    extra_metadata: Metadata = Field(default_factory=dict)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    supporting_signal_ids: list[str] = Field(default_factory=list)


class OrganizationalGraphRead(OrmSchema):
    organization_id: str
    nodes: list[GraphNodeRead]
    edges: list[GraphEdgeRead]
    node_count: int
    edge_count: int


class GraphSyncRead(OrmSchema):
    organization_id: str
    nodes_synced: int
    edges_synced: int
