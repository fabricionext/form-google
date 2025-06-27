#!/usr/bin/env python3
"""
Teste simples para a tabela clientes_peticionador
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Configuração do banco
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'form_google',
    'user': 'postgres',
    'password': 'postgres'
}

def testar_tabela_clientes():
    """Testa a tabela clientes_peticionador."""
    try:
        # Conecta ao banco
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ Conexão estabelecida!")
        
        # Lista todas as tabelas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        print(f"\n📋 Tabelas encontradas ({len(tabelas)}):")
        for tabela in tabelas:
            print(f"  - {tabela[0]}")
        
        # Verifica se a tabela clientes_peticionador existe
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'clientes_peticionador'
        """)
        
        existe = cursor.fetchone()[0] > 0
        
        if existe:
            print("\n✅ Tabela 'clientes_peticionador' encontrada!")
            
            # Mostra a estrutura da tabela
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'clientes_peticionador'
                ORDER BY ordinal_position
            """)
            
            colunas = cursor.fetchall()
            print(f"\n📊 Estrutura da tabela ({len(colunas)} colunas):")
            for col in colunas:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"  - {col[0]}: {col[1]} {nullable}{default}")
            
            # Conta registros existentes
            cursor.execute("SELECT COUNT(*) FROM clientes_peticionador")
            count = cursor.fetchone()[0]
            print(f"\n📈 Registros existentes: {count}")
            
            # Testa inserção de um cliente de exemplo
            try:
                print("\n🧪 Testando inserção...")
                cursor.execute("""
                    INSERT INTO clientes_peticionador (
                        tipo_pessoa, email, telefone_celular, nome_completo, cpf
                    ) VALUES (
                        'FISICA', 'teste@exemplo.com', '41999887766', 'Cliente Teste', '12345678901'
                    ) RETURNING id
                """)
                
                novo_id = cursor.fetchone()[0]
                print(f"✅ Teste de inserção bem-sucedido! ID: {novo_id}")
                
                # Remove o registro de teste
                cursor.execute("DELETE FROM clientes_peticionador WHERE id = %s", (novo_id,))
                conn.commit()
                print("🗑️ Registro de teste removido")
                
            except Exception as e:
                print(f"❌ Erro no teste de inserção: {e}")
                conn.rollback()
        else:
            print("❌ Tabela 'clientes_peticionador' NÃO encontrada!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

if __name__ == "__main__":
    print("🔍 TESTE DA TABELA CLIENTES")
    print("=" * 40)
    testar_tabela_clientes()
    print("\n✅ TESTE CONCLUÍDO!") 