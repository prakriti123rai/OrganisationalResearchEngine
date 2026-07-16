from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReasoningSession(Base):
    __tablename__ = "reasoning_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pull_request_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("pull_requests.id", ondelete="SET NULL"), index=True
    )
    question: Mapped[str] = mapped_column(String(1000), nullable=False)
    pattern: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    context_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    report: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    organization = relationship("Organization", back_populates="reasoning_sessions")
    pull_request = relationship("PullRequest", back_populates="reasoning_sessions")
    actions = relationship("Action", back_populates="reasoning_session")
