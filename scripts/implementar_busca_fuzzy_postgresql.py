#!/usr/bin/env python3
"""
Script para implementar busca fuzzy com PostgreSQL + pg_trgm
Única melhoria recomendada da análise crítica.

Uso:
    python scripts/implementar_busca_fuzzy_postgresql.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app import create_app
from extensions import db

def criar_extensao_pg_trgm():
    """Criar extensão pg_trgm no PostgreSQL"""
    print("🔧 Criando extensão pg_trgm...")
    
    try:
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        db.session.commit()
        print("✅ Extensão pg_trgm criada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar extensão: {e}")
        db.session.rollback()
        return False
    
    return True

def criar_indices_fuzzy():
    """Criar índices GIN para busca fuzzy"""
    print("📊 Criando índices GIN para busca fuzzy...")
    
    indices = [
        # Clientes
        """
        CREATE INDEX IF NOT EXISTS idx_clientes_nome_gin 
        ON clientes USING GIN (nome_completo gin_trgm_ops);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_clientes_primeiro_nome_gin 
        ON clientes USING GIN (primeiro_nome gin_trgm_ops);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_clientes_sobrenome_gin 
        ON clientes USING GIN (sobrenome gin_trgm_ops);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_clientes_cpf_gin 
        ON clientes USING GIN (cpf gin_trgm_ops);
        """,
        
        # Autoridades de Trânsito
        """
        CREATE INDEX IF NOT EXISTS idx_autoridades_nome_gin 
        ON autoridades_transito USING GIN (nome gin_trgm_ops);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_autoridades_cidade_gin 
        ON autoridades_transito USING GIN (cidade gin_trgm_ops);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_autoridades_estado_gin 
        ON autoridades_transito USING GIN (estado gin_trgm_ops);
        """
    ]
    
    for i, sql in enumerate(indices, 1):
        try:
            db.session.execute(text(sql))
            print(f"✅ Índice {i}/{len(indices)} criado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar índice {i}: {e}")
            db.session.rollback()
            return False
    
    try:
        db.session.commit()
        print("🎉 Todos os índices criados com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao confirmar transação: {e}")
        db.session.rollback()
        return False
    
    return True

def criar_funcoes_busca():
    """Criar funções SQL otimizadas para busca"""
    print("⚙️ Criando funções SQL otimizadas...")
    
    funcoes = [
        # Função para busca de clientes
        """
        CREATE OR REPLACE FUNCTION buscar_clientes_fuzzy(
            p_query TEXT,
            p_limit INTEGER DEFAULT 10,
            p_threshold REAL DEFAULT 0.3
        )
        RETURNS TABLE(
            id INTEGER,
            nome_completo TEXT,
            cpf TEXT,
            score REAL
        )
        LANGUAGE SQL
        STABLE
        AS $$
            SELECT 
                c.id,
                c.nome_completo,
                c.cpf,
                GREATEST(
                    similarity(c.nome_completo, p_query),
                    similarity(c.primeiro_nome || ' ' || c.sobrenome, p_query),
                    similarity(c.cpf, p_query)
                ) as score
            FROM clientes c
            WHERE 
                c.nome_completo % p_query
                OR c.primeiro_nome % p_query  
                OR c.sobrenome % p_query
                OR c.cpf % p_query
                OR similarity(c.nome_completo, p_query) > p_threshold
            ORDER BY score DESC
            LIMIT p_limit;
        $$;
        """,
        
        # Função para busca de autoridades
        """
        CREATE OR REPLACE FUNCTION buscar_autoridades_fuzzy(
            p_query TEXT,
            p_limit INTEGER DEFAULT 10,
            p_threshold REAL DEFAULT 0.3
        )
        RETURNS TABLE(
            id INTEGER,
            nome TEXT,
            cidade TEXT,
            estado TEXT,
            cnpj TEXT,
            score REAL
        )
        LANGUAGE SQL
        STABLE  
        AS $$
            SELECT 
                a.id,
                a.nome,
                a.cidade,
                a.estado,
                a.cnpj,
                GREATEST(
                    similarity(a.nome, p_query),
                    similarity(a.cidade, p_query),
                    similarity(a.estado, p_query)
                ) as score
            FROM autoridades_transito a
            WHERE 
                a.nome % p_query
                OR a.cidade % p_query
                OR a.estado % p_query
                OR similarity(a.nome, p_query) > p_threshold
            ORDER BY score DESC
            LIMIT p_limit;
        $$;
        """
    ]
    
    for i, sql in enumerate(funcoes, 1):
        try:
            db.session.execute(text(sql))
            print(f"✅ Função {i}/{len(funcoes)} criada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar função {i}: {e}")
            db.session.rollback()
            return False
    
    try:
        db.session.commit()
        print("🎉 Todas as funções criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao confirmar transação: {e}")
        db.session.rollback()
        return False
    
    return True

def gerar_codigo_python():
    """Gerar código Python para usar a busca fuzzy"""
    codigo = '''
# ==========================================
# CÓDIGO PYTHON PARA USAR A BUSCA FUZZY
# ==========================================

from sqlalchemy import text
from extensions import db

class SearchServiceFuzzy:
    """Service otimizado para busca fuzzy com PostgreSQL"""
    
    @staticmethod
    def buscar_clientes(query: str, limit: int = 10, threshold: float = 0.3):
        """
        Busca clientes usando fuzzy search otimizado
        
        Args:
            query: Termo de busca
            limit: Máximo de resultados
            threshold: Limite mínimo de similaridade (0.0 a 1.0)
            
        Returns:
            Lista de dicionários com dados dos clientes
        """
        sql = text("""
            SELECT * FROM buscar_clientes_fuzzy(:query, :limit, :threshold)
        """)
        
        result = db.session.execute(sql, {
            'query': query,
            'limit': limit, 
            'threshold': threshold
        })
        
        return [dict(row._mapping) for row in result]
    
    @staticmethod
    def buscar_autoridades(query: str, limit: int = 10, threshold: float = 0.3):
        """
        Busca autoridades usando fuzzy search otimizado
        
        Args:
            query: Termo de busca
            limit: Máximo de resultados
            threshold: Limite mínimo de similaridade (0.0 a 1.0)
            
        Returns:
            Lista de dicionários com dados das autoridades
        """
        sql = text("""
            SELECT * FROM buscar_autoridades_fuzzy(:query, :limit, :threshold)
        """)
        
        result = db.session.execute(sql, {
            'query': query,
            'limit': limit,
            'threshold': threshold
        })
        
        return [dict(row._mapping) for row in result]
'''
    
    with open('search_service_fuzzy.py', 'w', encoding='utf-8') as f:
        f.write(codigo)
    
    print("📄 Código Python gerado em: search_service_fuzzy.py")

def main():
    """Executar todas as etapas da implementação"""
    print("🚀 IMPLEMENTANDO BUSCA FUZZY COM POSTGRESQL + PG_TRGM")
    print("=" * 60)
    
    # Criar aplicação Flask
    app = create_app()
    
    with app.app_context():
        # Etapa 1: Criar extensão
        if not criar_extensao_pg_trgm():
            print("❌ Falha ao criar extensão. Abortando...")
            return False
        
        # Etapa 2: Criar índices
        if not criar_indices_fuzzy():
            print("❌ Falha ao criar índices. Abortando...")
            return False
        
        # Etapa 3: Criar funções SQL
        if not criar_funcoes_busca():
            print("❌ Falha ao criar funções. Abortando...")
            return False
        
        # Etapa 4: Gerar código Python
        gerar_codigo_python()
    
    print("\n🎉 IMPLEMENTAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("📋 Próximos passos:")
    print("  1. Revisar o código gerado em 'search_service_fuzzy.py'")
    print("  2. Integrar as novas rotas no seu aplicativo")
    print("  3. Testar a performance com dados reais")
    print("  4. Monitorar os logs de performance")
    
    return True

if __name__ == '__main__':
    main() 