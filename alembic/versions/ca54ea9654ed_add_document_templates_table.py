"""add document_templates table

Revision ID: ca54ea9654ed
Revises: b11811568f9d
Create Date: 2025-08-30 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca54ea9654ed"
down_revision: Union[str, None] = "b11811568f9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo_pessoa", sa.String(length=10), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("template_id", sa.String(length=64), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("document_templates")
