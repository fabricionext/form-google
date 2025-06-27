#!/usr/bin/env python3
"""
Script para verificar formulários no banco de dados
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.peticionador.models import FormularioGerado, PeticaoModelo
from extensions import db

def main():
    app = create_app()
    
    with app.app_context():
        print("=== VERIFICAÇÃO DE FORMULÁRIOS ===")
        print(f"Data/hora: {datetime.now()}")
        print()
        
        # Verificar o formulário específico que está dando erro
        slug_problema = "suspens-o-do-direito-de-dirigir---vers-o-23-6-827a9e3d"
        form_problema = FormularioGerado.query.filter_by(slug=slug_problema).first()
        
        if form_problema:
            print(f"✅ Formulário encontrado: {form_problema.nome}")
            print(f"   Slug: {form_problema.slug}")
            print(f"   Modelo ID: {form_problema.modelo_id}")
            print(f"   Criado em: {form_problema.criado_em}")
        else:
            print(f"❌ Formulário NÃO encontrado: {slug_problema}")
        
        print()
        
        # Listar todos os formulários disponíveis
        print("=== TODOS OS FORMULÁRIOS DISPONÍVEIS ===")
        formularios = FormularioGerado.query.all()
        
        if not formularios:
            print("Nenhum formulário encontrado no banco de dados.")
        else:
            for i, form in enumerate(formularios, 1):
                modelo = PeticaoModelo.query.get(form.modelo_id)
                modelo_nome = modelo.nome if modelo else "Modelo não encontrado"
                
                print(f"{i}. {form.nome}")
                print(f"   Slug: {form.slug}")
                print(f"   Modelo: {modelo_nome}")
                print(f"   Criado em: {form.criado_em}")
                print()
        
        # Verificar modelos disponíveis
        print("=== MODELOS DISPONÍVEIS ===")
        modelos = PeticaoModelo.query.all()
        
        if not modelos:
            print("Nenhum modelo encontrado no banco de dados.")
        else:
            for i, modelo in enumerate(modelos, 1):
                print(f"{i}. {modelo.nome}")
                print(f"   ID: {modelo.id}")
                print(f"   Ativo: {modelo.ativo}")
                print(f"   Descrição: {modelo.descricao}")
                print()

if __name__ == "__main__":
    main() 