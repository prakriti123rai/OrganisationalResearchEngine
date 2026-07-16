from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import (
    assumption_evidence_links,
    entity_evidence_links,
    relationship_evidence_links,
    signal_evidence_links,
)


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(String(4000), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    organization = relationship("Organization", back_populates="evidence")
    author = relationship("User", back_populates="authored_evidence")
    referenced_entities = relationship(
        "Entity", secondary=entity_evidence_links, back_populates="supporting_evidence"
    )
    supported_relationships = relationship(
        "EntityRelationship",
        secondary=relationship_evidence_links,
        back_populates="supporting_evidence",
    )
    supported_signals = relationship(
        "OrganizationalSignal",
        secondary=signal_evidence_links,
        back_populates="supporting_evidence",
    )
    supported_assumptions = relationship(
        "Assumption", secondary=assumption_evidence_links, back_populates="supporting_evidence"
    )
