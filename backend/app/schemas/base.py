from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class OrmSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


Metadata = dict[str, Any]


class TimestampedRead(OrmSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
