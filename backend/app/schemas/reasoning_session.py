from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.schemas.base import OrmSchema


class ReasoningSessionCreate(OrmSchema):
    id: str
    organization_id: str
    pull_request_id: Optional[str] = None
    question: str
    pattern: Optional[str] = None
    status: str = "pending"
    context_metadata: dict[str, Any] = Field(default_factory=dict)
    report: Optional[dict[str, Any]] = None


class ReasoningSessionRead(ReasoningSessionCreate):
    created_at: datetime
    completed_at: Optional[datetime] = None
