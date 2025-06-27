#!/usr/bin/env python3
"""Script para testar importação da aplicação."""

try:
    print("Tentando importar application...")
    from application import app
    print("SUCCESS: Aplicacao carregada com sucesso!")
    print(f"Configuracao: {app.config.get('ENV', 'unknown')}")
    print(f"Debug: {app.config.get('DEBUG', False)}")
    
    # Testar se as novas rotas estão registradas
    for rule in app.url_map.iter_rules():
        if '/api/' in rule.rule:
            print(f"Rota API: {rule.rule} [{rule.methods}]")
    
except ImportError as e:
    print(f"ERRO DE IMPORTACAO: {e}")
except Exception as e:
    print(f"ERRO GERAL: {e}") 