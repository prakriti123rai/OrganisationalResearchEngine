from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.schemas.base import OrmSchema


class ExecutionHistoryCreate(OrmSchema):
    id: str
    organization_id: str
    action_id: Optional[str] = None
    status: str = "queued"
    artifact_type: Optional[str] = None
    artifact_title: Optional[str] = None
    logs: Optional[str] = None
    result_metadata: dict[str, Any] = Field(default_factory=dict)
    completed_at: Optional[datetime] = None


class ExecutionHistoryRead(ExecutionHistoryCreate):
    started_at: datetime
