from datetime import datetime

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema


class EntityRelationshipCreate(OrmSchema):
    id: str
    organization_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    provenance: str
    strength: str
    active: bool = True
    extra_metadata: Metadata = Field(default_factory=dict)


class EntityRelationshipRead(EntityRelationshipCreate):
    created_at: datetime
    last_updated: datetime
