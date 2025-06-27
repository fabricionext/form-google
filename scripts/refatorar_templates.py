#!/usr/bin/env python3
"""
Script para refatorar o sistema de templates e torná-lo mais robusto
"""

import os
import sys
import json
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def main():
    # Configurar conexão com banco
    database_url = CONFIG.get('DATABASE_URL', 'postgresql://form_user:nova_senha_segura@localhost/form_google')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("=== REFATORAÇÃO DO SISTEMA DE TEMPLATES ===")
        print(f"Data/hora: {datetime.now()}")
        print()
        
        # 1. Limpar todos os placeholders existentes do modelo 1
        print("1. Limpando placeholders existentes...")
        session.execute(text("DELETE FROM peticao_placeholders WHERE modelo_id = 1"))
        
        # 2. Criar estrutura robusta de placeholders
        print("2. Criando estrutura robusta de placeholders...")
        
        placeholders = [
            # A. Dados do Cliente (Preenchido Automaticamente)
            {"chave": "primeiro_nome", "label": "Primeiro Nome", "tipo": "string", "ordem": 1, "obrigatorio": True, "categoria": "cliente"},
            {"chave": "sobrenome", "label": "Sobrenome", "tipo": "string", "ordem": 2, "obrigatorio": True, "categoria": "cliente"},
            {"chave": "cpf", "label": "CPF", "tipo": "string", "ordem": 3, "obrigatorio": True, "categoria": "cliente"},
            {"chave": "rg", "label": "RG", "tipo": "string", "ordem": 4, "obrigatorio": False, "categoria": "cliente"},
            {"chave": "estado_emissor_rg", "label": "Estado Emissor do RG", "tipo": "string", "ordem": 5, "obrigatorio": False, "categoria": "cliente"},
            {"chave": "cnh", "label": "CNH", "tipo": "string", "ordem": 6, "obrigatorio": False, "categoria": "cliente"},
            {"chave": "nacionalidade", "label": "Nacionalidade", "tipo": "string", "ordem": 7, "obrigatorio": False, "categoria": "cliente"},
            {"chave": "estado_civil", "label": "Estado Civil", "tipo": "string", "ordem": 8, "obrigatorio": False, "categoria": "cliente"},
            {"chave": "profissao", "label": "Profissão", "tipo": "string", "ordem": 9, "obrigatorio": False, "categoria": "cliente"},
            
            # Endereço
            {"chave": "endereco_logradouro", "label": "Logradouro", "tipo": "string", "ordem": 10, "obrigatorio": False, "categoria": "endereco"},
            {"chave": "endereco_numero", "label": "Número", "tipo": "string", "ordem": 11, "obrigatorio": False, "categoria": "endereco"},
            {"chave": "endereco_complemento", "label": "Complemento", "tipo": "string", "ordem": 12, "obrigatorio": False, "categoria": "endereco"},
            {"chave": "endereco_bairro", "label": "Bairro", "tipo": "string", "ordem": 13, "obrigatorio": False, "categoria": "endereco"},
            {"chave": "endereco_cidade", "label": "Cidade", "tipo": "string", "ordem": 14, "obrigatorio": False, "categoria": "endereco"},
            {"chave": "endereco_estado", "label": "Estado", "tipo": "string", "ordem": 15, "obrigatorio": False, "categoria": "endereco"},
            {"chave": "endereco_cep", "label": "CEP", "tipo": "string", "ordem": 16, "obrigatorio": False, "categoria": "endereco"},
            
            # B. Dados da Infração e Processo
            {"chave": "processo_numero", "label": "Número do Processo", "tipo": "string", "ordem": 17, "obrigatorio": True, "categoria": "infracao"},
            {"chave": "auto_infracao", "label": "Auto de Infração", "tipo": "string", "ordem": 18, "obrigatorio": False, "categoria": "infracao"},
            {"chave": "data_infracao", "label": "Data da Infração", "tipo": "date", "ordem": 19, "obrigatorio": False, "categoria": "infracao"},
            {"chave": "local_infracao", "label": "Local da Infração", "tipo": "string", "ordem": 20, "obrigatorio": False, "categoria": "infracao"},
            
            # C. Detalhes da Penalidade
            {"chave": "total_pontos", "label": "Total de Pontos", "tipo": "string", "ordem": 21, "obrigatorio": False, "categoria": "penalidade"},
            {"chave": "data_notificacao", "label": "Data da Notificação", "tipo": "date", "ordem": 22, "obrigatorio": False, "categoria": "penalidade"},
            {"chave": "prazo_defesa", "label": "Prazo para Defesa", "tipo": "date", "ordem": 23, "obrigatorio": False, "categoria": "penalidade"},
            
            # D. Autoridades e Outros
            {"chave": "autoridade_transito", "label": "Autoridade de Trânsito", "tipo": "select", "ordem": 24, "obrigatorio": True, "categoria": "autoridade", 
             "opcoes": ["DETRAN-SP", "DETRAN-RJ", "DETRAN-MG", "DETRAN-PR", "DETRAN-RS", "DETRAN-SC", "DETRAN-GO", "DETRAN-BA", "DETRAN-CE", "DETRAN-PE"]},
            
            # Campos gerais
            {"chave": "data_atual", "label": "Data Atual", "tipo": "date", "ordem": 25, "obrigatorio": False, "categoria": "geral"},
            {"chave": "observacoes", "label": "Observações", "tipo": "string", "ordem": 26, "obrigatorio": False, "categoria": "geral"},
        ]
        
        # Inserir placeholders
        for ph in placeholders:
            opcoes_json = json.dumps(ph.get("opcoes", [])) if ph.get("opcoes") else None
            session.execute(text("""
                INSERT INTO peticao_placeholders 
                (modelo_id, chave, label_form, tipo_campo, ordem, obrigatorio, opcoes_json) 
                VALUES (:modelo_id, :chave, :label, :tipo, :ordem, :obrigatorio, :opcoes_json)
            """), {
                "modelo_id": 1,
                "chave": ph["chave"],
                "label": ph["label"],
                "tipo": ph["tipo"],
                "ordem": ph["ordem"],
                "obrigatorio": ph["obrigatorio"],
                "opcoes_json": opcoes_json
            })
        
        session.commit()
        print(f"   ✓ {len(placeholders)} placeholders criados")
        
        # 3. Verificar resultado
        print("3. Verificando resultado...")
        result = session.execute(text("SELECT chave, label_form, tipo_campo, ordem FROM peticao_placeholders WHERE modelo_id = 1 ORDER BY ordem"))
        
        print("\nPlaceholders organizados por categoria:")
        categorias = {}
        for row in result:
            chave = row[0]
            label = row[1]
            tipo = row[2]
            ordem = row[3]
            
            # Determinar categoria baseado na chave
            if any(x in chave for x in ["primeiro_nome", "sobrenome", "cpf", "rg", "cnh", "nacionalidade", "estado_civil", "profissao"]):
                cat = "A. Dados do Cliente"
            elif any(x in chave for x in ["endereco"]):
                cat = "A. Dados do Cliente (Endereço)"
            elif any(x in chave for x in ["processo", "auto", "infracao"]):
                cat = "B. Dados da Infração e Processo"
            elif any(x in chave for x in ["pontos", "notificacao", "defesa"]):
                cat = "C. Detalhes da Penalidade"
            elif "autoridade" in chave:
                cat = "D. Autoridades de Trânsito"
            else:
                cat = "E. Outros Campos"
            
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(f"  {ordem:2d}. {label} ({tipo})")
        
        for cat, fields in categorias.items():
            print(f"\n{cat}:")
            for field in fields:
                print(field)
        
        print(f"\n✅ Refatoração concluída com sucesso!")
        print(f"   Total de placeholders: {len(placeholders)}")
        print(f"   Categorias criadas: {len(categorias)}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erro durante a refatoração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main() 