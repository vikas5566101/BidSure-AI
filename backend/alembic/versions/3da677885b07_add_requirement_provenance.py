"""add requirement provenance

Revision ID: 3da677885b07
Revises: 5ae4ce188b7d
Create Date: 2026-09-02 01:59:03.295111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3da677885b07'
down_revision: Union[str, Sequence[str], None] = '5ae4ce188b7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tender_requirements",
        sa.Column(
            "source_document",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "tender_requirements",
        sa.Column(
            "source_chunk_ids",
            sa.JSON(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "tender_requirements",
        "source_chunk_ids",
    )

    op.drop_column(
        "tender_requirements",
        "source_document",
    )