#!/usr/bin/env python3
"""
Debug client data processing
"""
import json

# Simular dados de cliente
cliente_data = {
    "tipo_pessoa": "FISICA",
    "primeiro_nome": "João", 
    "sobrenome": "Silva",
    "cpf": "44455566677",
    "email": "teste.final.completo@gmail.com"
}

print("=== Debug Client Data Processing ===")
print(f"Cliente data: {json.dumps(cliente_data, indent=2)}")

# Simular lógica do DocumentGenerationService
tipo_pessoa = cliente_data.get('tipo_pessoa', 'FISICA')
pessoa_type = 'PF' if tipo_pessoa == 'FISICA' else 'PJ'

print(f"Tipo pessoa: {tipo_pessoa}")
print(f"Pessoa type: {pessoa_type}")

# Gerar nome do cliente
if pessoa_type == 'PF':
    client_name = f"{cliente_data.get('primeiro_nome', '')} {cliente_data.get('sobrenome', '')}".strip()
else:
    client_name = cliente_data.get('razao_social', cliente_data.get('primeiro_nome', ''))

print(f"Client name: '{client_name}'")
print(f"Client name type: {type(client_name)}")
print(f"Client name bool: {bool(client_name)}")

if not client_name:
    print("❌ Client name is empty!")
else:
    print("✅ Client name is valid")