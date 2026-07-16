from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    repositories = relationship("Repository", back_populates="organization")
    users = relationship("User", back_populates="organization")
    pull_requests = relationship("PullRequest", back_populates="organization")
    evidence = relationship("Evidence", back_populates="organization")
    entities = relationship("Entity", back_populates="organization")
    relationships = relationship("EntityRelationship", back_populates="organization")
    signals = relationship("OrganizationalSignal", back_populates="organization")
    assumptions = relationship("Assumption", back_populates="organization")
    reasoning_sessions = relationship("ReasoningSession", back_populates="organization")
    actions = relationship("Action", back_populates="organization")
    execution_history = relationship("ExecutionHistory", back_populates="organization")
