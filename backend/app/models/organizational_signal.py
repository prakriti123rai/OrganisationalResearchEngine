from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import signal_evidence_links, signal_relationship_links


class OrganizationalSignal(Base):
    __tablename__ = "organizational_signals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_entity_id: Mapped[str] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(4000), nullable=False)
    confidence: Mapped[str] = mapped_column(String(32), nullable=False)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization = relationship("Organization", back_populates="signals")
    subject_entity = relationship("Entity", back_populates="signals")
    supporting_relationships = relationship(
        "EntityRelationship",
        secondary=signal_relationship_links,
        back_populates="supporting_signals",
    )
    supporting_evidence = relationship(
        "Evidence", secondary=signal_evidence_links, back_populates="supported_signals"
    )
    assumptions = relationship(
        "Assumption", secondary="assumption_signal_links", back_populates="supporting_signals"
    )
