"""Add slug to peticao_modelos

Revision ID: add_slug_to_peticao_modelos
Revises: 
Create Date: 2025-06-26 01:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_slug_to_peticao_modelos'
down_revision = 'c12345678901'
branch_labels = None
depends_on = None

def upgrade():
    # Add slug column to peticao_modelos
    with op.batch_alter_table('peticao_modelos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=150), nullable=True))
        batch_op.create_unique_constraint('uq_peticao_modelos_slug', ['slug'])
    
    # Update existing records with slug based on nome
    connection = op.get_bind()
    
    # Generate slugs for existing records
    result = connection.execute(sa.text("SELECT id, nome FROM peticao_modelos WHERE slug IS NULL"))
    for row in result:
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', row.nome.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = f"{slug}-{row.id}"
        connection.execute(sa.text("UPDATE peticao_modelos SET slug = :slug WHERE id = :id"), 
                         {'slug': slug, 'id': row.id})
    
    # Make slug column NOT NULL after updating
    with op.batch_alter_table('peticao_modelos', schema=None) as batch_op:
        batch_op.alter_column('slug', nullable=False)

def downgrade():
    # Remove slug column from peticao_modelos
    with op.batch_alter_table('peticao_modelos', schema=None) as batch_op:
        batch_op.drop_constraint('uq_peticao_modelos_slug', type_='unique')
        batch_op.drop_column('slug')