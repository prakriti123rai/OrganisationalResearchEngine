from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema


class EntityCreate(OrmSchema):
    id: str
    organization_id: str
    entity_type: str
    display_name: str
    description: Optional[str] = None
    status: str = "active"
    extra_metadata: Metadata = Field(default_factory=dict)


class EntityRead(EntityCreate):
    created_at: datetime
    updated_at: datetime
