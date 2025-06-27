#!/usr/bin/env python3
"""
Script para corrigir e sincronizar todos os formulários dinâmicos
Adiciona placeholders de autoridades de trânsito a todos os modelos que não os possuem
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application import app
from extensions import db
from app.peticionador.models import PeticaoModelo, PeticaoPlaceholder, FormularioGerado

def adicionar_placeholders_autoridades():
    """Adiciona placeholders de autoridades de trânsito a todos os modelos"""
    
    # Definir placeholders de autoridades padrão
    placeholders_autoridades = [
        ('orgao_transito_1_nome', 'Órgão de Trânsito 1 - Nome', 'text', 100, False),
        ('orgao_transito_1_cnpj', 'Órgão de Trânsito 1 - CNPJ', 'text', 101, False),
        ('orgao_transito_1_endereco', 'Órgão de Trânsito 1 - Endereço', 'text', 102, False),
        ('orgao_transito_2_nome', 'Órgão de Trânsito 2 - Nome', 'text', 103, False),
        ('orgao_transito_2_cnpj', 'Órgão de Trânsito 2 - CNPJ', 'text', 104, False),
        ('orgao_transito_2_endereco', 'Órgão de Trânsito 2 - Endereço', 'text', 105, False),
        ('orgao_transito_3_nome', 'Órgão de Trânsito 3 - Nome', 'text', 106, False),
        ('orgao_transito_3_cnpj', 'Órgão de Trânsito 3 - CNPJ', 'text', 107, False),
        ('orgao_transito_3_endereco', 'Órgão de Trânsito 3 - Endereço', 'text', 108, False),
    ]
    
    # Buscar todos os modelos
    modelos = PeticaoModelo.query.all()
    print(f"Encontrados {len(modelos)} modelos para processar...")
    
    modelos_atualizados = 0
    placeholders_criados = 0
    
    for modelo in modelos:
        print(f"\nProcessando modelo: {modelo.nome} (ID: {modelo.id})")
        
        # Verificar se já existem placeholders de autoridades
        placeholders_existentes = PeticaoPlaceholder.query.filter_by(
            modelo_id=modelo.id
        ).filter(
            PeticaoPlaceholder.chave.like('orgao_transito_%')
        ).all()
        
        if placeholders_existentes:
            print(f"  - Modelo já possui {len(placeholders_existentes)} placeholders de autoridades")
            continue
        
        # Adicionar placeholders de autoridades
        for chave, label, tipo, ordem, obrigatorio in placeholders_autoridades:
            # Verificar se já existe
            if not PeticaoPlaceholder.query.filter_by(modelo_id=modelo.id, chave=chave).first():
                placeholder = PeticaoPlaceholder(
                    modelo_id=modelo.id,
                    chave=chave,
                    label_form=label,
                    tipo_campo=tipo,
                    ordem=ordem,
                    obrigatorio=obrigatorio
                )
                db.session.add(placeholder)
                placeholders_criados += 1
                print(f"  + Criado placeholder: {chave}")
        
        modelos_atualizados += 1
    
    try:
        db.session.commit()
        print(f"\n✅ Sucesso!")
        print(f"   - {modelos_atualizados} modelos atualizados")
        print(f"   - {placeholders_criados} placeholders criados")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Erro ao salvar: {e}")

def verificar_formularios_dinamicos():
    """Verifica status dos formulários dinâmicos"""
    
    formularios = FormularioGerado.query.all()
    print(f"\n📋 Formulários dinâmicos ativos: {len(formularios)}")
    
    for form in formularios:
        modelo = PeticaoModelo.query.get(form.modelo_id)
        placeholders_count = PeticaoPlaceholder.query.filter_by(modelo_id=form.modelo_id).count()
        
        print(f"  - {form.nome}")
        print(f"    Slug: {form.slug}")
        print(f"    Modelo: {modelo.nome if modelo else 'N/A'}")
        print(f"    Placeholders: {placeholders_count}")
        print()

if __name__ == "__main__":
    print("🔧 Script de Correção de Formulários Dinâmicos")
    print("=" * 50)
    
    with app.app_context():
        # Verificar status atual
        verificar_formularios_dinamicos()
        
        # Aplicar correções
        adicionar_placeholders_autoridades()
        
        print("\n✨ Script concluído!") 