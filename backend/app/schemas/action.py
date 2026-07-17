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


class ActionGenerateRequest(OrmSchema):
    organization_id: str = "org-demo-apex"
    reasoning_session_id: str = "reasoning-demo-pr-482"
    force: bool = False


class ActionUpdateRequest(OrmSchema):
    organization_id: str = "org-demo-apex"
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    artifact_preview: Optional[str] = Field(default=None, min_length=1)


class ActionPlanRead(OrmSchema):
    organization_id: str
    reasoning_session_id: str
    actions: list[ActionRead] = Field(default_factory=list)
