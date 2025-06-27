#!/usr/bin/env python3
"""Script para testar rapidamente as importações da nova arquitetura."""

import sys

def test_basic_imports():
    """Testar importações básicas."""
    try:
        print("1. Testando BaseController...")
        from app.api.controllers.base import BaseController
        print("✓ BaseController OK")
        
        print("2. Testando ClientController...")
        from app.api.controllers.client_controller import ClientController
        print("✓ ClientController OK")
        
        print("3. Testando auth routes...")
        from app.api.routes.auth import auth_bp
        print("✓ auth_bp OK")
        
        print("4. Testando clients routes...")
        from app.api.routes.clients import clients_bp
        print("✓ clients_bp OK")
        
        print("5. Testando exceptions...")
        from app.utils.exceptions import NotFoundException, ValidationException
        print("✓ Exceptions OK")
        
        return True
        
    except Exception as e:
        print(f"✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_without_db():
    """Testar criação básica da app sem DB."""
    try:
        print("\n6. Testando criação básica da Flask app...")
        from flask import Flask
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test'
        
        # Tentar registrar os blueprints
        from app.api.routes.auth import auth_bp
        from app.api.routes.clients import clients_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(clients_bp)
        
        print(f"✓ App criada com {len(app.blueprints)} blueprints")
        
        # Mostrar rotas
        print("\nRotas da Nova Arquitetura:")
        for rule in app.url_map.iter_rules():
            if '/api/' in rule.rule:
                print(f"  {rule.rule} [{', '.join(rule.methods)}]")
        
        return True
        
    except Exception as e:
        print(f"✗ ERRO na criação da app: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== TESTE RÁPIDO DA NOVA ARQUITETURA ===\n")
    
    success = test_basic_imports()
    if success:
        success = test_app_without_db()
    
    if success:
        print("\n🎉 SUCESSO: Nova arquitetura carrega corretamente!")
        sys.exit(0)
    else:
        print("\n❌ FALHA: Problemas na importação da nova arquitetura")
        sys.exit(1) 