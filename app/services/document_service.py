"""
Serviço para geração de documentos Google Docs com melhorias de performance e tratamento de erros.
"""

import asyncio
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class DocumentResult:
    """Resultado da geração de um documento"""

    tipo_documento: str
    link: str
    id: str
    nome_arquivo: str
    sucesso: bool = True
    erro: Optional[str] = None


@dataclass
class ClienteData:
    """Dados do cliente para geração de documentos"""

    tipo_pessoa: str
    primeiro_nome: str
    sobrenome: str
    email: str
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    rg: Optional[str] = None
    cnh: Optional[str] = None
    data_nascimento: Optional[str] = None
    telefone_celular: Optional[str] = None
    endereco_logradouro: Optional[str] = None
    endereco_numero: Optional[str] = None
    endereco_complemento: Optional[str] = None
    endereco_bairro: Optional[str] = None
    endereco_cidade: Optional[str] = None
    endereco_estado: Optional[str] = None
    endereco_cep: Optional[str] = None
    nacionalidade: Optional[str] = None
    estado_civil: Optional[str] = None
    profissao: Optional[str] = None
    estado_emissor_rg: Optional[str] = None


class DocumentService:
    """Service para gerar documentos com melhorias de performance e tratamento de erros"""

    def __init__(self, config: Dict):
        self.config = config
        self._google_services = None
        self._executor = ThreadPoolExecutor(max_workers=5)

    @property
    def google_services(self):
        """Lazy loading dos serviços Google com cache"""
        if self._google_services is None:
            self._google_services = self._initialize_google_services()
        return self._google_services

    def _initialize_google_services(self):
        """Inicializa serviços do Google uma única vez"""
        credentials = self.config.get("GOOGLE_CREDENTIALS_AS_JSON_STR")
        if not credentials:
            raise ValueError("Credenciais do Google não configuradas")

        from document_generator import _initialize_google_services

        return _initialize_google_services(credentials)

    def gerar_documentos_cliente(
        self, cliente_data: ClienteData
    ) -> Tuple[List[DocumentResult], List[str]]:
        """
        Gera todos os documentos para um cliente

        Returns:
            Tuple com (sucessos, erros)
        """
        try:
            logger.info(
                f"Iniciando geração de documentos para cliente: {cliente_data.primeiro_nome} {cliente_data.sobrenome}"
            )

            # 1. Obter/criar pasta do cliente
            drive_service, docs_service = self.google_services
            id_pasta_cliente = self._obter_pasta_cliente(
                drive_service, cliente_data.primeiro_nome, cliente_data.sobrenome
            )

            # 2. Obter templates para o tipo de pessoa
            templates = self._obter_templates(cliente_data.tipo_pessoa)

            # 3. Gerar documentos em paralelo
            resultados = self._gerar_documentos_paralelo(
                templates, cliente_data, id_pasta_cliente
            )

            # 4. Separar sucessos e erros
            sucessos = [r for r in resultados if r.sucesso]
            erros = [r.erro for r in resultados if not r.sucesso]

            logger.info(
                f"Geração concluída: {len(sucessos)} sucessos, {len(erros)} erros"
            )
            return sucessos, erros

        except Exception as e:
            logger.error(f"Erro ao gerar documentos: {str(e)}", exc_info=True)
            raise

    def _obter_pasta_cliente(
        self, drive_service, primeiro_nome: str, sobrenome: str
    ) -> str:
        """Obtém ou cria a pasta do cliente"""
        from document_generator import buscar_ou_criar_pasta_cliente

        ano_atual = datetime.now().year
        return buscar_ou_criar_pasta_cliente(
            drive_service, primeiro_nome, sobrenome, ano_atual
        )

    def _obter_templates(self, tipo_pessoa: str) -> Dict[str, str]:
        """Obtém templates configurados para o tipo de pessoa"""
        templates = self.config["TEMPLATES"].get(tipo_pessoa, {})
        if not templates:
            raise ValueError(f"Nenhum template configurado para tipo: {tipo_pessoa}")
        return templates

    def _gerar_documentos_paralelo(
        self,
        templates: Dict[str, str],
        cliente_data: ClienteData,
        id_pasta_cliente: str,
    ) -> List[DocumentResult]:
        """Gera documentos em paralelo com controle de concorrência"""

        # Usar ThreadPoolExecutor para processamento paralelo
        futures = []
        for tipo_doc, template_id in templates.items():
            if not template_id:
                logger.warning(
                    f"Template ID para '{tipo_doc}' não encontrado. Pulando..."
                )
                continue

            future = self._executor.submit(
                self._gerar_documento_individual,
                tipo_doc,
                template_id,
                cliente_data,
                id_pasta_cliente,
            )
            futures.append(future)

        # Coletar resultados
        resultados = []
        for future in futures:
            try:
                resultado = future.result(timeout=60)  # Timeout de 60 segundos
                resultados.append(resultado)
            except Exception as e:
                logger.error(f"Erro ao aguardar resultado: {str(e)}")
                resultados.append(
                    DocumentResult(
                        tipo_documento="desconhecido",
                        link="",
                        id="",
                        nome_arquivo="",
                        sucesso=False,
                        erro=str(e),
                    )
                )

        return resultados

    def _gerar_documento_individual(
        self,
        tipo_doc: str,
        template_id: str,
        cliente_data: ClienteData,
        id_pasta_cliente: str,
    ) -> DocumentResult:
        """Gera um documento individual com tratamento de erro"""
        try:
            logger.info(f"Gerando documento: {tipo_doc}")
            drive_service, docs_service = self.google_services
            dados_mapeados = self._mapear_dados_cliente(cliente_data)

            from document_generator import gerar_documento_cliente

            resultado = gerar_documento_cliente(
                drive_service=drive_service,
                docs_service=docs_service,
                id_template=template_id,
                tipo_doc=tipo_doc,
                dados_cliente=dados_mapeados,
                id_pasta_cliente=id_pasta_cliente,
                tipo_pessoa=cliente_data.tipo_pessoa,
            )

            logger.info(f"Documento gerado com sucesso: {tipo_doc}")
            return DocumentResult(
                tipo_documento=tipo_doc,
                link=resultado["link_documento"],
                id=resultado["id_documento"],
                nome_arquivo=resultado["nome_arquivo"],
            )

        except Exception as e:
            logger.error(f"Erro ao gerar documento {tipo_doc}: {str(e)}", exc_info=True)
            return DocumentResult(
                tipo_documento=tipo_doc,
                link="",
                id="",
                nome_arquivo="",
                sucesso=False,
                erro=str(e),
            )

    def _mapear_dados_cliente(self, cliente_data: ClienteData) -> Dict[str, str]:
        """Mapeia dados do cliente para formato esperado pelos templates"""
        return {
            "Primeiro Nome": cliente_data.primeiro_nome or "",
            "Sobrenome": cliente_data.sobrenome or "",
            "E-mail": cliente_data.email or "",
            "CPF": cliente_data.cpf or "",
            "CNPJ": cliente_data.cnpj or "",
            "RG": cliente_data.rg or "",
            "CNH": cliente_data.cnh or "",
            "Nascimento": cliente_data.data_nascimento or "",
            "Telefone Celular": cliente_data.telefone_celular or "",
            "Nacionalidade": cliente_data.nacionalidade or "Brasileiro(a)",
            "Estado Civil": cliente_data.estado_civil or "",
            "Profissão": cliente_data.profissao or "",
            "Estado emissor do RG": cliente_data.estado_emissor_rg or "",
            # Endereço estruturado
            "Logradouro": cliente_data.endereco_logradouro or "",
            "Número": cliente_data.endereco_numero or "",
            "Complemento": cliente_data.endereco_complemento or "",
            "Bairro": cliente_data.endereco_bairro or "",
            "Cidade": cliente_data.endereco_cidade or "",
            "Estado": cliente_data.endereco_estado or "",
            "CEP": cliente_data.endereco_cep or "",
            # Endereço completo para compatibilidade
            "Endereço": self._montar_endereco_completo(cliente_data),
        }

    def _montar_endereco_completo(self, cliente_data: ClienteData) -> str:
        """Monta endereço completo para compatibilidade com templates antigos"""
        partes = []
        if cliente_data.endereco_logradouro:
            partes.append(cliente_data.endereco_logradouro)
        if cliente_data.endereco_numero:
            partes.append(cliente_data.endereco_numero)
        if cliente_data.endereco_complemento:
            partes.append(cliente_data.endereco_complemento)
        if cliente_data.endereco_bairro:
            partes.append(cliente_data.endereco_bairro)

        endereco = ", ".join(partes)
        if cliente_data.endereco_cidade and cliente_data.endereco_estado:
            endereco += (
                f", {cliente_data.endereco_cidade}/{cliente_data.endereco_estado}"
            )
        if cliente_data.endereco_cep:
            endereco += f" - CEP: {cliente_data.endereco_cep}"

        return endereco

    def __del__(self):
        """Cleanup do executor"""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=True)
