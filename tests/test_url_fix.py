#!/usr/bin/env python3
"""
Teste para verificar se os parâmetros de URL foram corrigidos.
"""

# Standard library imports
import requests

# Local application imports

def test_url_endpoints():
    """Testa os endpoints que foram corrigidos."""
    
    base_url = "https://appform.estevaoalmeida.com.br"
    
    endpoints_to_test = [
        "/peticionador/modelos",
        "/peticionador/modelos/3/novo-formulario", 
        "/peticionador/formularios/transferencia-de-pontos-3-reus-2-autores-junho-2025-8bfb9942",
        "/api/v1/docs/",
    ]
    
    print("🧪 Testando Endpoints Corrigidos")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=10, allow_redirects=False)
            status = response.status_code
            
            # Status codes esperados:
            # 302 = Redirecionamento (provavelmente para login) - OK
            # 200 = Sucesso - OK
            # 404 = Não encontrado - pode ser OK dependendo do caso
            # 500 = Erro interno - PROBLEMA
            
            if status == 500:
                print(f"❌ {endpoint:<60} - ERRO 500 (PROBLEMA!)")
            elif status in [200, 302, 404]:
                print(f"✅ {endpoint:<60} - HTTP {status} (OK)")
            else:
                print(f"⚠️  {endpoint:<60} - HTTP {status} (VERIFICAR)")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint:<60} - ERRO DE CONEXÃO: {e}")
    
    print("\n📋 Legendas:")
    print("✅ OK       - Endpoint funcionando (200, 302, 404)")
    print("❌ PROBLEMA - Erro 500 ou falha de conexão")
    print("⚠️  VERIFICAR - Status code inesperado")
    
    print("\n📝 Nota:")
    print("HTTP 302 é esperado para páginas que requerem login.")
    print("HTTP 404 pode ser normal para alguns endpoints.")
    print("HTTP 500 indica problema que precisa ser corrigido.")


if __name__ == "__main__":
    test_url_endpoints()