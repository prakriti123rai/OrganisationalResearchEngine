"""canonical data model

Revision ID: 0001_canonical_data_model
Revises:
Create Date: 2026-07-16
"""

from alembic import op

from app import models  # noqa: F401
from app.db.base import Base

revision = "0001_canonical_data_model"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
