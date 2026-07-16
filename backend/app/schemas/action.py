from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.schemas.base import OrmSchema


class ActionCreate(OrmSchema):
    id: str
    organization_id: str
    reasoning_session_id: Optional[str] = None
    action_type: str
    title: str
    description: str
    status: str = "proposed"
    confidence: str
    payload: dict[str, Any] = Field(default_factory=dict)
    approved_at: Optional[datetime] = None


class ActionRead(ActionCreate):
    created_at: datetime
    updated_at: datetime
