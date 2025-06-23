"""Camada de serviço para geração de documentos Google Docs.

Responsável por encapsular regras de negócio, acesso aos serviços
Google e tratamento de exceções de quota.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from flask import current_app
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from document_generator import (
    _initialize_google_services,
    buscar_ou_criar_pasta_cliente,
    gerar_documento_cliente,
)


class DocumentGenerationService:
    """Service para gerar documentos a partir dos dados de um cliente."""

    def __init__(self):
        """Inicializa o serviço com lazy loading dos serviços Google."""
        self._drive_service = None
        self._docs_service = None
        self._sheets_service = None

    @property
    def drive_service(self):
        """Lazy loading do Drive service."""
        if self._drive_service is None:
            try:
                self._drive_service = build(
                    "drive", "v3", credentials=self._get_credentials()
                )
            except Exception as e:
                raise
        return self._drive_service

    @property
    def docs_service(self):
        """Lazy loading do Docs service."""
        if self._docs_service is None:
            try:
                self._docs_service = build(
                    "docs", "v1", credentials=self._get_credentials()
                )
            except Exception as e:
                raise
        return self._docs_service

    @property
    def sheets_service(self):
        """Lazy loading do Sheets service."""
        if self._sheets_service is None:
            try:
                self._sheets_service = build(
                    "sheets", "v4", credentials=self._get_credentials()
                )
            except Exception as e:
                raise
        return self._sheets_service

    def _get_credentials(self):
        """Obtém credenciais do Google."""
        try:
            from config import CONFIG

            credentials_json = CONFIG.get("GOOGLE_CREDENTIALS_AS_JSON_STR")

            if not credentials_json:
                raise ValueError("Credenciais Google não configuradas")

            credentials = service_account.Credentials.from_service_account_info(
                json.loads(credentials_json),
                scopes=[
                    "https://www.googleapis.com/auth/drive",
                    "https://www.googleapis.com/auth/documents",
                    "https://www.googleapis.com/auth/spreadsheets",
                ],
            )
            return credentials
        except Exception as e:
            raise

    def generate_documents(
        self,
        dados_cliente: dict,
        tipo_pessoa: str,
        documentos_requeridos: Iterable[str] | None = None,
    ) -> List[str]:
        """Gera documentos e retorna links."""
        from config import CONFIG

        with open(
            "/var/www/estevaoalmeida.com.br/form-google/debug_dados_cliente.log", "a"
        ) as f:
            f.write(f"[DEBUG] Tipo de dados_cliente: {type(dados_cliente)}\n")
            f.write(f"[DEBUG] Conteúdo de dados_cliente: {dados_cliente}\n")

        current_app.logger.info(
            f"generate_documents iniciado com dados_cliente: {dados_cliente}"
        )
        current_app.logger.info(f"tipo_pessoa: {tipo_pessoa}")
        current_app.logger.info(f"documentos_requeridos: {documentos_requeridos}")

        templates_disponiveis = CONFIG["TEMPLATES"].get(tipo_pessoa, {})
        current_app.logger.info(f"templates_disponiveis: {templates_disponiveis}")

        docs_a_gerar = documentos_requeridos or templates_disponiveis.keys()
        current_app.logger.info(f"docs_a_gerar: {docs_a_gerar}")

        # Pasta do cliente - garantir que nome e sobrenome estejam presentes
        primeiro_nome = (
            dados_cliente.get("primeiroNome")
            or dados_cliente.get("nome")
            or dados_cliente.get("Primeiro Nome", "")
        )
        sobrenome = dados_cliente.get("sobrenome") or dados_cliente.get("Sobrenome", "")

        # Se não encontrar nome estruturado, tentar nome completo
        if not primeiro_nome and dados_cliente.get("nomeCompleto"):
            nome_completo = dados_cliente.get("nomeCompleto", "").strip()
            partes_nome = nome_completo.split(" ", 1)
            primeiro_nome = partes_nome[0]
            sobrenome = partes_nome[1] if len(partes_nome) > 1 else ""

        # Se ainda não tiver nome ou sobrenome, lançar exceção e logar
        if not primeiro_nome or not sobrenome:
            msg = (
                f"[ERRO] Nome ou sobrenome ausente para dados_cliente: {dados_cliente}"
            )
            current_app.logger.error(msg)
            with open(
                "/var/www/estevaoalmeida.com.br/form-google/debug_dados_cliente.log",
                "a",
            ) as f:
                f.write(msg + "\n")
            raise ValueError(
                "Nome e sobrenome do cliente são obrigatórios para criação da pasta!"
            )

        current_app.logger.info(
            f"Gerando pasta para: primeiro_nome='{primeiro_nome}', sobrenome='{sobrenome}'"
        )
        with open(
            "/var/www/estevaoalmeida.com.br/form-google/debug_dados_cliente.log", "a"
        ) as f:
            f.write(
                f"[DEBUG] Gerando pasta para: primeiro_nome='{primeiro_nome}', sobrenome='{sobrenome}'\n"
            )

        try:
            pasta_id = buscar_ou_criar_pasta_cliente(
                drive_service=self.drive_service,
                primeiro_nome=primeiro_nome,
                sobrenome=sobrenome,
                ano=datetime.now().year,
            )
            current_app.logger.info(f"Pasta criada/encontrada com ID: {pasta_id}")

            with open(
                "/var/www/estevaoalmeida.com.br/form-google/debug_dados_cliente.log",
                "a",
            ) as f:
                f.write(f"[DEBUG] Pasta criada/encontrada com ID: {pasta_id}\n")

        except Exception as e:
            current_app.logger.error(f"Erro ao criar pasta: {e}", exc_info=True)

            with open(
                "/var/www/estevaoalmeida.com.br/form-google/debug_dados_cliente.log",
                "a",
            ) as f:
                f.write(f"[DEBUG] Erro ao criar pasta: {e}\n")

            raise RuntimeError(
                f"Falha ao criar/encontrar pasta do cliente no Drive: {e}"
            )

        if not pasta_id:
            raise RuntimeError("Falha ao criar/encontrar pasta do cliente no Drive")

        links = []
        for tipo_doc in docs_a_gerar:
            current_app.logger.info(f"Processando documento: {tipo_doc}")
            id_template = templates_disponiveis.get(tipo_doc)
            if not id_template:
                current_app.logger.warning(
                    f"Template ID para '{tipo_doc}' não encontrado em CONFIG. Pulando."
                )
                continue

            try:
                current_app.logger.info(
                    f"Gerando documento {tipo_doc} com template {id_template}"
                )

                with open(
                    "/var/www/estevaoalmeida.com.br/form-google/debug_dados_cliente.log",
                    "a",
                ) as f:
                    f.write(
                        f"[DEBUG] Gerando documento {tipo_doc} com template {id_template}\n"
                    )

                resultado = gerar_documento_cliente(
                    drive_service=self.drive_service,
                    docs_service=self.docs_service,
                    id_template=id_template,
                    tipo_doc=tipo_doc,
                    dados_cliente=dados_cliente,
                    id_pasta_cliente=pasta_id,
                    tipo_pessoa=tipo_pessoa,
                )
                current_app.logger.info(
                    f"Resultado da geração do documento {tipo_doc}: {resultado}"
                )

                with open(
                    "/var/www/estevaoalmeida.com.br/form-google/debug_dados_cliente.log",
                    "a",
                ) as f:
                    f.write(
                        f"[DEBUG] Resultado da geração do documento {tipo_doc}: {resultado}\n"
                    )

                if resultado and resultado.get("status") == "sucesso":
                    links.append(resultado["link_documento"])
                    current_app.logger.info(
                        f"Documento {tipo_doc} gerado com sucesso: {resultado['link_documento']}"
                    )
                else:
                    current_app.logger.error(
                        f"Falha na geração do documento {tipo_doc}: {resultado}"
                    )

            except Exception as e:
                current_app.logger.error(
                    f"Erro ao gerar documento {tipo_doc}: {e}", exc_info=True
                )

                with open(
                    "/var/www/estevaoalmeida.com.br/form-google/debug_dados_cliente.log",
                    "a",
                ) as f:
                    f.write(f"[DEBUG] Erro ao gerar documento {tipo_doc}: {e}\n")

        current_app.logger.info(
            "Documentos gerados para %s %s: %s", primeiro_nome, sobrenome, links
        )
        return links
