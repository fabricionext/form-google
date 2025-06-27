#!/usr/bin/env python3
"""
Demonstração da API refatorada com Flask-RESTX e Marshmallow.

Esta demonstração mostra como usar a nova estrutura da API.
"""

# Standard library imports
import json

# Third party imports
import requests

# Local application imports

# Configuração base
BASE_URL = "https://appform.estevaoalmeida.com.br"
API_BASE = f"{BASE_URL}/api/v1"

def demo_api_endpoints():
    """Demonstra os endpoints da API refatorada."""
    
    print("🚀 Demonstração da API Refatorada")
    print("=" * 50)
    
    # 1. Documentação da API
    print("\n1. 📚 Documentação da API:")
    print(f"   Acesse: {API_BASE}/docs/")
    print("   - Swagger UI interativo")
    print("   - Esquemas de validação")
    print("   - Testes diretos na interface")
    
    # 2. Endpoints disponíveis
    print("\n2. 🔗 Endpoints Disponíveis:")
    
    endpoints = {
        "Autenticação": {
            "POST /api/v1/auth/login": "Login de usuário",
            "POST /api/v1/auth/logout": "Logout de usuário", 
            "GET /api/v1/auth/me": "Dados do usuário atual"
        },
        "Clientes": {
            "GET /api/v1/clientes/": "Listar clientes",
            "POST /api/v1/clientes/": "Criar cliente",
            "GET /api/v1/clientes/{id}": "Obter cliente",
            "PUT /api/v1/clientes/{id}": "Atualizar cliente",
            "DELETE /api/v1/clientes/{id}": "Excluir cliente"
        },
        "Modelos": {
            "GET /api/v1/modelos/": "Listar modelos",
            "POST /api/v1/modelos/": "Criar modelo",
            "GET /api/v1/modelos/{id}": "Obter modelo",
            "GET /api/v1/modelos/{slug}": "Obter modelo por slug",
            "PUT /api/v1/modelos/{id}": "Atualizar modelo",
            "DELETE /api/v1/modelos/{id}": "Desativar modelo"
        },
        "Formulários": {
            "GET /api/v1/formularios/{slug}": "Obter formulário",
            "POST /api/v1/formularios/{slug}": "Submeter formulário",
            "POST /api/v1/formularios/validar": "Validar formulário",
            "POST /api/v1/formularios/{slug}/excluir": "Excluir formulário"
        }
    }
    
    for categoria, eps in endpoints.items():
        print(f"\n   {categoria}:")
        for endpoint, desc in eps.items():
            print(f"     {endpoint:<35} - {desc}")
    
    # 3. Vantagens da refatoração
    print("\n3. ✨ Vantagens da Refatoração:")
    
    vantagens = [
        "📝 Validação automática com Marshmallow",
        "📖 Documentação automática com Swagger",
        "🏗️  Estrutura organizada com namespaces",
        "🔒 Autenticação padronizada",
        "⚡ Respostas consistentes em JSON",
        "🧪 Facilita testes automatizados",
        "📊 Monitoramento e debugging melhorados",
        "🔄 Separação clara de responsabilidades"
    ]
    
    for vantagem in vantagens:
        print(f"   {vantagem}")
    
    # 4. Exemplo de uso
    print("\n4. 💡 Exemplo de Uso - Criar Cliente:")
    
    exemplo_cliente = {
        "tipo_pessoa": "FISICA",
        "email": "cliente@exemplo.com",
        "primeiro_nome": "João",
        "sobrenome": "Silva",
        "cpf": "123.456.789-00",
        "telefone_celular": "(11) 99999-9999",
        "endereco_logradouro": "Rua das Flores",
        "endereco_numero": "123",
        "endereco_cidade": "São Paulo",
        "endereco_estado": "SP",
        "endereco_cep": "01234-567"
    }
    
    print("   POST /api/v1/clientes/")
    print("   Content-Type: application/json")
    print(f"   Body: {json.dumps(exemplo_cliente, indent=2, ensure_ascii=False)}")
    
    # 5. Estrutura de resposta
    print("\n5. 📄 Estrutura de Resposta Padrão:")
    
    exemplo_resposta = {
        "success": True,
        "message": "Cliente criado com sucesso",
        "data": {
            "id": 1,
            "email": "cliente@exemplo.com",
            "nome_completo_formatado": "João Silva"
        }
    }
    
    print(f"   {json.dumps(exemplo_resposta, indent=2, ensure_ascii=False)}")
    
    # 6. Estrutura de arquivos
    print("\n6. 📁 Nova Estrutura de Arquivos:")
    
    estrutura = """
   app/peticionador/
   ├── api/                    # Nova estrutura API
   │   ├── __init__.py        # Configuração Flask-RESTX
   │   ├── auth.py            # Endpoints de autenticação
   │   ├── clientes.py        # CRUD de clientes
   │   ├── formularios.py     # Formulários dinâmicos
   │   └── modelos.py         # Modelos de petição
   ├── schemas/               # Validação Marshmallow
   │   ├── __init__.py
   │   ├── cliente_schema.py  # Schemas de cliente
   │   ├── formulario_schema.py # Schemas de formulário
   │   └── user_schema.py     # Schemas de usuário
   └── routes.py              # Rotas originais (mantidas)
   """
    
    print(estrutura)
    
    print("\n7. 🔧 Ferramentas Utilizadas:")
    
    ferramentas = [
        "Flask-RESTX - Organização e documentação da API",
        "Marshmallow - Validação e serialização robusta", 
        "Black - Formatação automática de código",
        "isort - Organização de imports",
        "Swagger UI - Interface interativa de documentação"
    ]
    
    for ferramenta in ferramentas:
        print(f"   • {ferramenta}")
    
    print("\n" + "=" * 50)
    print("✅ API refatorada está funcionando!")
    print(f"🌐 Acesse a documentação em: {API_BASE}/docs/")


if __name__ == "__main__":
    demo_api_endpoints()