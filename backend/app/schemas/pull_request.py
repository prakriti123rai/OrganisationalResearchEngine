from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema


class PullRequestCreate(OrmSchema):
    id: str
    organization_id: str
    repository_id: str
    author_id: Optional[str] = None
    number: int
    title: str
    description: Optional[str] = None
    status: str = "open"
    source_branch: Optional[str] = None
    target_branch: Optional[str] = None
    extra_metadata: Metadata = Field(default_factory=dict)
    merged_at: Optional[datetime] = None


class PullRequestRead(PullRequestCreate):
    created_at: datetime
    updated_at: datetime
