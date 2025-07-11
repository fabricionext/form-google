"""feat(model): adiciona campos estruturados de endereco

Revision ID: b999e01c3884
Revises:
Create Date: 2025-06-06 17:59:12.401237

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b999e01c3884"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "respostas_form",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp_processamento", sa.DateTime(), nullable=True),
        sa.Column("submission_id", sa.String(length=64), nullable=False),
        sa.Column("tipo_pessoa", sa.String(length=16), nullable=True),
        sa.Column("primeiro_nome", sa.String(length=64), nullable=True),
        sa.Column("sobrenome", sa.String(length=64), nullable=True),
        sa.Column("cpf", sa.String(length=32), nullable=True),
        sa.Column("data_nascimento", sa.String(length=16), nullable=True),
        sa.Column("rg", sa.String(length=32), nullable=True),
        sa.Column("estado_emissor_rg", sa.String(length=32), nullable=True),
        sa.Column("nacionalidade", sa.String(length=32), nullable=True),
        sa.Column("estado_civil", sa.String(length=32), nullable=True),
        sa.Column("profissao", sa.String(length=64), nullable=True),
        sa.Column("cnh", sa.String(length=32), nullable=True),
        sa.Column("razao_social", sa.String(length=128), nullable=True),
        sa.Column("cnpj", sa.String(length=32), nullable=True),
        sa.Column("nome_representante_legal", sa.String(length=128), nullable=True),
        sa.Column("cpf_representante_legal", sa.String(length=32), nullable=True),
        sa.Column("cargo_representante_legal", sa.String(length=64), nullable=True),
        sa.Column("cep", sa.String(length=16), nullable=True),
        sa.Column("endereco", sa.String(length=128), nullable=True),
        sa.Column("logradouro", sa.String(length=128), nullable=True),
        sa.Column("numero", sa.String(length=16), nullable=True),
        sa.Column("complemento", sa.String(length=64), nullable=True),
        sa.Column("bairro", sa.String(length=64), nullable=True),
        sa.Column("cidade", sa.String(length=64), nullable=True),
        sa.Column("uf_endereco", sa.String(length=32), nullable=True),
        sa.Column("telefone_celular", sa.String(length=32), nullable=True),
        sa.Column("outro_telefone", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=128), nullable=True),
        sa.Column("nome_cliente_pasta", sa.String(length=128), nullable=True),
        sa.Column("ids_arquivos_anexados", sa.String(length=256), nullable=True),
        sa.Column("link_pasta_cliente", sa.String(length=256), nullable=True),
        sa.Column("status_processamento", sa.String(length=64), nullable=True),
        sa.Column("observacoes_processamento", sa.String(length=256), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("submission_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("respostas_form")
    # ### end Alembic commands ###
