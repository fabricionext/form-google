#!/usr/bin/env python3
"""
Teste simples de conexão e importação
"""

import psycopg2
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def testar_conexao():
    """Testa a conexão direta com PostgreSQL."""
    try:
        # Conecta diretamente
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="form_google",
            user="postgres",
            password="postgres"
        )
        
        cursor = conn.cursor()
        
        # Testa a conexão
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        logger.info(f"✅ Conectado ao PostgreSQL: {version[0]}")
        
        # Verifica se a tabela resposta_form existe
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'resposta_form'
        """)
        
        table_count = cursor.fetchone()[0]
        
        if table_count > 0:
            logger.info("✅ Tabela 'resposta_form' encontrada!")
            
            # Conta registros existentes
            cursor.execute("SELECT COUNT(*) FROM resposta_form")
            count = cursor.fetchone()[0]
            logger.info(f"📊 Registros existentes na tabela: {count}")
            
            # Testa inserção de um registro de exemplo
            try:
                cursor.execute("""
                    INSERT INTO resposta_form (
                        primeiro_nome, sobrenome, email, cpf, 
                        telefone_celular, cidade, created_at
                    ) VALUES (
                        'Teste', 'Importacao', 'teste@exemplo.com', '12345678901',
                        '41999887766', 'Curitiba', NOW()
                    ) RETURNING id
                """)
                
                novo_id = cursor.fetchone()[0]
                conn.commit()
                
                logger.info(f"✅ Registro de teste inserido com ID: {novo_id}")
                
                # Remove o registro de teste
                cursor.execute("DELETE FROM resposta_form WHERE id = %s", (novo_id,))
                conn.commit()
                logger.info("🗑️ Registro de teste removido")
                
            except Exception as e:
                logger.error(f"❌ Erro ao inserir registro de teste: {e}")
                conn.rollback()
        else:
            logger.error("❌ Tabela 'resposta_form' não encontrada!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na conexão: {e}")
        return False

def inserir_dados_demo():
    """Insere alguns dados de demonstração."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432", 
            database="form_google",
            user="postgres",
            password="postgres"
        )
        
        cursor = conn.cursor()
        
        # Dados de demonstração
        dados_demo = [
            ("Maria", "Silva", "maria.silva@exemplo.com", "11122233301", "41987654321", "Curitiba", "PR"),
            ("João", "Santos", "joao.santos@exemplo.com", "11122233302", "41987654322", "Londrina", "PR"),
            ("Ana", "Costa", "ana.costa@exemplo.com", "11122233303", "41987654323", "Maringá", "PR"),
        ]
        
        sucessos = 0
        
        for dados in dados_demo:
            try:
                # Verifica se já existe
                cursor.execute("SELECT id FROM resposta_form WHERE cpf = %s OR email = %s", 
                             (dados[3], dados[2]))
                
                if cursor.fetchone():
                    logger.info(f"⚠️ Registro já existe: {dados[0]} {dados[1]}")
                    continue
                
                # Insere novo registro
                cursor.execute("""
                    INSERT INTO resposta_form (
                        primeiro_nome, sobrenome, email, cpf, telefone_celular, 
                        cidade, uf_endereco, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW()) RETURNING id
                """, dados)
                
                novo_id = cursor.fetchone()[0]
                sucessos += 1
                logger.info(f"✅ Inserido: {dados[0]} {dados[1]} (ID: {novo_id})")
                
            except Exception as e:
                logger.error(f"❌ Erro ao inserir {dados[0]} {dados[1]}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🎉 {sucessos} registros inseridos com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro na inserção de dados demo: {e}")

if __name__ == "__main__":
    print("🚀 TESTE DE CONEXÃO E IMPORTAÇÃO")
    print("=" * 50)
    
    if testar_conexao():
        print("\n📝 INSERINDO DADOS DE DEMONSTRAÇÃO")
        print("=" * 50)
        inserir_dados_demo()
    
    print("\n✅ TESTE CONCLUÍDO!") 