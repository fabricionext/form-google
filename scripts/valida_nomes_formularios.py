#!/usr/bin/env python3
"""
Script para validar e corrigir nomes de formulários
"""

import os
import sys
import re
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def main():
    # Configurar conexão com banco
    database_url = CONFIG.get('DATABASE_URL', 'postgresql://form_user:form_password@localhost/form_google')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("=== VALIDAÇÃO DE FORMULÁRIOS ===")
        print(f"Data/hora: {datetime.now()}")
        print()
        
        # Buscar todos os formulários
        from app.peticionador.models import FormularioGerado, PeticaoModelo
        
        formularios = session.query(FormularioGerado).all()
        
        if not formularios:
            print("Nenhum formulário encontrado no banco de dados.")
            return
        
        print(f"Encontrados {len(formularios)} formulários:")
        print()
        
        problemas_encontrados = []
        
        for i, form in enumerate(formularios, 1):
            modelo = session.query(PeticaoModelo).get(form.modelo_id)
            modelo_nome = modelo.nome if modelo else "Modelo não encontrado"
            
            print(f"{i}. {form.nome}")
            print(f"   Slug: {form.slug}")
            print(f"   Modelo: {modelo_nome}")
            print(f"   Criado em: {form.criado_em}")
            
            # Validar slug
            slug_esperado = re.sub(r"[^a-zA-Z0-9_-]", "-", form.nome.lower()).strip("-")
            
            # Verificar se o slug atual está correto
            if not form.slug.startswith(slug_esperado):
                print(f"   ⚠️  PROBLEMA: Slug não corresponde ao nome!")
                print(f"      Esperado: {slug_esperado}-[hash]")
                print(f"      Atual: {form.slug}")
                problemas_encontrados.append(form)
            
            # Verificar se o slug é único
            slugs_duplicados = session.query(FormularioGerado).filter_by(slug=form.slug).all()
            if len(slugs_duplicados) > 1:
                print(f"   ⚠️  PROBLEMA: Slug duplicado!")
                problemas_encontrados.append(form)
            
            print()
        
        # Resumo
        print("=== RESUMO ===")
        if problemas_encontrados:
            print(f"⚠️  Encontrados {len(problemas_encontrados)} formulários com problemas:")
            for form in problemas_encontrados:
                print(f"   - {form.nome} (ID: {form.id})")
            
            print()
            resposta = input("Deseja corrigir os problemas encontrados? (s/N): ")
            if resposta.lower() in ['s', 'sim', 'y', 'yes']:
                corrigir_problemas(session, problemas_encontrados)
        else:
            print("✅ Todos os formulários estão corretos!")
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def corrigir_problemas(session, formularios_problema):
    """Corrige problemas encontrados nos formulários"""
    print("\n=== CORRIGINDO PROBLEMAS ===")
    
    import uuid
    
    for form in formularios_problema:
        print(f"Corrigindo formulário: {form.nome}")
        
        # Gerar novo slug baseado no nome
        slug_base = re.sub(r"[^a-zA-Z0-9_-]", "-", form.nome.lower()).strip("-")
        novo_slug = f"{slug_base}-{uuid.uuid4().hex[:8]}"
        
        # Verificar se o novo slug já existe
        while session.query(FormularioGerado).filter_by(slug=novo_slug).first():
            novo_slug = f"{slug_base}-{uuid.uuid4().hex[:8]}"
        
        # Atualizar o slug
        slug_antigo = form.slug
        form.slug = novo_slug
        
        try:
            session.commit()
            print(f"   ✅ Slug corrigido: {slug_antigo} → {novo_slug}")
        except Exception as e:
            session.rollback()
            print(f"   ❌ Erro ao corrigir: {e}")
    
    print("\n✅ Correção concluída!")

if __name__ == "__main__":
    main()
