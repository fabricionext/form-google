#!/usr/bin/env python3
"""
Script para executar a importação automaticamente com configuração correta do banco
"""

import sys
import os

# Adiciona o diretório do projeto ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configura as variáveis de ambiente antes de importar
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASSWORD"] = "postgres"
os.environ["DB_PASS"] = "postgres"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "form_google"
os.environ["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/form_google"

from import_planilha_especifica import (
    get_sheets_service, 
    buscar_dados_planilha, 
    importar_para_resposta_form,  # Mudança aqui - usar RespostaForm
    logger
)

def executar_importacao_automatica():
    """Executa a importação automaticamente para demonstração."""
    try:
        logger.info("=== EXECUTANDO IMPORTAÇÃO AUTOMÁTICA ===")
        logger.info("Configuração: Aba 'Respostas' -> Tabela 'RespostaForm'")
        
        # Obtém serviço do Google Sheets
        service = get_sheets_service()
        
        # Busca dados da aba Respostas
        logger.info("Buscando dados da aba 'Respostas'...")
        dados = buscar_dados_planilha(service, "Respostas")
        
        if not dados:
            logger.error("Nenhum dado encontrado para importar")
            return
        
        logger.info(f"Total de {len(dados)} linhas encontradas")
        
        # Mostra amostra dos primeiros registros
        logger.info("=== AMOSTRA DOS DADOS ENCONTRADOS ===")
        for i, linha in enumerate(dados[:3], 1):
            nome = f"{linha.get('Primeiro Nome', '')} {linha.get('Sobrenome', '')}".strip()
            email = linha.get('Email', '')
            cpf = linha.get('CPF', '')
            logger.info(f"  {i}. Nome: {nome}, Email: {email}, CPF: {cpf}")
        
        if len(dados) > 3:
            logger.info(f"  ... e mais {len(dados) - 3} registros")
        
        # Executa importação para tabela RespostaForm
        logger.info("=== IMPORTANDO PARA TABELA RESPOSTAFORM ===")
        stats = importar_para_resposta_form(dados)
        
        # Mostra resultados
        print("\n" + "="*60)
        print("🎯 RESULTADOS DA IMPORTAÇÃO")
        print("="*60)
        print(f"📊 Total de registros processados: {stats['total']}")
        print(f"✅ Registros importados com sucesso: {stats['importados']}")
        print(f"⚠️  Registros duplicados (ignorados): {stats['duplicados']}")
        print(f"❌ Registros com erro: {stats['erros']}")
        
        if stats['importados'] > 0:
            print(f"🎉 {stats['importados']} novos registros foram adicionados ao banco de dados!")
        
        if stats['duplicados'] > 0:
            print(f"ℹ️  {stats['duplicados']} registros foram ignorados por já existirem")
        
        if stats['erros'] > 0:
            print(f"⚠️  {stats['erros']} registros tiveram problemas na importação")
        
        print("\n✅ Importação concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante a importação automática: {e}")
        print(f"❌ Erro durante a importação: {e}")

if __name__ == "__main__":
    executar_importacao_automatica() 