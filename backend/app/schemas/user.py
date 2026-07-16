from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema


class UserCreate(OrmSchema):
    id: str
    organization_id: str
    team_entity_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    role: Optional[str] = None
    extra_metadata: Metadata = Field(default_factory=dict)


class UserRead(UserCreate):
    created_at: datetime
    updated_at: datetime
