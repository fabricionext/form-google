#!/usr/bin/env python3
"""
Script para analisar a estrutura da planilha Google Sheets
ID: 1Hj0D-VeJ51nQdAOBlvwzTKR_S3Sls40drthXfLI9Eow
antes da importação para o banco de dados.
"""

import os
import logging
from typing import Dict, List

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


def listar_abas(service) -> List[str]:
    """Lista todas as abas da planilha."""
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=PLANILHA_ID).execute()
        sheets = sheet_metadata.get('sheets', [])
        
        abas = []
        for sheet in sheets:
            properties = sheet.get("properties", {})
            nome_aba = properties.get("title", "Sem nome")
            abas.append(nome_aba)
        
        return abas
        
    except Exception as e:
        logger.error(f"Erro ao listar abas: {e}")
        raise


def analisar_aba(service, nome_aba: str) -> Dict:
    """Analisa a estrutura de uma aba específica."""
    try:
        range_name = f"{nome_aba}!A:ZZ"
        
        result = service.spreadsheets().values().get(
            spreadsheetId=PLANILHA_ID,
            range=range_name
        ).execute()
        
        values = result.get("values", [])
        
        if not values:
            return {
                "nome": nome_aba,
                "total_linhas": 0,
                "cabecalhos": [],
                "linhas_dados": 0,
                "colunas": 0,
                "amostra_dados": []
            }
        
        # Primeira linha são os cabeçalhos
        headers = [str(header).strip() for header in values[0]]
        
        # Conta linhas com dados
        linhas_dados = 0
        amostra_dados = []
        
        for i, row in enumerate(values[1:], start=2):
            if any(str(cell).strip() for cell in row if cell):  # Se tem alguma célula não vazia
                linhas_dados += 1
                
                # Pega amostra das primeiras 3 linhas
                if len(amostra_dados) < 3:
                    linha_dict = {}
                    for j, header in enumerate(headers):
                        if j < len(row):
                            linha_dict[header] = str(row[j]).strip()
                        else:
                            linha_dict[header] = ""
                    amostra_dados.append(linha_dict)
        
        return {
            "nome": nome_aba,
            "total_linhas": len(values),
            "cabecalhos": headers,
            "linhas_dados": linhas_dados,
            "colunas": len(headers),
            "amostra_dados": amostra_dados
        }
        
    except Exception as e:
        logger.error(f"Erro ao analisar aba '{nome_aba}': {e}")
        return {
            "nome": nome_aba,
            "erro": str(e)
        }


def detectar_tipo_dados(cabecalhos: List[str]) -> Dict[str, str]:
    """Detecta o tipo de dados baseado nos nomes dos cabeçalhos."""
    tipos_detectados = {}
    
    # Mapeamentos comuns
    mapeamentos = {
        # Identificação
        "email": ["email", "e-mail", "e_mail", "mail"],
        "nome": ["nome", "primeiro_nome", "nome_completo", "full_name"],
        "sobrenome": ["sobrenome", "ultimo_nome", "last_name"],
        "razao_social": ["razao_social", "empresa", "company", "nome_empresa"],
        
        # Documentos
        "cpf": ["cpf", "documento", "doc"],
        "cnpj": ["cnpj", "cnpj_empresa"],
        "rg": ["rg", "identidade"],
        
        # Contato
        "telefone": ["telefone", "celular", "phone", "tel", "whatsapp"],
        "endereco": ["endereco", "address", "rua", "street"],
        "cidade": ["cidade", "city"],
        "estado": ["estado", "uf", "state"],
        "cep": ["cep", "zip", "zipcode"],
        
        # Pessoais
        "nascimento": ["nascimento", "data_nascimento", "birth", "birthday"],
        "profissao": ["profissao", "occupation", "trabalho"],
        "estado_civil": ["estado_civil", "marital"],
        "nacionalidade": ["nacionalidade", "nationality"],
        
        # Outros
        "timestamp": ["timestamp", "data", "date", "carimbo"],
    }
    
    for cabecalho in cabecalhos:
        cabecalho_lower = cabecalho.lower().strip()
        tipo_detectado = "outro"
        
        for tipo, variantes in mapeamentos.items():
            for variante in variantes:
                if variante in cabecalho_lower:
                    tipo_detectado = tipo
                    break
            if tipo_detectado != "outro":
                break
        
        tipos_detectados[cabecalho] = tipo_detectado
    
    return tipos_detectados


def main():
    """Função principal do script."""
    try:
        print("=" * 60)
        print("ANÁLISE DA PLANILHA GOOGLE SHEETS")
        print("=" * 60)
        print(f"ID da planilha: {PLANILHA_ID}")
        print()
        
        # Obtém serviço do Google Sheets
        service = get_sheets_service()
        
        # Lista todas as abas
        logger.info("Listando abas da planilha...")
        abas = listar_abas(service)
        
        print(f"Total de abas encontradas: {len(abas)}")
        print(f"Abas: {', '.join(abas)}")
        print()
        
        # Analisa cada aba
        for i, aba in enumerate(abas, 1):
            print(f"[{i}/{len(abas)}] ANALISANDO ABA: '{aba}'")
            print("-" * 50)
            
            analise = analisar_aba(service, aba)
            
            if "erro" in analise:
                print(f"❌ Erro ao analisar: {analise['erro']}")
                print()
                continue
            
            print(f"📊 Total de linhas: {analise['total_linhas']}")
            print(f"📊 Linhas com dados: {analise['linhas_dados']}")
            print(f"📊 Total de colunas: {analise['colunas']}")
            print()
            
            if analise['cabecalhos']:
                print("📋 CABEÇALHOS ENCONTRADOS:")
                tipos = detectar_tipo_dados(analise['cabecalhos'])
                
                for j, cabecalho in enumerate(analise['cabecalhos'], 1):
                    tipo = tipos.get(cabecalho, "outro")
                    emoji = {
                        "email": "📧",
                        "nome": "👤",
                        "cpf": "🆔",
                        "cnpj": "🏢",
                        "telefone": "📱",
                        "endereco": "🏠",
                        "nascimento": "🎂",
                        "timestamp": "⏰",
                        "outro": "❓"
                    }.get(tipo, "❓")
                    
                    print(f"  {j:2d}. {emoji} {cabecalho} ({tipo})")
                
                print()
                
                # Mostra amostra de dados
                if analise['amostra_dados']:
                    print("📝 AMOSTRA DE DADOS (primeiras linhas):")
                    for idx, linha in enumerate(analise['amostra_dados'], 1):
                        print(f"  Linha {idx}:")
                        for campo, valor in list(linha.items())[:5]:  # Mostra só os 5 primeiros campos
                            if valor:  # Só mostra campos não vazios
                                valor_truncado = valor[:50] + "..." if len(valor) > 50 else valor
                                print(f"    {campo}: {valor_truncado}")
                        print()
            else:
                print("⚠️  Nenhum cabeçalho encontrado")
            
            print()
        
        # Recomendações
        print("💡 RECOMENDAÇÕES PARA IMPORTAÇÃO:")
        print("-" * 40)
        
        melhor_aba = None
        maior_dados = 0
        
        for aba in abas:
            analise = analisar_aba(service, aba)
            if analise.get('linhas_dados', 0) > maior_dados:
                maior_dados = analise['linhas_dados']
                melhor_aba = aba
        
        if melhor_aba:
            print(f"🎯 Aba recomendada para importação: '{melhor_aba}' ({maior_dados} linhas)")
            
            # Analisa a melhor aba em detalhes
            analise_detalhada = analisar_aba(service, melhor_aba)
            tipos = detectar_tipo_dados(analise_detalhada['cabecalhos'])
            
            # Campos essenciais encontrados
            essenciais_encontrados = []
            essenciais_perdidos = []
            
            campos_essenciais = ["email", "nome", "cpf", "telefone"]
            
            for essencial in campos_essenciais:
                encontrado = any(tipo == essencial for tipo in tipos.values())
                if encontrado:
                    essenciais_encontrados.append(essencial)
                else:
                    essenciais_perdidos.append(essencial)
            
            if essenciais_encontrados:
                print(f"✅ Campos essenciais encontrados: {', '.join(essenciais_encontrados)}")
            
            if essenciais_perdidos:
                print(f"⚠️  Campos essenciais não detectados: {', '.join(essenciais_perdidos)}")
            
        else:
            print("⚠️  Nenhuma aba com dados encontrada")
        
        print()
        print("🚀 Para executar a importação, use:")
        print("   python import_planilha_especifica.py")
        print()
        
    except Exception as e:
        logger.error(f"Erro durante a análise: {e}")
        raise


if __name__ == "__main__":
    main()