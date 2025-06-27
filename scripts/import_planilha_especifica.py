#!/usr/bin/env python3
"""
Script para importar dados da planilha Google Sheets específica
ID: 1Hj0D-VeJ51nQdAOBlvwzTKR_S3Sls40drthXfLI9Eow
para o banco de dados do sistema de cadastro.
"""

import hashlib
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from flask import Flask
from google.oauth2 import service_account
from googleapiclient.discovery import build
from sqlalchemy.exc import IntegrityError

from app.peticionador.models import Cliente, TipoPessoaEnum
from app.validators.form_validator import validate_cpf, validate_email
from extensions import db
from models import RespostaForm

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Inicializa app Flask
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# ID da planilha específica
PLANILHA_ID = "1Hj0D-VeJ51nQdAOBlvwzTKR_S3Sls40drthXfLI9Eow"

# Auxiliar: garante que strings não excedam o tamanho máximo da coluna


def truncate_str(valor: str, max_len: int) -> str:
    if not valor:
        return valor
    return valor[:max_len]


def get_sheets_service():
    """Obtém o serviço do Google Sheets."""
    try:
        service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not service_account_file:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON não configurado")

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

        service = build("sheets", "v4", credentials=credentials)
        logger.info("Serviço Google Sheets inicializado com sucesso")
        return service

    except Exception as e:
        logger.error(f"Erro ao inicializar Google Sheets: {e}")
        raise


def buscar_dados_planilha(service, sheet_name: str = "Respostas") -> List[Dict]:
    """Busca dados da planilha."""
    try:
        range_name = f"{sheet_name}!A:ZZ"  # Busca todas as colunas

        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=PLANILHA_ID, range=range_name)
            .execute()
        )

        values = result.get("values", [])
        if not values:
            logger.warning(f"Nenhum dado encontrado na aba '{sheet_name}'")
            return []

        # Primeira linha são os cabeçalhos
        headers = [str(header).strip() for header in values[0]]
        logger.info(f"Cabeçalhos encontrados na aba '{sheet_name}': {headers}")

        # Converte as linhas em dicionários
        dados = []
        for i, row in enumerate(values[1:], start=2):
            # Garante que a linha tenha o mesmo número de colunas dos cabeçalhos
            while len(row) < len(headers):
                row.append("")

            linha_dict = {
                headers[j]: str(row[j]).strip() if j < len(row) else ""
                for j in range(len(headers))
            }

            # Ignora linhas completamente vazias
            if any(linha_dict.values()):
                linha_dict["_linha_original"] = str(i)
                linha_dict["_aba_origem"] = sheet_name
                dados.append(linha_dict)

        logger.info(
            f"Total de {len(dados)} linhas de dados encontradas na aba '{sheet_name}'"
        )
        return dados

    except Exception as e:
        logger.error(f"Erro ao buscar dados da aba '{sheet_name}': {e}")
        raise


def limpar_documento(documento: str) -> str:
    """Remove formatação de documentos (CPF, CNPJ)."""
    if not documento:
        return ""
    return re.sub(r"[^\d]", "", documento)


def limpar_telefone(telefone: str) -> str:
    """Remove formatação de telefones."""
    if not telefone:
        return ""
    return re.sub(r"[^\d]", "", telefone)


def normalizar_nome(nome: str) -> str:
    """Normaliza nomes para capitalização correta."""
    if not nome:
        return ""
    return " ".join(word.capitalize() for word in nome.strip().split())


def detectar_tipo_pessoa(dados: Dict) -> str:
    """Detecta se é pessoa física ou jurídica baseado nos dados."""
    # Verifica se tem dados de PJ
    if dados.get("cnpj") or dados.get("razao_social"):
        return "pj"

    # Verifica se tem dados de PF
    if dados.get("cpf") or dados.get("primeiro_nome"):
        return "pf"

    # Por padrão, assume pessoa física
    return "pf"


def mapear_dados_para_cliente(dados_linha: Dict) -> Optional[Dict]:
    """Mapeia dados da planilha para o modelo Cliente.

    A lógica segue a estrutura real identificada nos cabeçalhos.
    """
    try:
        dados_mapeados = {}
        aba_origem = dados_linha.get("_aba_origem", "Desconhecida")

        # Mapeamento específico baseado na análise da planilha
        if aba_origem == "Respostas":
            # Email (obrigatório)
            email = dados_linha.get("Email", "").strip().lower()
            if not email or not validate_email(email):
                logger.warning(
                    (
                        "Linha %s da aba '%s': Email inválido ou não encontrado ('%s')"
                        % (dados_linha.get("_linha_original", "?"), aba_origem, email)
                    )
                )
                return None
            dados_mapeados["email"] = email

            # Nome e Sobrenome
            primeiro_nome = normalizar_nome(dados_linha.get("Primeiro Nome", ""))
            sobrenome = normalizar_nome(dados_linha.get("Sobrenome", ""))
            if not primeiro_nome:
                logger.warning(
                    (
                        "Linha %s: Primeiro Nome não encontrado."
                        % (dados_linha.get("_linha_original", "?"))
                    )
                )
                return None
            dados_mapeados["primeiro_nome"] = primeiro_nome
            dados_mapeados["sobrenome"] = sobrenome

            # CPF
            cpf_bruto = limpar_documento(dados_linha.get("CPF", ""))
            if not validate_cpf(cpf_bruto):
                logger.warning(
                    (
                        "Linha %s: CPF inválido ('%s')"
                        % (dados_linha.get("_linha_original", "?"), cpf_bruto)
                    )
                )
                return None
            dados_mapeados["cpf"] = cpf_bruto

            # Telefone
            dados_mapeados["telefone_celular"] = limpar_telefone(
                dados_linha.get("Telefone Celular", "")
            )

            # Dados Pessoais Adicionais
            dados_mapeados["nacionalidade"] = truncate_str(
                normalizar_nome(dados_linha.get("Nacionalidade", "Brasileiro(a)")), 32
            )
            dados_mapeados["rg_numero"] = dados_linha.get("RG", "")
            dados_mapeados["rg_orgao_emissor"] = dados_linha.get("Órgão Emissor", "")
            dados_mapeados["rg_uf_emissor"] = dados_linha.get("UF Emissor", "")
            dados_mapeados["profissao"] = truncate_str(
                normalizar_nome(dados_linha.get("Profissão", "")), 64
            )
            dados_mapeados["cnh_numero"] = dados_linha.get("CNH", "")

            # Data de Nascimento
            data_nasc_str = dados_linha.get("Data de Nascimento")
            if data_nasc_str:
                try:
                    # Tenta múltiplos formatos, comum em planilhas
                    dados_mapeados["data_nascimento"] = datetime.strptime(
                        data_nasc_str, "%d/%m/%Y"
                    ).date()
                except ValueError:
                    try:
                        dados_mapeados["data_nascimento"] = datetime.strptime(
                            data_nasc_str, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        linha_id = dados_linha.get("_linha_original", "?")
                        msg = (
                            "Linha %s: formato de data de nascimento inválido ('%s')"
                            % (linha_id, data_nasc_str)
                        )
                        logger.warning(msg)
                        dados_mapeados["data_nascimento"] = None
            else:
                dados_mapeados["data_nascimento"] = None

            # Estado Civil - Mapear para os valores do Enum
            estado_civil_str = dados_linha.get("Estado Civil", "").upper()
            if "SOLTEIRO" in estado_civil_str:
                dados_mapeados["estado_civil"] = "SOLTEIRO"
            elif "CASADO" in estado_civil_str:
                dados_mapeados["estado_civil"] = "CASADO"
            elif "DIVORCIADO" in estado_civil_str:
                dados_mapeados["estado_civil"] = "DIVORCIADO"
            elif "VIUVO" in estado_civil_str or "VIÚVO" in estado_civil_str:
                dados_mapeados["estado_civil"] = "VIUVO"
            elif "UNIAO" in estado_civil_str or "UNIÃO" in estado_civil_str:
                dados_mapeados["estado_civil"] = "UNIAO_ESTAVEL"
            else:
                dados_mapeados["estado_civil"] = None

            # Endereço
            dados_mapeados["endereco_logradouro"] = dados_linha.get(
                "Endereço (Rua/Avenida)", ""
            )
            dados_mapeados["endereco_numero"] = dados_linha.get("Número", "")
            dados_mapeados["endereco_complemento"] = dados_linha.get("Complemento", "")
            dados_mapeados["endereco_bairro"] = dados_linha.get("Bairro", "")
            dados_mapeados["endereco_cidade"] = dados_linha.get("Cidade", "")
            dados_mapeados["endereco_estado"] = dados_linha.get("Estado (UF)", "")
            dados_mapeados["endereco_cep"] = limpar_documento(
                dados_linha.get("CEP", "")
            )

            # Sempre pessoa física para esta aba
            dados_mapeados["tipo_pessoa"] = TipoPessoaEnum.FISICA

        elif aba_origem == "Antigos":
            # Email (obrigatório)
            email = dados_linha.get("Email", "").strip().lower()
            if not email:
                logger.warning(
                    (
                        "Linha %s da aba '%s': Email não encontrado"
                        % (dados_linha.get("_linha_original", "?"), aba_origem)
                    )
                )
                return None

            dados_mapeados["email"] = email

            # Nome (usa primeiro nome limpo ou nome bruto)
            primeiro_nome = normalizar_nome(dados_linha.get("Primeiro Nome", ""))
            sobrenome = normalizar_nome(dados_linha.get("Sobrenome", ""))

            if not primeiro_nome:
                # Fallback para nome bruto
                nome_bruto = normalizar_nome(dados_linha.get("Primeiro Nome Bruto", ""))
                if nome_bruto:
                    # Tenta extrair primeiro e último nome
                    partes_nome = nome_bruto.split()
                    if len(partes_nome) >= 2:
                        primeiro_nome = partes_nome[0]
                        sobrenome = " ".join(partes_nome[1:])
                    else:
                        primeiro_nome = nome_bruto

            nome_completo = f"{primeiro_nome} {sobrenome}".strip()
            if not nome_completo:
                logger.warning(
                    (
                        "Linha %s: Nome não encontrado"
                        % dados_linha.get("_linha_original", "?")
                    )
                )
                return None

            dados_mapeados["nome_completo"] = nome_completo

            # O modelo Cliente não tem 'nome_completo', então separamos
            partes_nome = nome_completo.split()
            dados_mapeados["primeiro_nome"] = partes_nome[0] if partes_nome else ""
            dados_mapeados["sobrenome"] = (
                " ".join(partes_nome[1:]) if len(partes_nome) > 1 else ""
            )

            # CPF
            cpf = limpar_documento(dados_linha.get("CPF", ""))
            dados_mapeados["cpf"] = cpf

            # Telefone
            telefone = limpar_telefone(dados_linha.get("Telefone Celular", ""))
            dados_mapeados["telefone_celular"] = telefone

            # Sempre pessoa física para esta aba
            dados_mapeados["tipo_pessoa"] = TipoPessoaEnum.FISICA

        else:
            logger.warning(f"Aba '{aba_origem}' não tem mapeamento definido")
            return None

        return dados_mapeados

    except Exception as e:
        logger.error(
            (
                "Erro ao mapear dados da linha %s da aba '%s': %s"
                % (dados_linha.get("_linha_original", "?"), aba_origem, e)
            )
        )
        return None


def mapear_dados_para_resposta_form(dados_linha: Dict) -> Optional[Dict]:
    """Mapeia dados da planilha para o modelo RespostaForm (legado)."""
    try:
        aba_origem = dados_linha.get("_aba_origem", "Desconhecida")
        if aba_origem != "Respostas":
            logger.warning(
                (
                    "Aba '%s' não mapeada para RespostaForm; ignorando linha %s"
                    % (aba_origem, dados_linha.get("_linha_original", "?"))
                )
            )
            return None

        # Extrai e valida campos principais ---------------------------------
        email = dados_linha.get("Email", "").strip().lower()
        cpf = limpar_documento(dados_linha.get("CPF", ""))
        primeiro_nome = normalizar_nome(dados_linha.get("Primeiro Nome", ""))
        sobrenome = normalizar_nome(dados_linha.get("Sobrenome", ""))

        if not (email or cpf):
            logger.warning(
                (
                    "Linha %s: sem Email e sem CPF – ignorando"
                    % dados_linha.get("_linha_original", "?")
                )
            )
            return None

        # Gera submission_id determinístico (email+cpf) para evitar duplicatas
        identificador_base = f"{email}|{cpf}"
        submission_id = hashlib.sha256(identificador_base.encode()).hexdigest()[:32]

        # ------------------------ Endereço ----------------------------------
        logradouro = dados_linha.get("Endereço Logradouro", "").strip()
        numero = dados_linha.get("Endereço Número", "").strip()
        complemento = dados_linha.get("Endereço Complemento", "").strip()
        bairro = dados_linha.get("Endereço Bairro", "").strip()
        cidade = dados_linha.get("Endereço Cidade", "").strip()
        uf_endereco = dados_linha.get("Endereço UF", "").strip().upper()
        cep = dados_linha.get("Endereço CEP", "").strip()

        endereco_composto = ", ".join(
            filter(
                None,
                [
                    logradouro,
                    numero,
                    complemento,
                    bairro,
                    f"{cidade}-{uf_endereco}" if cidade or uf_endereco else "",
                    cep,
                ],
            )
        )

        # ------------------- Demais campos pessoais -------------------------
        nacionalidade = truncate_str(
            normalizar_nome(dados_linha.get("Nacionalidade", "")), 32
        )
        estado_civil = truncate_str(dados_linha.get("Estado Civil", "").strip(), 32)
        profissao = truncate_str(normalizar_nome(dados_linha.get("Profissão", "")), 64)
        telefone_celular = limpar_telefone(dados_linha.get("Telefone Celular", ""))
        outro_telefone = limpar_telefone(dados_linha.get("Telefone Outro", ""))
        rg = truncate_str(dados_linha.get("RG Número", "").strip(), 32)
        estado_emissor_rg = truncate_str(
            dados_linha.get("RG UF Emissor", "").strip(), 32
        )
        cnh = truncate_str(dados_linha.get("CNH Número", "").strip(), 32)

        # ------------------------ Data Nascimento ---------------------------
        data_nascimento = None
        data_nasc_str = dados_linha.get("Data Nascimento")
        if data_nasc_str:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    data_nascimento = datetime.strptime(data_nasc_str, fmt).date()
                    break
                except ValueError:
                    continue

        dados_mapeados = {
            "submission_id": submission_id,
            "timestamp_processamento": datetime.now(),
            "tipo_pessoa": "pf",  # Aba Respostas contém apenas PF
            "email": email,
            "primeiro_nome": primeiro_nome,
            "sobrenome": sobrenome,
            "cpf": cpf,
            "data_nascimento": str(data_nascimento) if data_nascimento else None,
            "rg": rg,
            "estado_emissor_rg": estado_emissor_rg,
            "nacionalidade": nacionalidade,
            "estado_civil": estado_civil,
            "profissao": profissao,
            "cnh": cnh,
            # Endereço estruturado
            "logradouro": truncate_str(logradouro, 128),
            "numero": truncate_str(numero, 16),
            "complemento": truncate_str(complemento, 64),
            "bairro": truncate_str(bairro, 64),
            "cidade": truncate_str(cidade, 64),
            "uf_endereco": truncate_str(uf_endereco, 32),
            "cep": truncate_str(cep, 16),
            # Campo legado: endereço completo
            "endereco": truncate_str(endereco_composto, 128),
            # Telefones
            "telefone_celular": truncate_str(telefone_celular, 32),
            "outro_telefone": truncate_str(outro_telefone, 32),
        }

        return dados_mapeados

    except Exception as e:
        logger.error(
            (
                "Erro ao mapear dados para RespostaForm (linha %s): %s"
                % (dados_linha.get("_linha_original", "?"), e)
            )
        )
        return None


def importar_para_cliente(dados: List[Dict]) -> Dict[str, int]:
    """Importa uma lista de dicionários para o modelo Cliente."""
    stats = {"criados": 0, "atualizados": 0, "erros": 0, "ignorados": 0}

    with app.app_context():
        for i, linha in enumerate(dados):
            try:
                dados_cliente = mapear_dados_para_cliente(linha)
                if not dados_cliente:
                    stats["ignorados"] += 1
                    continue

                cpf = dados_cliente.get("cpf")
                email = dados_cliente.get("email")

                if not cpf and not email:
                    logger.warning(f"Linha {i+2}: Ignorando por falta de CPF e Email.")
                    stats["ignorados"] += 1
                    continue

                # Lógica de busca: Tenta por CPF, depois por email
                cliente_existente = None
                if cpf:
                    cliente_existente = Cliente.query.filter_by(cpf=cpf).first()
                if not cliente_existente and email:
                    cliente_existente = Cliente.query.filter_by(email=email).first()

                if cliente_existente:
                    # Atualiza o cliente existente
                    logger.info(
                        f"Atualizando cliente existente com CPF/Email: {cpf or email}"
                    )
                    for key, value in dados_cliente.items():
                        if (
                            value is not None and value != ""
                        ):  # Não sobrescrever com vazio
                            setattr(cliente_existente, key, value)
                    stats["atualizados"] += 1
                else:
                    # Cria um novo cliente
                    logger.info(f"Criando novo cliente com CPF/Email: {cpf or email}")
                    cliente = Cliente(**dados_cliente)
                    db.session.add(cliente)
                    stats["criados"] += 1

                # Commit a cada 100 registros para não sobrecarregar
                if i % 100 == 0:
                    db.session.commit()

            except IntegrityError as e:
                db.session.rollback()
                logger.error(
                    (
                        "Erro de integridade na linha %s (CPF/Email: %s): %s"
                        % (i + 2, cpf or email, e)
                    )
                )
                stats["erros"] += 1
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erro inesperado na linha {i+2}: {e}")
                stats["erros"] += 1

        # Commit final
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro no commit final: {e}")
            stats["erros"] += 1

    return stats


def importar_para_resposta_form(dados: List[Dict]) -> Dict[str, int]:
    """Importa dados para a tabela RespostaForm (legado)."""
    estatisticas = {"total": len(dados), "importados": 0, "duplicados": 0, "erros": 0}

    with app.app_context():
        for linha in dados:
            try:
                dados_resposta = mapear_dados_para_resposta_form(linha)
                if not dados_resposta:
                    estatisticas["erros"] += 1
                    continue

                # Verifica duplicados
                resposta_existente = RespostaForm.query.filter_by(
                    submission_id=dados_resposta["submission_id"]
                ).first()

                if resposta_existente:
                    estatisticas["duplicados"] += 1
                    continue

                # Cria nova resposta
                resposta = RespostaForm(**dados_resposta)
                db.session.add(resposta)
                db.session.commit()

                logger.info(f"Resposta importada: {resposta.email}")
                estatisticas["importados"] += 1

            except IntegrityError as e:
                db.session.rollback()
                logger.warning(f"Violação de integridade: {e}")
                estatisticas["duplicados"] += 1
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erro ao importar resposta: {e}")
                estatisticas["erros"] += 1

    return estatisticas


def main():
    """Função principal do script."""
    try:
        logger.info("=== INICIANDO IMPORTAÇÃO DA PLANILHA ===")
        logger.info(f"ID da planilha: {PLANILHA_ID}")

        # Obtém serviço do Google Sheets
        service = get_sheets_service()

        # Escolhe as abas para importar
        print("\nAbas disponíveis:")
        print("1 - Respostas (324 linhas) - Recomendada")
        print("2 - Antigos (189 linhas)")
        print("3 - Ambas")

        escolha_aba = input("Escolha a(s) aba(s) para importar (1, 2 ou 3): ").strip()

        abas_para_importar = []
        if escolha_aba in ["1", "3"]:
            abas_para_importar.append("Respostas")
        if escolha_aba in ["2", "3"]:
            abas_para_importar.append("Antigos")

        if not abas_para_importar:
            logger.error("Nenhuma aba selecionada")
            return

        # Busca dados de todas as abas selecionadas
        todos_dados = []
        for aba in abas_para_importar:
            logger.info(f"Buscando dados da aba '{aba}'...")
            dados_aba = buscar_dados_planilha(service, aba)
            todos_dados.extend(dados_aba)

        if not todos_dados:
            logger.error("Nenhum dado encontrado para importar")
            return

        logger.info(f"Total de {len(todos_dados)} linhas encontradas em todas as abas")

        # Mostra estatísticas por aba
        for aba in abas_para_importar:
            dados_aba = [d for d in todos_dados if d.get("_aba_origem") == aba]
            logger.info(f"Aba '{aba}': {len(dados_aba)} linhas")

        # Pergunta ao usuário qual tabela usar
        print("\nEscolha a tabela de destino:")
        print("1 - Cliente (novo sistema)")
        print("2 - RespostaForm (sistema legado)")
        print("3 - Ambas")

        escolha_tabela = input("Digite sua escolha (1, 2 ou 3): ").strip()

        if escolha_tabela in ["1", "3"]:
            logger.info("=== IMPORTANDO PARA TABELA CLIENTE ===")
            stats_cliente = importar_para_cliente(todos_dados)
            print("\n📊 ESTATÍSTICAS - TABELA CLIENTE:")
            total_processado_cliente = sum(stats_cliente.values())
            print(f"  Total de linhas processadas: {total_processado_cliente}")
            print(f"  Clientes criados: {stats_cliente['criados']}")
            print(f"  Clientes atualizados: {stats_cliente['atualizados']}")
            print(
                "  Linhas ignoradas (dados inválidos/insuficientes): "
                f"{stats_cliente['ignorados']}"
            )
            print(f"  Erros: {stats_cliente['erros']}")

        if escolha_tabela in ["2", "3"]:
            logger.info("=== IMPORTANDO PARA TABELA RESPOSTA_FORM ===")
            stats_resposta = importar_para_resposta_form(todos_dados)
            print("\n📊 ESTATÍSTICAS - TABELA RESPOSTA_FORM:")
            total_processado_respostas = sum(stats_resposta.values())
            print(f"  Total de linhas processadas: {total_processado_respostas}")
            print(f"  Respostas criadas: {stats_resposta['importados']}")
            print(
                "  Respostas ignoradas (duplicadas/erros): "
                f"{stats_resposta['duplicados']}"
            )
            print(f"  Erros: {stats_resposta['erros']}")

        logger.info("=== IMPORTAÇÃO CONCLUÍDA ===")

    except Exception as e:
        logger.error(f"Erro durante a importação: {e}")
        raise


if __name__ == "__main__":
    main()
