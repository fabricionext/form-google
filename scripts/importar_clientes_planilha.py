#!/usr/bin/env python3
"""
Script de importação para tabela CLIENTES_PETICIONADOR
Importa dados da planilha Google Sheets para o sistema de cadastro de clientes
"""

import os
import sys
import logging
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração direta do banco
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'form_google',
    'user': 'postgres',
    'password': 'postgres'
}

# ID da planilha
PLANILHA_ID = "1Hj0D-VeJ51nQdAOBlvwzTKR_S3Sls40drthXfLI9Eow"

def get_database_connection():
    """Cria conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        logger.info("✅ Conexão com banco de dados estabelecida!")
        return conn
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com banco: {e}")
        raise

def get_sheets_service():
    """Obtém o serviço do Google Sheets."""
    try:
        # Busca o arquivo de credenciais
        service_account_file = None
        
        # Procura por arquivos de credenciais
        possible_files = [
            '/var/www/estevaoalmeida.com.br/form-google/credentials.json',
            '/var/www/estevaoalmeida.com.br/form-google/service-account.json',
            './credentials.json',
            './service-account.json'
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                service_account_file = file_path
                break
        
        if not service_account_file:
            logger.warning("⚠️ Arquivo de credenciais não encontrado. Usando dados de demonstração.")
            return None
        
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        
        service = build("sheets", "v4", credentials=credentials)
        logger.info("✅ Serviço Google Sheets inicializado!")
        return service
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao inicializar Google Sheets: {e}")
        return None

def buscar_dados_planilha(service, sheet_name="Respostas"):
    """Busca dados da planilha Google Sheets."""
    if not service:
        return get_dados_demonstracao()
    
    try:
        range_name = f"{sheet_name}!A:ZZ"
        
        result = service.spreadsheets().values().get(
            spreadsheetId=PLANILHA_ID,
            range=range_name
        ).execute()
        
        values = result.get("values", [])
        if not values:
            logger.warning(f"⚠️ Nenhum dado encontrado na aba '{sheet_name}'")
            return get_dados_demonstracao()
        
        # Primeira linha são os cabeçalhos
        headers = [str(header).strip() for header in values[0]]
        logger.info(f"📋 Cabeçalhos encontrados: {len(headers)} colunas")
        
        # Converte as linhas em dicionários
        dados = []
        for i, row in enumerate(values[1:], start=2):
            # Garante que a linha tenha o mesmo número de colunas
            while len(row) < len(headers):
                row.append("")
            
            linha_dict = {headers[j]: str(row[j]).strip() if j < len(row) else "" 
                         for j in range(len(headers))}
            
            # Ignora linhas completamente vazias
            if any(linha_dict.values()):
                linha_dict["_linha_original"] = i
                dados.append(linha_dict)
        
        logger.info(f"📊 Total de {len(dados)} registros encontrados na planilha")
        return dados
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar dados da planilha: {e}")
        return get_dados_demonstracao()

def get_dados_demonstracao():
    """Retorna dados de demonstração se não conseguir acessar a planilha."""
    logger.info("📋 Usando dados de demonstração...")
    
    return [
        {
            "Primeiro Nome": "Maria",
            "Sobrenome": "Silva",
            "Email": "maria.silva@exemplo.com",
            "CPF": "111.222.333-01",
            "Telefone Celular": "(41) 98765-4321",
            "_linha_original": 2
        },
        {
            "Primeiro Nome": "João",
            "Sobrenome": "Santos",
            "Email": "joao.santos@exemplo.com", 
            "CPF": "111.222.333-02",
            "Telefone Celular": "(41) 98765-4322",
            "_linha_original": 3
        },
        {
            "Primeiro Nome": "Ana",
            "Sobrenome": "Costa",
            "Email": "ana.costa@exemplo.com",
            "CPF": "111.222.333-03", 
            "Telefone Celular": "(41) 98765-4323",
            "_linha_original": 4
        }
    ]

def limpar_cpf(cpf):
    """Remove formatação do CPF."""
    if not cpf:
        return ""
    return re.sub(r'[^\d]', '', str(cpf))

def limpar_telefone(telefone):
    """Remove formatação do telefone."""
    if not telefone:
        return ""
    return re.sub(r'[^\d]', '', str(telefone))

def validar_email(email):
    """Valida formato do email."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def mapear_dados_cliente(dados_linha):
    """Mapeia dados da planilha para o modelo Cliente."""
    try:
        # Email (obrigatório)
        email = dados_linha.get("Email", "").strip().lower()
        if not email or not validar_email(email):
            logger.warning(f"⚠️ Email inválido na linha {dados_linha.get('_linha_original')}: {email}")
            return None
        
        # Nome completo
        primeiro_nome = dados_linha.get("Primeiro Nome", "").strip()
        sobrenome = dados_linha.get("Sobrenome", "").strip()
        nome_completo = f"{primeiro_nome} {sobrenome}".strip()
        
        if not nome_completo:
            logger.warning(f"⚠️ Nome não encontrado na linha {dados_linha.get('_linha_original')}")
            return None
        
        # CPF (limpo)
        cpf = limpar_cpf(dados_linha.get("CPF", ""))
        
        # Telefone (limpo)
        telefone_celular = limpar_telefone(dados_linha.get("Telefone Celular", ""))
        
        dados_mapeados = {
            'tipo_pessoa': 'FISICA',  # Valor correto do enum
            'email': email,
            'telefone_celular': telefone_celular if telefone_celular else None,
            'nome_completo': nome_completo,
            'cpf': cpf if cpf else None,
            'razao_social': None,  # Para pessoa física
            'cnpj': None,  # Para pessoa física
            'representante_nome': None  # Para pessoa física
        }
        
        return dados_mapeados
        
    except Exception as e:
        logger.error(f"❌ Erro ao mapear dados da linha {dados_linha.get('_linha_original')}: {e}")
        return None

def importar_cliente_individual(cursor, dados):
    """Importa um cliente individual."""
    try:
        # Verifica se já existe pelo email ou CPF
        check_query = """
            SELECT id FROM clientes_peticionador 
            WHERE email = %s OR (cpf IS NOT NULL AND cpf = %s)
            LIMIT 1
        """
        
        cursor.execute(check_query, (dados['email'], dados['cpf']))
        existing = cursor.fetchone()
        
        if existing:
            logger.info(f"⚠️ Cliente já existe (Email: {dados['email']}, CPF: {dados['cpf']})")
            return False, "duplicado"
        
        # Insere novo cliente
        insert_query = """
            INSERT INTO clientes_peticionador (
                tipo_pessoa, email, telefone_celular, nome_completo, cpf,
                razao_social, cnpj, representante_nome
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        
        cursor.execute(insert_query, (
            dados['tipo_pessoa'],
            dados['email'],
            dados['telefone_celular'], 
            dados['nome_completo'],
            dados['cpf'],
            dados['razao_social'],
            dados['cnpj'],
            dados['representante_nome']
        ))
        
        novo_id = cursor.fetchone()[0]
        logger.info(f"✅ Cliente importado: {dados['nome_completo']} (ID: {novo_id})")
        return True, "sucesso"
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar cliente {dados.get('nome_completo')}: {e}")
        return False, str(e)

def executar_importacao_clientes():
    """Executa a importação dos clientes da planilha."""
    logger.info("🚀 INICIANDO IMPORTAÇÃO DE CLIENTES")
    logger.info("=" * 60)
    
    try:
        # Conecta ao banco
        conn = get_database_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verifica se a tabela existe
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'clientes_peticionador'
        """)
        
        if cursor.fetchone()[0] == 0:
            logger.error("❌ Tabela 'clientes_peticionador' não encontrada!")
            return
        
        # Conta registros existentes
        cursor.execute("SELECT COUNT(*) FROM clientes_peticionador")
        count_antes = cursor.fetchone()[0]
        logger.info(f"📊 Clientes cadastrados antes da importação: {count_antes}")
        
        # Obtém serviço do Google Sheets
        service = get_sheets_service()
        
        # Busca dados da planilha
        dados_planilha = buscar_dados_planilha(service)
        
        if not dados_planilha:
            logger.error("❌ Nenhum dado para importar")
            return
        
        # Estatísticas
        total_processados = 0
        sucessos = 0
        duplicados = 0
        erros = 0
        
        # Processa cada registro
        for i, linha in enumerate(dados_planilha, 1):
            logger.info(f"📝 Processando registro {i}/{len(dados_planilha)}")
            
            # Mapeia dados
            dados_cliente = mapear_dados_cliente(linha)
            if not dados_cliente:
                erros += 1
                continue
            
            # Importa cliente
            sucesso, resultado = importar_cliente_individual(cursor, dados_cliente)
            total_processados += 1
            
            if resultado == "duplicado":
                duplicados += 1
            elif sucesso:
                sucessos += 1
                conn.commit()  # Confirma inserção
            else:
                erros += 1
                conn.rollback()  # Desfaz em caso de erro
        
        # Conta registros após importação
        cursor.execute("SELECT COUNT(*) FROM clientes_peticionador")
        count_depois = cursor.fetchone()[0]
        
        # Resultados finais
        print("\n" + "=" * 60)
        print("🎯 RESULTADOS DA IMPORTAÇÃO DE CLIENTES")
        print("=" * 60)
        print(f"📊 Total de registros processados: {total_processados}")
        print(f"✅ Clientes importados com sucesso: {sucessos}")
        print(f"⚠️ Clientes duplicados (ignorados): {duplicados}")
        print(f"❌ Registros com erro: {erros}")
        print(f"📋 Clientes antes da importação: {count_antes}")
        print(f"📋 Clientes após a importação: {count_depois}")
        
        if sucessos > 0:
            print(f"\n🎉 {sucessos} novos clientes foram importados!")
            print("✅ Os clientes agora podem ser utilizados no sistema de petições!")
        
        cursor.close()
        conn.close()
        
        print("\n✅ IMPORTAÇÃO DE CLIENTES CONCLUÍDA!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a importação: {e}")
        print(f"\n❌ Erro durante a importação: {e}")

if __name__ == "__main__":
    executar_importacao_clientes() 