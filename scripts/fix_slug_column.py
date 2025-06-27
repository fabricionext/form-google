#!/usr/bin/env python3
"""Script para adicionar coluna slug na tabela peticao_modelos"""

import os
import sys
import re
from sqlalchemy import create_engine, text
from app import create_app

def main():
    app = create_app()
    
    with app.app_context():
        from extensions import db
        
        try:
            # Verificar se a coluna já existe
            result = db.engine.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='peticao_modelos' AND column_name='slug'
            """))
            
            if result.rowcount == 0:
                print("Adicionando coluna slug...")
                
                # Adicionar coluna slug
                db.engine.execute(text("ALTER TABLE peticao_modelos ADD COLUMN slug VARCHAR(150)"))
                
                # Gerar slugs para registros existentes
                print("Gerando slugs para registros existentes...")
                
                modelos = db.engine.execute(text("SELECT id, nome FROM peticao_modelos WHERE slug IS NULL"))
                
                for modelo in modelos:
                    # Criar slug baseado no nome
                    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', modelo.nome.lower())
                    slug = re.sub(r'\s+', '-', slug.strip())
                    slug = f"{slug}-{modelo.id}"
                    
                    db.engine.execute(text("UPDATE peticao_modelos SET slug = :slug WHERE id = :id"), 
                                    {'slug': slug, 'id': modelo.id})
                    print(f"Slug criado: {slug}")
                
                # Tornar coluna NOT NULL e UNIQUE
                db.engine.execute(text("ALTER TABLE peticao_modelos ALTER COLUMN slug SET NOT NULL"))
                db.engine.execute(text("ALTER TABLE peticao_modelos ADD CONSTRAINT uq_peticao_modelos_slug UNIQUE (slug)"))
                
                print("✅ Coluna slug adicionada com sucesso!")
            else:
                print("Coluna slug já existe.")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())