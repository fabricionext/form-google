"""add obrigatorio column

Revision ID: 2595ffa5342e
Revises: 0b673a3309d3
Create Date: 2025-07-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2595ffa5342e"
down_revision = "0b673a3309d3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("peticao_placeholders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("obrigatorio", sa.Boolean(), nullable=True))
        batch_op.execute(
            sa.text(
                "UPDATE peticao_placeholders SET obrigatorio = true WHERE obrigatorio IS NULL"
            )
        )
        batch_op.alter_column("obrigatorio", nullable=False)


def downgrade():
    with op.batch_alter_table("peticao_placeholders", schema=None) as batch_op:
        batch_op.drop_column("obrigatorio")
