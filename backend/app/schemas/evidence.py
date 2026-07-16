from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import Metadata, OrmSchema


class EvidenceCreate(OrmSchema):
    id: str
    organization_id: str
    author_id: Optional[str] = None
    evidence_type: str
    source: str
    source_reference: str
    title: str
    summary: str
    timestamp: datetime
    extra_metadata: Metadata = Field(default_factory=dict)


class EvidenceRead(EvidenceCreate):
    ingested_at: datetime
