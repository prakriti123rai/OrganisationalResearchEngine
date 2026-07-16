from sqlalchemy import Column, ForeignKey, Table

from app.db.base import Base

entity_evidence_links = Table(
    "entity_evidence_links",
    Base.metadata,
    Column("entity_id", ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
    Column("evidence_id", ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True),
)

relationship_evidence_links = Table(
    "relationship_evidence_links",
    Base.metadata,
    Column(
        "relationship_id",
        ForeignKey("entity_relationships.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("evidence_id", ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True),
)

signal_relationship_links = Table(
    "signal_relationship_links",
    Base.metadata,
    Column(
        "signal_id",
        ForeignKey("organizational_signals.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "relationship_id",
        ForeignKey("entity_relationships.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

signal_evidence_links = Table(
    "signal_evidence_links",
    Base.metadata,
    Column(
        "signal_id",
        ForeignKey("organizational_signals.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("evidence_id", ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True),
)

assumption_signal_links = Table(
    "assumption_signal_links",
    Base.metadata,
    Column("assumption_id", ForeignKey("assumptions.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "signal_id",
        ForeignKey("organizational_signals.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

assumption_evidence_links = Table(
    "assumption_evidence_links",
    Base.metadata,
    Column("assumption_id", ForeignKey("assumptions.id", ondelete="CASCADE"), primary_key=True),
    Column("evidence_id", ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True),
)
