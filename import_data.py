import argparse
import csv
import hashlib
import json
import os

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy.exc import IntegrityError

from google_client import get_sheets_service
from models import RespostaForm, db
from utils import capitalize_words, clean_document, is_document_valid

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa app Flask para uso do contexto do SQLAlchemy
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Configurações da planilha
SHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Respostas")
SHEET_HEADERS = [
    "Timestamp Processamento",
    "Submission ID",
    "Tipo Pessoa",
    "Primeiro Nome",
    "Sobrenome",
    "CPF",
    "Data de Nascimento",
    "RG",
    "Estado Emissor RG",
    "Nacionalidade",
    "Estado Civil",
    "Profissão",
    "CNH",
    "Razão Social",
    "CNPJ",
    "Nome Representante Legal",
    "CPF Representante Legal",
    "Cargo Representante Legal",
    "CEP",
    "Endereço",
    "Complemento",
    "Bairro",
    "Cidade",
    "UF Endereço",
    "Telefone Celular",
    "Outro Telefone",
    "E-mail",
    "Nome Cliente/Pasta",
    "IDs Arquivos Anexados",
    "Link Pasta Cliente",
    "Status Processamento",
    "Observações de Processamento",
]


def fetch_sheet_data():
    service = get_sheets_service()
    range_ = f"{SHEET_NAME}!A1:AE"
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SHEET_ID, range=range_)
        .execute()
    )
    values = result.get("values", [])
    if not values:
        print("Nenhum dado encontrado na planilha.")
        return []
    headers = values[0]
    data = [dict(zip(headers, row)) for row in values[1:]]
    return data


def sanitize_row(row):
    # Gera um identificador único moderno baseado nos campos mais relevantes
    identificador_base = (
        (row.get("E-mail") or "").strip().lower()
        + (
            row.get("Nome completo")
            or row.get("Primeiro Nome", "") + row.get("Sobrenome", "")
        )
        .strip()
        .lower()
        + (row.get("Data de nascimento") or "").strip()
        + (row.get("Carimbo de data/hora") or "").strip()
    )
    submission_id = (
        hashlib.sha256(identificador_base.encode("utf-8")).hexdigest()
        if identificador_base
        else None
    )
    print(
        f"[IMPORT] submission_id gerado: {submission_id} | base: {identificador_base}"
    )
    return {
        "timestamp_processamento": row.get("Carimbo de data/hora"),
        "submission_id": submission_id,
        "tipo_pessoa": None,  # Não presente no cabeçalho
        "primeiro_nome": capitalize_words(row.get("Primeiro Nome", "")),
        "sobrenome": capitalize_words(row.get("Sobrenome", "")),
        "cpf": clean_document(row.get("CPF", "")),
        "data_nascimento": row.get("Data de nascimento"),
        "rg": row.get("RG"),
        "estado_emissor_rg": row.get("Estado emissor do RG"),
        "nacionalidade": row.get("Nacionalidade"),
        "estado_civil": row.get("Estado Civil"),
        "profissao": row.get("Profissão"),
        "cnh": row.get("Digite sua CNH (opcional):"),
        "razao_social": None,
        "cnpj": None,
        "nome_representante_legal": None,
        "cpf_representante_legal": None,
        "cargo_representante_legal": None,
        "cep": row.get("CEP"),
        "endereco": row.get("Endereço"),
        "complemento": None,
        "bairro": None,
        "cidade": capitalize_words(row.get("Cidade", "")),
        "uf_endereco": row.get("Estado"),
        "telefone_celular": row.get("Telefone celular"),
        "outro_telefone": row.get("Outro telefone"),
        "email": row.get("E-mail"),
        "nome_cliente_pasta": row.get("Nome completo"),
        "ids_arquivos_anexados": row.get("Foto da CNH ou RG"),
        "link_pasta_cliente": None,
        "status_processamento": None,
        "observacoes_processamento": None,
    }


def import_from_google_sheet():
    dados = fetch_sheet_data()
    if not dados:
        print("Nenhum dado para importar.")
        return
    total, inseridos, ignorados, erros = 0, 0, 0, 0
    with app.app_context():
        for row in dados:
            total += 1
            data = sanitize_row(row)
            if not data["submission_id"]:
                ignorados += 1
                continue
            if RespostaForm.query.filter_by(
                submission_id=data["submission_id"]
            ).first():
                ignorados += 1
                continue
            try:
                resposta = RespostaForm(**data)
                db.session.add(resposta)
                db.session.commit()
                inseridos += 1
                # Geração automática de documento após inserção
                from document_generator import gerar_documento_cliente

                try:
                    tipo_doc = "Ficha Cadastral"  # Pode ser dinâmico
                    tipo_pessoa = resposta.tipo_pessoa or "pf"
                    # Mapeia campos para os placeholders do template
                    dados_cliente = {
                        "Primeiro Nome": resposta.primeiro_nome or "",
                        "Sobrenome": resposta.sobrenome or "",
                        "Nacionalidade": resposta.nacionalidade or "",
                        "RG": resposta.rg or "",
                        "Estado emissor do RG": resposta.estado_emissor_rg or "",
                        "Estado Civil": resposta.estado_civil or "",
                        "CPF": resposta.cpf or "",
                        "Profissão": resposta.profissao or "",
                        "CNH": resposta.cnh or "",
                        "Endereço": resposta.endereco or "",
                        "Cidade": resposta.cidade or "",
                        "Estado": resposta.uf_endereco or "",
                        "CEP": resposta.cep or "",
                        "E-mail": resposta.email or "",
                        "Nascimento": resposta.data_nascimento or "",
                        "Telefone Celular": resposta.telefone_celular or "",
                        "Outro telefone": resposta.outro_telefone or "",
                    }
                    resultado_doc = gerar_documento_cliente(
                        tipo_doc, dados_cliente, tipo_pessoa
                    )
                    resposta.link_pasta_cliente = resultado_doc["link"]
                    db.session.commit()
                    print(
                        f"[DOC] Documento gerado para {resposta.primeiro_nome} {resposta.sobrenome}: {resultado_doc['link']}"
                    )
                except Exception as e:
                    db.session.rollback()
                    print(
                        f"[DOC][ERRO] Falha ao gerar documento para {resposta.primeiro_nome} {resposta.sobrenome}: {e}"
                    )
            except IntegrityError:
                db.session.rollback()
                ignorados += 1
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao inserir registro: {e}")
                erros += 1
    print(f"Total processado: {total}")
    print(f"Inseridos: {inseridos}")
    print(f"Ignorados (duplicados ou inválidos): {ignorados}")
    print(f"Erros: {erros}")


def import_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cliente = Cliente(
                primeiro_nome=row.get("primeiro_nome"),
                sobrenome=row.get("sobrenome"),
                email=row.get("email"),
                cpf=row.get("cpf"),
                cep=row.get("cep"),
                endereco=row.get("endereco"),
            )
            db.session.add(cliente)
        db.session.commit()


def import_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        for row in data:
            cliente = Cliente(
                primeiro_nome=row.get("primeiro_nome"),
                sobrenome=row.get("sobrenome"),
                email=row.get("email"),
                cpf=row.get("cpf"),
                cep=row.get("cep"),
                endereco=row.get("endereco"),
            )
            db.session.add(cliente)
        db.session.commit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Importa dados da planilha Google ou de arquivos locais"
    )
    parser.add_argument(
        "--google", action="store_true", help="Importa da planilha Google"
    )
    parser.add_argument("--csv", help="Arquivo CSV de dados")
    parser.add_argument("--json", help="Arquivo JSON de dados")
    args = parser.parse_args()
    if args.google:
        import_from_google_sheet()
    elif args.csv:
        import_csv(args.csv)
    elif args.json:
        import_json(args.json)
    else:
        print("Informe --google para importar da planilha Google.")
