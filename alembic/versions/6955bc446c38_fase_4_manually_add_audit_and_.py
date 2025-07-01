"""Fase 4: Manually Add Audit and Versioning Models

Revision ID: 6955bc446c38
Revises: ca54ea9654ed
Create Date: 2025-06-30 19:09:41.054359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6955bc446c38'
down_revision: Union[str, None] = 'ca54ea9654ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.Enum('CREATE', 'UPDATE', 'DELETE', 'SYNC', 'LOGIN', 'LOGOUT', 'ACCESS', 'IMPORT', name='auditaction'), nullable=False),
        sa.Column('target_type', sa.String(length=100), nullable=True),
        sa.Column('target_id', sa.String(length=255), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False),
        sa.Column('notification_type', sa.Enum('SUCCESS', 'ERROR', 'INFO', 'WARNING', name='notificationtype'), nullable=False),
        sa.Column('related_object_type', sa.String(length=100), nullable=True),
        sa.Column('related_object_id', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['clientes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'document_template_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('google_doc_id', sa.String(length=255), nullable=True),
        sa.Column('detected_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('changed_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['document_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_template_versions_template_id'), 'document_template_versions', ['template_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_document_template_versions_template_id'), table_name='document_template_versions')
    op.drop_table('document_template_versions')
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    # Manually drop the enums created
    op.execute("DROP TYPE auditaction;")
    op.execute("DROP TYPE notificationtype;")
