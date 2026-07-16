from datetime import datetime

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema


class OrganizationalSignalCreate(OrmSchema):
    id: str
    organization_id: str
    subject_entity_id: str
    signal_type: str
    summary: str
    confidence: str
    extra_metadata: Metadata = Field(default_factory=dict)


class OrganizationalSignalRead(OrganizationalSignalCreate):
    last_updated: datetime
