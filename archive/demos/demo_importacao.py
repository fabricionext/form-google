#!/usr/bin/env python3
"""
Demo da importação de dados da planilha Google Sheets
sem conexão real ao banco de dados.
"""

import os
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ID da planilha específica
PLANILHA_ID = "1Hj0D-VeJ51nQdAOBlvwzTKR_S3Sls40drthXfLI9Eow"


def get_sheets_service():
    """Obtém o serviço do Google Sheets."""
    try:
        service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not service_account_file:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON não configurado")
        
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
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
        range_name = f"{sheet_name}!A:ZZ"
        
        result = service.spreadsheets().values().get(
            spreadsheetId=PLANILHA_ID,
            range=range_name
        ).execute()
        
        values = result.get("values", [])
        if not values:
            logger.warning(f"Nenhum dado encontrado na aba '{sheet_name}'")
            return []
        
        headers = [str(header).strip() for header in values[0]]
        logger.info(f"Cabeçalhos encontrados na aba '{sheet_name}': {headers}")
        
        dados = []
        for i, row in enumerate(values[1:], start=2):
            while len(row) < len(headers):
                row.append("")
            
            linha_dict = {headers[j]: str(row[j]).strip() if j < len(row) else "" 
                         for j in range(len(headers))}
            
            if any(linha_dict.values()):
                linha_dict["_linha_original"] = i
                linha_dict["_aba_origem"] = sheet_name
                dados.append(linha_dict)
        
        logger.info(f"Total de {len(dados)} linhas de dados encontradas na aba '{sheet_name}'")
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


def validate_cpf(cpf: str) -> tuple[bool, str]:
    """Valida CPF usando o algoritmo oficial."""
    if not cpf:
        return False, "CPF é obrigatório"
    
    cpf_digits = re.sub(r'\D', '', cpf)
    
    if len(cpf_digits) != 11:
        return False, "CPF deve ter 11 dígitos"
    
    if cpf_digits == cpf_digits[0] * 11:
        return False, "CPF inválido"
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf_digits[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_digits[9]) != dv1:
        return False, "CPF inválido"
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf_digits[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_digits[10]) != dv2:
        return False, "CPF inválido"
    
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Valida formato de email."""
    if not email:
        return False, "Email é obrigatório"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    return True, ""


def mapear_dados_para_cliente(dados_linha: Dict) -> Optional[Dict]:
    """Mapeia dados da planilha para o modelo Cliente."""
    try:
        dados_mapeados = {}
        aba_origem = dados_linha.get("_aba_origem", "Desconhecida")
        
        if aba_origem == "Respostas":
            # Email (obrigatório)
            email = dados_linha.get("Email", "").strip().lower()
            if not email:
                logger.warning(f"Linha {dados_linha.get('_linha_original', '?')} da aba '{aba_origem}': Email não encontrado")
                return None
            
            dados_mapeados["email"] = email
            
            # Nome completo
            primeiro_nome = normalizar_nome(dados_linha.get("Primeiro Nome", ""))
            sobrenome = normalizar_nome(dados_linha.get("Sobrenome", ""))
            nome_completo = f"{primeiro_nome} {sobrenome}".strip()
            
            if not nome_completo:
                logger.warning(f"Linha {dados_linha.get('_linha_original', '?')}: Nome não encontrado")
                return None
            
            dados_mapeados["nome_completo"] = nome_completo
            dados_mapeados["cpf"] = limpar_documento(dados_linha.get("CPF", ""))
            dados_mapeados["telefone_celular"] = limpar_telefone(dados_linha.get("Telefone Celular", ""))
            dados_mapeados["tipo_pessoa"] = "FISICA"
            
        elif aba_origem == "Antigos":
            # Email (obrigatório)
            email = dados_linha.get("Email", "").strip().lower()
            if not email:
                logger.warning(f"Linha {dados_linha.get('_linha_original', '?')} da aba '{aba_origem}': Email não encontrado")
                return None
            
            dados_mapeados["email"] = email
            
            # Nome
            primeiro_nome = normalizar_nome(dados_linha.get("Primeiro Nome", ""))
            sobrenome = normalizar_nome(dados_linha.get("Sobrenome", ""))
            
            if not primeiro_nome:
                nome_bruto = normalizar_nome(dados_linha.get("Primeiro Nome Bruto", ""))
                if nome_bruto:
                    partes_nome = nome_bruto.split()
                    if len(partes_nome) >= 2:
                        primeiro_nome = partes_nome[0]
                        sobrenome = " ".join(partes_nome[1:])
                    else:
                        primeiro_nome = nome_bruto
            
            nome_completo = f"{primeiro_nome} {sobrenome}".strip()
            if not nome_completo:
                logger.warning(f"Linha {dados_linha.get('_linha_original', '?')}: Nome não encontrado")
                return None
            
            dados_mapeados["nome_completo"] = nome_completo
            dados_mapeados["cpf"] = limpar_documento(dados_linha.get("CPF", ""))
            dados_mapeados["telefone_celular"] = limpar_telefone(dados_linha.get("Telefone Celular", ""))
            dados_mapeados["tipo_pessoa"] = "FISICA"
            
        else:
            logger.warning(f"Aba '{aba_origem}' não tem mapeamento definido")
            return None
        
        return dados_mapeados
        
    except Exception as e:
        logger.error(f"Erro ao mapear dados da linha {dados_linha.get('_linha_original', '?')}: {e}")
        return None


def simular_importacao(dados: List[Dict]) -> Dict[str, int]:
    """Simula a importação dos dados (sem salvar no banco real)."""
    estatisticas = {
        "total": len(dados),
        "importados": 0,
        "duplicados": 0,
        "erros": 0
    }
    
    emails_existentes = set()  # Simula emails já existentes no banco
    cpfs_existentes = set()    # Simula CPFs já existentes no banco
    
    clientes_validos = []
    
    for linha in dados:
        try:
            dados_cliente = mapear_dados_para_cliente(linha)
            if not dados_cliente:
                estatisticas["erros"] += 1
                continue
            
            # Validação de email
            if dados_cliente.get("email"):
                is_valid, error_msg = validate_email(dados_cliente["email"])
                if not is_valid:
                    logger.warning(f"Email inválido ({dados_cliente['email']}): {error_msg}")
                    estatisticas["erros"] += 1
                    continue
            
            # Validação de CPF
            if dados_cliente.get("cpf"):
                is_valid, error_msg = validate_cpf(dados_cliente["cpf"])
                if not is_valid:
                    logger.warning(f"CPF inválido ({dados_cliente['cpf']}): {error_msg}")
                    estatisticas["erros"] += 1
                    continue
            
            # Verifica duplicados (simulação)
            email = dados_cliente.get("email")
            cpf = dados_cliente.get("cpf")
            
            if email in emails_existentes or cpf in cpfs_existentes:
                logger.info(f"Cliente já existe: {dados_cliente.get('email', dados_cliente.get('nome_completo', 'N/A'))}")
                estatisticas["duplicados"] += 1
                continue
            
            # "Salva" o cliente (simulação)
            if email:
                emails_existentes.add(email)
            if cpf:
                cpfs_existentes.add(cpf)
            
            clientes_validos.append(dados_cliente)
            logger.info(f"Cliente válido para importação: {dados_cliente['nome_completo']}")
            estatisticas["importados"] += 1
            
        except Exception as e:
            logger.error(f"Erro ao processar cliente: {e}")
            estatisticas["erros"] += 1
    
    return estatisticas, clientes_validos


def main():
    """Função principal da demonstração."""
    try:
        print("=" * 60)
        print("🚀 DEMONSTRAÇÃO DE IMPORTAÇÃO DA PLANILHA")
        print("=" * 60)
        print(f"ID da planilha: {PLANILHA_ID}")
        print()
        
        # Obtém serviço do Google Sheets
        service = get_sheets_service()
        
        # Busca dados da aba Respostas (demonstração)
        logger.info("Buscando dados da aba 'Respostas'...")
        dados = buscar_dados_planilha(service, "Respostas")
        
        if not dados:
            logger.error("Nenhum dado encontrado para importar")
            return
        
        # Limita a amostra para demonstração (primeiros 50 registros)
        dados_amostra = dados[:50]
        logger.info(f"Processando amostra de {len(dados_amostra)} registros de {len(dados)} totais")
        
        # Mostra amostra dos dados
        print("\n📋 AMOSTRA DOS DADOS ENCONTRADOS:")
        print("-" * 40)
        for i, linha in enumerate(dados_amostra[:5], 1):
            nome = f"{linha.get('Primeiro Nome', '')} {linha.get('Sobrenome', '')}".strip()
            email = linha.get('Email', '')
            cpf = linha.get('CPF', '')
            print(f"  {i}. Nome: {nome}")
            print(f"     Email: {email}")
            print(f"     CPF: {cpf}")
            print()
        
        if len(dados_amostra) > 5:
            print(f"  ... e mais {len(dados_amostra) - 5} registros na amostra")
        
        # Simula a importação
        print("\n🔄 SIMULANDO IMPORTAÇÃO...")
        print("-" * 40)
        stats, clientes_validos = simular_importacao(dados_amostra)
        
        # Mostra resultados
        print("\n" + "="*60)
        print("🎯 RESULTADOS DA SIMULAÇÃO")
        print("="*60)
        print(f"📊 Total de registros processados: {stats['total']}")
        print(f"✅ Clientes válidos para importação: {stats['importados']}")
        print(f"⚠️  Registros duplicados (ignorados): {stats['duplicados']}")
        print(f"❌ Registros com erro: {stats['erros']}")
        
        # Taxa de sucesso
        if stats['total'] > 0:
            taxa_sucesso = (stats['importados'] / stats['total']) * 100
            print(f"📈 Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        # Mostra alguns clientes válidos
        if clientes_validos:
            print(f"\n👥 EXEMPLOS DE CLIENTES VÁLIDOS:")
            print("-" * 40)
            for i, cliente in enumerate(clientes_validos[:5], 1):
                print(f"  {i}. {cliente['nome_completo']}")
                print(f"     Email: {cliente['email']}")
                print(f"     CPF: {cliente.get('cpf', 'Não informado')}")
                print(f"     Telefone: {cliente.get('telefone_celular', 'Não informado')}")
                print()
        
        print("\n🎉 Para executar a importação real:")
        print("   1. Configure a conexão com o banco de dados")
        print("   2. Execute: python import_planilha_especifica.py")
        print("   3. Escolha as abas e tabelas de destino")
        print()
        print("✅ Demonstração concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante a demonstração: {e}")
        raise


if __name__ == "__main__":
    main() 