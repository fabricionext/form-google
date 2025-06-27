# Nova Arquitetura - Demonstração de Uso

Este documento demonstra como usar a nova arquitetura implementada para o sistema peticionador.

## 📁 Estrutura Implementada

```
app/
├── config/
│   ├── __init__.py
│   ├── constants.py         ✅ Constantes centralizadas
│   └── settings.py         ✅ Configurações por ambiente
├── models/
│   ├── __init__.py
│   ├── base.py            ✅ Modelo base com CRUD
│   ├── template.py        ✅ Modelo Template completo
│   ├── document.py        ✅ Modelo Document completo  
│   ├── placeholder.py     ✅ Modelo Placeholder completo
│   └── client.py          ✅ Modelo Client completo
├── repositories/
│   ├── __init__.py
│   ├── base.py            ✅ Repository base genérico
│   ├── template_repository.py    ✅ Repository Template
│   ├── document_repository.py    ✅ Repository Document
│   ├── placeholder_repository.py ✅ Repository Placeholder
│   └── client_repository.py      ✅ Repository Client
└── utils/
    ├── __init__.py
    └── exceptions.py       ✅ Exceções customizadas
```

## 🔧 Como Usar

### 1. Configuração

```python
from app.config.settings import get_config
from app.config.constants import DOCUMENT_STATUS_COMPLETED

# Carrega configuração baseada no ambiente
config = get_config('development')  # ou 'production', 'testing'

# Usa constantes centralizadas
if document.status == DOCUMENT_STATUS_COMPLETED:
    print("Documento concluído!")
```

### 2. Modelos

```python
from app.models import Template, Document, Placeholder, Client

# Criar novo template
template = Template(
    name="Suspensão do Direito de Dirigir",
    slug="suspensao-direito-dirigir",
    description="Template para suspensão CNH",
    google_drive_id="1ABC123",
    category="transito"
)
template.save()

# Buscar por slug
template = Template.find_by_slug("suspensao-direito-dirigir")

# Adicionar placeholders
placeholder = Placeholder(
    name="nome_cliente",
    label="Nome Completo",
    type="text",
    category="cliente",
    required=True
)
template.add_placeholder(placeholder)

# Validar dados
data = {"nome_cliente": "João Silva"}
is_valid, errors = template.validate_data(data)
```

### 3. Repositories

```python
from app.repositories import TemplateRepository, DocumentRepository

# Usar repositories para operações complexas
template_repo = TemplateRepository()

# Buscar templates ativos
active_templates = template_repo.find_active()

# Buscar com filtros avançados
marketing_templates = template_repo.find_by_category("marketing")

# Estatísticas
stats = template_repo.get_statistics()
print(f"Templates mais usados: {stats['most_used_template']}")

# Operações de documento
doc_repo = DocumentRepository()

# Documentos pendentes
pending_docs = doc_repo.find_pending_processing()

# Estatísticas de geração
gen_stats = doc_repo.get_generation_statistics(days=30)
print(f"Taxa de sucesso: {gen_stats['success_rate_percentage']}%")
```

### 4. Tratamento de Erros

```python
from app.utils.exceptions import (
    TemplateNotFoundException,
    DocumentGenerationException,
    ValidationException
)

try:
    template = template_repo.find_by_id(999)
    if not template:
        raise TemplateNotFoundException(999)
        
except TemplateNotFoundException as e:
    print(f"Erro: {e.message}")
    print(f"Detalhes: {e.details}")
    
except ValidationException as e:
    print(f"Validação falhou no campo {e.field}: {e.message}")
```

## 🚀 Próximos Passos

### Fase 2: Services (Próxima etapa)

```python
# Estrutura planejada para services
app/services/
├── __init__.py
├── template_service.py     # Lógica de negócio para templates
├── document_service.py     # Geração de documentos
├── placeholder_service.py  # Processamento de placeholders
└── validation_service.py   # Validações complexas
```

### Fase 3: Controllers

```python
# Estrutura planejada para controllers
app/api/controllers/
├── __init__.py
├── base.py                 # Controller base
├── template_controller.py  # Endpoints de templates
├── document_controller.py  # Endpoints de documentos
└── client_controller.py    # Endpoints de clientes
```

### Fase 4: Adapters

```python
# Estrutura planejada para adapters
app/adapters/
├── __init__.py
├── google_drive.py         # Integração Google Drive
├── document_generator.py   # Geração de documentos
└── cache_adapter.py        # Sistema de cache
```

## 📊 Benefícios da Nova Arquitetura

### ✅ Já Implementado

1. **Modelos Robustos**: Validação integrada, métodos utilitários, relacionamentos claros
2. **Repositories Especializados**: Queries otimizadas, métodos de busca específicos
3. **Tratamento de Erros**: Exceções customizadas com contexto detalhado
4. **Configuração Centralizada**: Ambientes separados, constantes organizadas
5. **Separação de Responsabilidades**: Cada camada tem função específica

### 🔄 Migração Incremental

- ✅ **Fase 1 Completa**: Estrutura base, modelos, repositories
- 🔄 **Fase 2**: Services (lógica de negócio)
- ⏳ **Fase 3**: Controllers (orquestração)
- ⏳ **Fase 4**: Adapters (integrações externas)

## 💡 Exemplos Práticos

### Busca Avançada de Templates

```python
template_repo = TemplateRepository()

# Templates mais usados
most_used = template_repo.get_most_used(limit=5)
for item in most_used:
    print(f"{item['template'].name}: {item['usage_count']} usos")

# Busca por tags
legal_templates = template_repo.find_by_tags(["juridico", "legal"])

# Templates com placeholders carregados
template_with_ph = template_repo.find_with_placeholders(template_id)
print(f"Placeholders: {len(template_with_ph.placeholders)}")
```

### Estatísticas de Documentos

```python
doc_repo = DocumentRepository()

# Estatísticas por período
stats = doc_repo.get_generation_statistics(days=7)
print(f"""
Últimos 7 dias:
- Total: {stats['total_documents']}
- Concluídos: {stats['completed_documents']}
- Taxa de sucesso: {stats['success_rate_percentage']}%
- Tempo médio: {stats['average_generation_time_seconds']}s
""")

# Estatísticas diárias
daily_stats = doc_repo.get_daily_statistics(days=7)
for day in daily_stats:
    print(f"{day['date']}: {day['completed']}/{day['total']} ({day['success_rate']}%)")
```

### Gestão de Clientes

```python
client_repo = ClientRepository()

# Busca flexível
clientes_joao = client_repo.search_by_name("João")
clientes_sp = client_repo.find_by_state("SP")

# Validação de duplicatas
if client_repo.check_email_exists("novo@email.com"):
    print("Email já cadastrado!")

# Estatísticas
stats = client_repo.get_statistics()
print(f"PF: {stats['pessoa_fisica_count']}, PJ: {stats['pessoa_juridica_count']}")
```

Esta nova arquitetura fornece uma base sólida e escalável para o sistema peticionador, com separação clara de responsabilidades e facilidade de manutenção.