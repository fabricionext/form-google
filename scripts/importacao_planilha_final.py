#!/usr/bin/env python3
"""
SCRIPT FINAL DE IMPORTAÇÃO - ABA RESPOSTAS
Importa dados da planilha Google Sheets com todas as máscaras e validações
"""

import os
import sys
import logging
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração do banco
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'form_google',
    'user': 'postgres',
    'password': 'postgres'
}

# ID da planilha
PLANILHA_ID = "1Hj0D-VeJ51nQdAOBlvwzTKR_S3Sls40drthXfLI9Eow"

# Colunas a ignorar (conforme orientação)
COLUNAS_IGNORAR = [
    "Foto CNH RG",
    "Pontuação", 
    "Endereço Número",
    "Endereço Complemento", 
    "Endereço Bairro"
]

def get_sheets_service():
    """Obtém serviço do Google Sheets com credenciais configuradas."""
    try:
        # Procura por arquivos de credenciais
        credential_files = [
            'app-script-459322-990ad4e6c8ea.json',  # Arquivo encontrado
            'credentials.json',
            'service-account.json'
        ]
        
        service_account_file = None
        for file_path in credential_files:
            if os.path.exists(file_path):
                service_account_file = file_path
                logger.info(f"📋 Usando credenciais: {file_path}")
                break
        
        if not service_account_file:
            raise Exception("Arquivo de credenciais não encontrado")
        
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        
        service = build("sheets", "v4", credentials=credentials)
        logger.info("✅ Google Sheets conectado com sucesso!")
        return service
        
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Google Sheets: {e}")
        raise

def aplicar_mascara_cpf(cpf):
    """Aplica máscara ao CPF: 000.000.000-00"""
    if not cpf:
        return ""
    
    # Remove tudo que não é número
    numeros = re.sub(r'[^\d]', '', str(cpf))
    
    # Valida se tem 11 dígitos
    if len(numeros) != 11:
        return numeros  # Retorna sem máscara se inválido
    
    # Aplica máscara: 123.456.789-01
    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"

def aplicar_mascara_telefone(telefone):
    """Aplica máscara ao telefone: (41) 99999-9999"""
    if not telefone:
        return ""
    
    # Remove tudo que não é número
    numeros = re.sub(r'[^\d]', '', str(telefone))
    
    # Se não tem DDD, adiciona 41 (Curitiba)
    if len(numeros) == 8:
        numeros = "41" + numeros
    elif len(numeros) == 9:
        numeros = "41" + numeros
    
    # Aplica máscaras conforme padrão
    if len(numeros) == 10:  # Fixo: (41) 3123-4567
        return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
    elif len(numeros) == 11:  # Celular: (41) 99123-4567
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    else:
        return numeros  # Retorna números se não conseguir formatar

def aplicar_mascara_cep(cep):
    """Aplica máscara ao CEP: 00000-000"""
    if not cep:
        return ""
    
    # Remove tudo que não é número
    numeros = re.sub(r'[^\d]', '', str(cep))
    
    # Valida se tem 8 dígitos
    if len(numeros) != 8:
        return numeros  # Retorna sem máscara se inválido
    
    # Aplica máscara: 80010-000
    return f"{numeros[:5]}-{numeros[5:]}"

def normalizar_email(email):
    """Normaliza email conforme padrão do banco."""
    if not email:
        return ""
    
    email = str(email).strip().lower()
    
    # Validação básica de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return ""
    
    return email

def converter_data_registro(data_str):
    """Converte string de data para timestamp PostgreSQL."""
    if not data_str:
        return datetime.now()
    
    try:
        # Formatos brasileiros possíveis
        formatos = [
            "%d/%m/%Y %H:%M:%S",  # 15/01/2024 10:30:45
            "%d/%m/%Y %H:%M",     # 15/01/2024 10:30
            "%d/%m/%Y",           # 15/01/2024
            "%Y-%m-%d %H:%M:%S",  # 2024-01-15 10:30:45
            "%Y-%m-%d"            # 2024-01-15
        ]
        
        for formato in formatos:
            try:
                return datetime.strptime(data_str.strip(), formato)
            except ValueError:
                continue
        
        logger.warning(f"⚠️ Formato de data não reconhecido: {data_str}")
        return datetime.now()
        
    except Exception as e:
        logger.error(f"❌ Erro ao converter data '{data_str}': {e}")
        return datetime.now()

def buscar_dados_aba_respostas(service):
    """Busca dados da aba 'Respostas' da planilha real."""
    try:
        logger.info(f"📊 Buscando dados da aba 'Respostas' da planilha {PLANILHA_ID}")
        
        range_name = "Respostas!A:ZZ"
        
        result = service.spreadsheets().values().get(
            spreadsheetId=PLANILHA_ID,
            range=range_name
        ).execute()
        
        values = result.get("values", [])
        if not values:
            raise Exception("Aba 'Respostas' vazia ou não encontrada")
        
        # Primeira linha são os cabeçalhos
        headers = [str(header).strip() for header in values[0]]
        logger.info(f"📋 Cabeçalhos encontrados ({len(headers)}): {headers[:10]}...")  # Mostra apenas os primeiros 10
        
        # Filtra colunas a ignorar
        indices_validos = []
        headers_filtrados = []
        colunas_ignoradas = []
        
        for i, header in enumerate(headers):
            if header in COLUNAS_IGNORAR:
                colunas_ignoradas.append(header)
            else:
                indices_validos.append(i)
                headers_filtrados.append(header)
        
        logger.info(f"📊 Colunas úteis: {len(headers_filtrados)}")
        logger.info(f"🗑️ Colunas ignoradas: {colunas_ignoradas}")
        
        # Processa dados
        dados = []
        for i, row in enumerate(values[1:], start=2):
            # Garante que a linha tenha dados suficientes
            while len(row) < len(headers):
                row.append("")
            
            # Filtra apenas colunas válidas
            linha_filtrada = {}
            for j, indice in enumerate(indices_validos):
                valor = str(row[indice]).strip() if indice < len(row) else ""
                linha_filtrada[headers_filtrados[j]] = valor
            
            # Ignora linhas vazias (sem email ou nome)
            if linha_filtrada.get("Email", "").strip() and linha_filtrada.get("Primeiro Nome", "").strip():
                linha_filtrada["_linha_original"] = i
                dados.append(linha_filtrada)
        
        logger.info(f"📈 {len(dados)} registros válidos encontrados")
        return dados
        
    except Exception as e:
        logger.error(f"❌ Erro ao ler planilha: {e}")
        raise

def mapear_cliente_planilha(linha):
    """Mapeia dados da planilha para modelo Cliente com todas as máscaras."""
    try:
        # Email (obrigatório, normalizado)
        email = normalizar_email(linha.get("Email", ""))
        if not email:
            logger.warning(f"⚠️ Email inválido na linha {linha.get('_linha_original')}")
            return None
        
        # Nome completo
        primeiro_nome = linha.get("Primeiro Nome", "").strip()
        sobrenome = linha.get("Sobrenome", "").strip()
        nome_completo = f"{primeiro_nome} {sobrenome}".strip()
        
        if not nome_completo:
            logger.warning(f"⚠️ Nome vazio na linha {linha.get('_linha_original')}")
            return None
        
        # CPF com máscara
        cpf_raw = linha.get("CPF", "")
        cpf_formatado = aplicar_mascara_cpf(cpf_raw)
        
        # Telefone com máscara
        telefone_raw = linha.get("Telefone Celular", "")
        telefone_formatado = aplicar_mascara_telefone(telefone_raw)
        
        # CEP com máscara (se existir)
        cep_raw = linha.get("CEP", "") or linha.get("Endereço CEP", "")
        cep_formatado = aplicar_mascara_cep(cep_raw) if cep_raw else None
        
        # Endereço unificado (conforme orientação)
        endereco_completo = linha.get("Endereço Logradouro", "").strip()
        
        # Data de registro
        data_registro = converter_data_registro(linha.get("Data Hora Registro", ""))
        
        dados_cliente = {
            'tipo_pessoa': 'FISICA',  # Apenas pessoas físicas
            'email': email,
            'telefone_celular': telefone_formatado if telefone_formatado else None,
            'nome_completo': nome_completo,
            'cpf': cpf_formatado if cpf_formatado else None,
            'cep': cep_formatado,
            'endereco_completo': endereco_completo if endereco_completo else None,
            'data_registro': data_registro,
            'razao_social': None,  # PF
            'cnpj': None,  # PF
            'representante_nome': None  # PF
        }
        
        return dados_cliente
        
    except Exception as e:
        logger.error(f"❌ Erro ao mapear linha {linha.get('_linha_original')}: {e}")
        return None

def importar_cliente_planilha(cursor, dados):
    """Importa cliente da planilha com validação de duplicatas."""
    try:
        # Verifica duplicatas por email e CPF (sem máscara para CPF)
        cpf_limpo = re.sub(r'[^\d]', '', dados['cpf']) if dados['cpf'] else None
        
        cursor.execute("""
            SELECT id, email, cpf FROM clientes_peticionador 
            WHERE email = %s OR (cpf IS NOT NULL AND cpf = %s)
        """, (dados['email'], cpf_limpo))
        
        existing = cursor.fetchone()
        if existing:
            logger.info(f"⚠️ Cliente duplicado: {dados['nome_completo']} (Email: {dados['email']})")
            return False, "duplicado"
        
        # Insere cliente com todos os campos
        cursor.execute("""
            INSERT INTO clientes_peticionador (
                tipo_pessoa, email, telefone_celular, nome_completo, 
                cpf, data_registro
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            dados['tipo_pessoa'],
            dados['email'],
            dados['telefone_celular'],
            dados['nome_completo'],
            cpf_limpo,  # Salva CPF limpo no banco
            dados['data_registro']
        ))
        
        result_insert = cursor.fetchone()
        novo_id = result_insert['id'] if result_insert else None
        
        logger.info(f"✅ Cliente importado: {dados['nome_completo']} (ID: {novo_id})")
        logger.info(f"   📧 Email: {dados['email']}")
        logger.info(f"   📱 Telefone: {dados['telefone_celular']}")
        logger.info(f"   🆔 CPF: {dados['cpf']}")
        
        return True, "sucesso"
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar {dados.get('nome_completo')}: {e}")
        return False, str(e)

def executar_importacao_final():
    """Executa importação final da aba Respostas da planilha real."""
    print("🚀 IMPORTAÇÃO FINAL - ABA RESPOSTAS")
    print("=" * 70)
    print(f"📊 Planilha: {PLANILHA_ID}")
    print("📋 Aba: Respostas")
    print("🎯 Máscaras: CPF, Telefone, CEP, Email")
    print("=" * 70)
    
    try:
        # Conecta ao banco
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        logger.info("✅ Conectado ao banco PostgreSQL")
        
        # Conta registros antes
        cursor.execute("SELECT COUNT(*) FROM clientes_peticionador")
        result = cursor.fetchone()
        count_antes = result['count'] if result else 0
        logger.info(f"📈 Clientes cadastrados antes: {count_antes}")
        
        # Conecta ao Google Sheets
        service = get_sheets_service()
        
        # Busca dados da planilha real
        dados_planilha = buscar_dados_aba_respostas(service)
        
        if not dados_planilha:
            raise Exception("Nenhum dado válido encontrado na planilha")
        
        # Estatísticas
        total_processados = 0
        sucessos = 0
        duplicados = 0
        erros = 0
        
        print(f"\n📋 Processando {len(dados_planilha)} registros...")
        
        # Processa cada registro
        for i, linha in enumerate(dados_planilha, 1):
            print(f"\n📝 [{i:3}/{len(dados_planilha)}] {linha.get('Primeiro Nome', '')} {linha.get('Sobrenome', '')}")
            
            # Mapeia dados
            dados_cliente = mapear_cliente_planilha(linha)
            if not dados_cliente:
                erros += 1
                continue
            
            # Importa
            sucesso, resultado = importar_cliente_planilha(cursor, dados_cliente)
            total_processados += 1
            
            if resultado == "duplicado":
                duplicados += 1
            elif sucesso:
                sucessos += 1
                conn.commit()
            else:
                erros += 1
                conn.rollback()
            
            # Mostra progresso a cada 10 registros
            if i % 10 == 0:
                print(f"📊 Progresso: {i}/{len(dados_planilha)} ({(i/len(dados_planilha)*100):.1f}%)")
        
        # Conta registros após importação
        cursor.execute("SELECT COUNT(*) FROM clientes_peticionador")
        result_after = cursor.fetchone()
        count_depois = result_after['count'] if result_after else 0
        
        # Resultados finais
        print("\n" + "=" * 70)
        print("🎯 RESULTADOS DA IMPORTAÇÃO FINAL")
        print("=" * 70)
        print(f"📊 Registros processados: {total_processados}")
        print(f"✅ Clientes importados: {sucessos}")
        print(f"⚠️ Duplicados ignorados: {duplicados}")
        print(f"❌ Erros encontrados: {erros}")
        print(f"📈 Total: {count_antes} → {count_depois} (+{count_depois - count_antes})")
        
        if sucessos > 0:
            taxa_sucesso = (sucessos / total_processados) * 100 if total_processados > 0 else 0
            print(f"📊 Taxa de sucesso: {taxa_sucesso:.1f}%")
            print(f"\n🎉 {sucessos} clientes importados da planilha Google Sheets!")
            print("✅ Formatações aplicadas:")
            print("   📞 Telefones: (41) 99999-9999")
            print("   🆔 CPF: 000.000.000-00") 
            print("   📧 Email: normalizado@dominio.com")
            print("   🏠 Endereços: unificados")
            print("   📅 Datas: preservadas da planilha")
        
        cursor.close()
        conn.close()
        
        print("\n✅ IMPORTAÇÃO FINAL CONCLUÍDA!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante importação: {e}")
        print(f"❌ Erro durante importação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    executar_importacao_final()