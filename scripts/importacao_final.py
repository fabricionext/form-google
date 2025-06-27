#!/usr/bin/env python3
"""
Script final de importação completamente independente
Usando configuração direta do PostgreSQL
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import re
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração direta do banco
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/form_google"

def get_database_engine():
    """Cria engine do banco de dados com configuração direta."""
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        # Testa a conexão
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Conexão com banco de dados estabelecida com sucesso!")
        return engine
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com o banco: {e}")
        raise

def verificar_tabela_resposta_form(engine):
    """Verifica se a tabela resposta_form existe e sua estrutura."""
    try:
        with engine.connect() as conn:
            # Verifica se a tabela existe
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'resposta_form'
                );
            """))
            
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                logger.warning("⚠️ Tabela 'resposta_form' não existe!")
                return False
            
            # Lista as colunas da tabela
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'resposta_form' 
                ORDER BY ordinal_position;
            """))
            
            colunas = result.fetchall()
            logger.info(f"✅ Tabela 'resposta_form' encontrada com {len(colunas)} colunas:")
            for col_name, col_type in colunas[:10]:  # Mostra apenas as primeiras 10
                logger.info(f"  - {col_name}: {col_type}")
            
            if len(colunas) > 10:
                logger.info(f"  ... e mais {len(colunas) - 10} colunas")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar tabela: {e}")
        return False

def buscar_dados_planilha_demo():
    """Cria dados de demonstração para teste."""
    dados_demo = []
    
    # Dados simulados baseados na estrutura real encontrada
    for i in range(1, 6):  # 5 registros de teste
        dados_demo.append({
            'primeiro_nome': f'Cliente{i}',
            'sobrenome': f'Teste{i}',
            'email': f'cliente{i}@exemplo.com',
            'cpf': f'12345678{i:03d}',
            'telefone_celular': f'(41) 9999-{i:04d}',
            'logradouro': f'Rua Teste {i}',
            'numero': f'{i}00',
            'bairro': f'Bairro {i}',
            'cidade': 'Curitiba',
            'uf_endereco': 'PR',
            'cep': f'8000{i}-000',
            'data_nascimento': f'1990-0{min(i, 9)}-01',
            'nacionalidade': 'Brasileira',
            'estado_civil': 'Solteiro',
            'profissao': 'Teste',
            'rg': f'123456{i:03d}',
            'estado_emissor_rg': 'PR',
            'cnh': f'1234567{i:04d}'
        })
    
    logger.info(f"📋 Criados {len(dados_demo)} registros de demonstração")
    return dados_demo

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

def importar_registro_individual(conn, dados):
    """Importa um registro individual na tabela resposta_form."""
    try:
        # Limpa e prepara os dados
        cpf_limpo = limpar_cpf(dados.get('cpf', ''))
        telefone_limpo = limpar_telefone(dados.get('telefone_celular', ''))
        
        # Verifica se já existe pelo CPF ou email
        check_query = text("""
            SELECT id FROM resposta_form 
            WHERE cpf = :cpf OR email = :email
            LIMIT 1
        """)
        
        existing = conn.execute(check_query, {
            'cpf': cpf_limpo,
            'email': dados.get('email', '').lower()
        }).fetchone()
        
        if existing:
            logger.info(f"⚠️ Registro já existe (CPF: {cpf_limpo}, Email: {dados.get('email')})")
            return False, "duplicado"
        
        # Insere novo registro
        insert_query = text("""
            INSERT INTO resposta_form (
                primeiro_nome, sobrenome, email, cpf, telefone_celular,
                logradouro, numero, bairro, cidade, uf_endereco, cep,
                data_nascimento, nacionalidade, estado_civil, profissao,
                rg, estado_emissor_rg, cnh, created_at
            ) VALUES (
                :primeiro_nome, :sobrenome, :email, :cpf, :telefone_celular,
                :logradouro, :numero, :bairro, :cidade, :uf_endereco, :cep,
                :data_nascimento, :nacionalidade, :estado_civil, :profissao,
                :rg, :estado_emissor_rg, :cnh, NOW()
            ) RETURNING id
        """)
        
        result = conn.execute(insert_query, {
            'primeiro_nome': dados.get('primeiro_nome', ''),
            'sobrenome': dados.get('sobrenome', ''),
            'email': dados.get('email', '').lower(),
            'cpf': cpf_limpo,
            'telefone_celular': telefone_limpo,
            'logradouro': dados.get('logradouro', ''),
            'numero': dados.get('numero', ''),
            'bairro': dados.get('bairro', ''),
            'cidade': dados.get('cidade', ''),
            'uf_endereco': dados.get('uf_endereco', ''),
            'cep': dados.get('cep', ''),
            'data_nascimento': dados.get('data_nascimento'),
            'nacionalidade': dados.get('nacionalidade', ''),
            'estado_civil': dados.get('estado_civil', ''),
            'profissao': dados.get('profissao', ''),
            'rg': dados.get('rg', ''),
            'estado_emissor_rg': dados.get('estado_emissor_rg', ''),
            'cnh': dados.get('cnh', '')
        })
        
        novo_id = result.fetchone()[0]
        logger.info(f"✅ Registro inserido com ID: {novo_id}")
        return True, "sucesso"
        
    except Exception as e:
        logger.error(f"❌ Erro ao inserir registro: {e}")
        return False, str(e)

def executar_importacao_final():
    """Executa a importação final dos dados."""
    logger.info("🚀 INICIANDO IMPORTAÇÃO FINAL DOS DADOS")
    logger.info("=" * 60)
    
    try:
        # Conecta ao banco
        engine = get_database_engine()
        
        # Verifica a tabela
        if not verificar_tabela_resposta_form(engine):
            logger.error("❌ Tabela não encontrada. Parando execução.")
            return
        
        # Para demonstração, vamos usar dados simulados
        logger.info("📋 Usando dados de demonstração...")
        dados_para_importar = buscar_dados_planilha_demo()
        
        # Estatísticas
        total_processados = 0
        sucessos = 0
        duplicados = 0
        erros = 0
        
        # Processa cada registro
        with engine.begin() as conn:  # Usa transação
            for i, linha in enumerate(dados_para_importar, 1):
                logger.info(f"📝 Processando registro {i}/{len(dados_para_importar)}: {linha['primeiro_nome']} {linha['sobrenome']}")
                
                sucesso, resultado = importar_registro_individual(conn, linha)
                total_processados += 1
                
                if resultado == "duplicado":
                    duplicados += 1
                elif sucesso:
                    sucessos += 1
                else:
                    erros += 1
                    logger.error(f"❌ Erro no registro {i}: {resultado}")
        
        # Resultados finais
        print("\n" + "=" * 60)
        print("🎯 RESULTADOS FINAIS DA IMPORTAÇÃO")
        print("=" * 60)
        print(f"📊 Total de registros processados: {total_processados}")
        print(f"✅ Registros importados com sucesso: {sucessos}")
        print(f"⚠️ Registros duplicados (ignorados): {duplicados}")
        print(f"❌ Registros com erro: {erros}")
        
        if sucessos > 0:
            print(f"\n🎉 {sucessos} novos registros foram importados com sucesso!")
            
            # Verifica o total na tabela
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM resposta_form"))
                total_na_tabela = result.fetchone()[0]
                print(f"📋 Total de registros na tabela: {total_na_tabela}")
        
        print("\n✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a importação: {e}")
        print(f"\n❌ Erro durante a importação: {e}")

if __name__ == "__main__":
    executar_importacao_final() 