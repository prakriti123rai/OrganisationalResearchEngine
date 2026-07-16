from datetime import datetime

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema


class AssumptionCreate(OrmSchema):
    id: str
    organization_id: str
    subject_entity_id: str
    assumption_type: str
    statement: str
    status: str = "active"
    confidence: str
    extra_metadata: Metadata = Field(default_factory=dict)


class AssumptionRead(AssumptionCreate):
    created_at: datetime
    last_evaluated: datetime
