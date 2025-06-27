#!/usr/bin/env python3
"""
Script para adicionar campo data_registro na tabela clientes_peticionador
"""

import psycopg2
from datetime import datetime

# Configuração do banco
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'form_google',
    'user': 'postgres',
    'password': 'postgres'
}

def adicionar_campo_data_registro():
    """Adiciona campo data_registro na tabela clientes_peticionador."""
    try:
        # Conecta ao banco
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        print("🔧 Adicionando campo data_registro na tabela clientes_peticionador...")
        
        # Verifica se o campo já existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'clientes_peticionador' 
            AND column_name = 'data_registro'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("⚠️ Campo data_registro já existe!")
            return
        
        # Adiciona o campo data_registro
        cursor.execute("""
            ALTER TABLE clientes_peticionador 
            ADD COLUMN data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        
        # Atualiza registros existentes com data atual
        cursor.execute("""
            UPDATE clientes_peticionador 
            SET data_registro = CURRENT_TIMESTAMP 
            WHERE data_registro IS NULL
        """)
        
        conn.commit()
        
        print("✅ Campo data_registro adicionado com sucesso!")
        print("📅 Registros existentes foram atualizados com timestamp atual")
        
        # Verifica a estrutura atualizada
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'clientes_peticionador'
            AND column_name = 'data_registro'
        """)
        
        resultado = cursor.fetchone()
        if resultado:
            print(f"📊 Campo criado: {resultado[0]} ({resultado[1]}) - Default: {resultado[3]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao adicionar campo: {e}")

if __name__ == "__main__":
    adicionar_campo_data_registro() 