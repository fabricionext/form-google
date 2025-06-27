"""add categoria field to peticao_placeholders

Revision ID: c12345678902
Revises: 06ae44016383
Create Date: 2025-06-24 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c12345678902'
down_revision = '06ae44016383'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar coluna categoria à tabela peticao_placeholders
    op.add_column('peticao_placeholders', sa.Column('categoria', sa.String(32), nullable=False, server_default='outros'))


def downgrade():
    # Remover coluna categoria da tabela peticao_placeholders
    op.drop_column('peticao_placeholders', 'categoria') 