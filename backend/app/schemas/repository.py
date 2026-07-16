from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema


class RepositoryCreate(OrmSchema):
    id: str
    organization_id: str
    name: str
    url: Optional[str] = None
    default_branch: str = "main"
    status: str = "active"
    extra_metadata: Metadata = Field(default_factory=dict)


class RepositoryRead(RepositoryCreate):
    created_at: datetime
    updated_at: datetime
