import os
import sys
from datetime import datetime

# Adicionar o diretório do projeto ao path para importações corretas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application import app, db
from models import RespostaForm


def create_test_client():
    """Cria um cliente de teste no banco de dados para depuração."""
    with app.app_context():
        print(
            f"SCRIPT_CREATE_CLIENT: Conectando ao banco de dados: {app.config['SQLALCHEMY_DATABASE_URI']}"
        )

        # Dados do cliente de teste
        test_cpf = "11122233344"
        test_email = "peticionador.teste@example.com"

        # 1. Tentar deletar qualquer cliente existente com este CPF para garantir um estado limpo
        try:
            existing_client_to_delete = RespostaForm.query.filter_by(
                cpf=test_cpf
            ).first()
            if existing_client_to_delete:
                print(
                    f"SCRIPT_CREATE_CLIENT: Encontrado cliente existente com CPF {test_cpf} para deletar. ID: {existing_client_to_delete.id}"
                )
                db.session.delete(existing_client_to_delete)
                db.session.commit()
                print(
                    f"SCRIPT_CREATE_CLIENT: Cliente com CPF {test_cpf} deletado e commitado."
                )
            else:
                print(
                    f"SCRIPT_CREATE_CLIENT: Nenhum cliente encontrado com CPF {test_cpf} para deletar."
                )
        except Exception as e:
            db.session.rollback()
            print(
                f"SCRIPT_CREATE_CLIENT: Erro ao tentar deletar cliente com CPF {test_cpf}: {e}"
            )
            return  # Não continuar se a limpeza falhar

        # 2. Verificar novamente se o cliente existe (após tentativa de deleção)
        # Esta verificação é mais para depuração, idealmente não deveria encontrar nada agora.
        existing_client_after_delete = RespostaForm.query.filter_by(
            cpf=test_cpf
        ).first()
        if existing_client_after_delete:
            print(
                f"SCRIPT_CREATE_CLIENT: ALERTA! Cliente com CPF {test_cpf} AINDA EXISTE após tentativa de deleção. Detalhes:"
            )
            print(f"  ID: {existing_client_after_delete.id}")
            print(f'  CPF no DB: "{existing_client_after_delete.cpf}"')
            print(f"SCRIPT_CREATE_CLIENT: Abortando criação.")
            return

        # 3. Criar o novo cliente
        print(
            f"SCRIPT_CREATE_CLIENT: Procedendo para criar novo cliente com CPF {test_cpf}."
        )
        new_client = RespostaForm(
            submission_id=f"test_submission_{datetime.utcnow().timestamp()}",
            tipo_pessoa="pf",
            primeiro_nome="Cliente",
            sobrenome="Teste Peticionador",
            cpf=test_cpf,
            email=test_email,
            status_processamento="Completo",
            timestamp_processamento=datetime.utcnow(),
        )

        try:
            print(
                f"SCRIPT_CREATE_CLIENT: Tentando adicionar cliente CPF {test_cpf} à sessão."
            )
            db.session.add(new_client)
            print(f"SCRIPT_CREATE_CLIENT: Cliente CPF {test_cpf} adicionado à sessão.")

            print(f"SCRIPT_CREATE_CLIENT: Tentando comitar a sessão.")
            db.session.commit()
            print(
                f"SCRIPT_CREATE_CLIENT: Sessão comitada com sucesso para CPF {test_cpf}."
            )

            # Verificar se o cliente foi realmente persistido na sessão atual
            persisted_client = RespostaForm.query.filter_by(cpf=test_cpf).first()
            if persisted_client:
                print(
                    f"SCRIPT_CREATE_CLIENT: VERIFICAÇÃO PÓS-COMMIT: Cliente CPF {test_cpf} encontrado no banco. ID: {persisted_client.id}"
                )
            else:
                print(
                    f"SCRIPT_CREATE_CLIENT: VERIFICAÇÃO PÓS-COMMIT: ERRO! Cliente CPF {test_cpf} NÃO encontrado no banco após commit."
                )

            print(
                f"Cliente de teste com CPF {test_cpf} criado com sucesso (mensagem original)!"
            )

        except Exception as e:
            print(
                f"SCRIPT_CREATE_CLIENT: ERRO DURANTE CRIAÇÃO/COMMIT para CPF {test_cpf}."
            )
            db.session.rollback()
            print(f"Erro ao criar cliente de teste: {e}")
            print(f"SCRIPT_CREATE_CLIENT: Rollback da sessão executado.")


if __name__ == "__main__":
    create_test_client()
