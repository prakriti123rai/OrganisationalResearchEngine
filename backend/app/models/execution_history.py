from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExecutionHistory(Base):
    __tablename__ = "execution_history"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("actions.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    artifact_type: Mapped[Optional[str]] = mapped_column(String(255))
    artifact_title: Mapped[Optional[str]] = mapped_column(String(500))
    logs: Mapped[Optional[str]] = mapped_column(String(8000))
    result_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    organization = relationship("Organization", back_populates="execution_history")
    action = relationship("Action", back_populates="execution_history")
