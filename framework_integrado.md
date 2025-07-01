# 🎯 Framework TDD/QDD Integrado - Sistema de Templates

## 📋 **Mapeamento Estratégico**

| **Nossa Fase**    | **Fase TDD/QDD**           | **Objetivo**                            | **Meta de Cobertura** |
| ----------------- | -------------------------- | --------------------------------------- | --------------------- |
| ✅ **Fase 1**     | ✅ **Fase 3** - MVP        | Base de dados funcionando               | **75%**               |
| 🔄 **Fase 1.5.1** | 🔄 **Fase 4** - Core       | Tabelas auxiliares + testes robustos    | **80%**               |
| 🔄 **Fase 1.5.2** | 🔄 **Fase 4** - Core       | ENUMs e validações + testes de contrato | **80%**               |
| 🔄 **Fase 2**     | 🔄 **Fase 5** - Integração | Template Manager Vue.js + E2E           | **85%**               |
| 🔄 **Fase 3**     | 🔄 **Fase 6** - Hardening  | Processamento assíncrono + performance  | **85%**               |

---

## 🚀 **FASE 1.5.1 - Estruturas Auxiliares + Core Testing**

### **📊 Objetivos da Fase**

```markdown
✅ Adicionar tabelas auxiliares (categories, versions, audit_log)
✅ Implementar framework de testes robusto
✅ Estabelecer pipeline de qualidade
✅ Atingir 80% de cobertura de testes
```

### **🧪 Estratégia TDD/QDD para Fase 1.5.1**

#### **1. Planejamento & Critérios de Aceitação**

```gherkin
# Feature: Template Categories Management
Scenario: Criar categoria de template
  Given que sou um administrador autenticado
  When eu criar uma categoria "Defesas Prévias" com slug "defesas-previas"
  Then a categoria deve ser salva no banco
  And deve aparecer na listagem de categorias
  And deve permitir associação com templates

Scenario: Versionamento automático de templates
  Given que existe um template "Ação Anulatória v1"
  When eu modificar campos do template
  Then uma nova versão deve ser criada automaticamente
  And a versão anterior deve ser preservada
  And o histórico deve ser auditado
```

#### **2. Estrutura de Testes (Bootstrap)**

```bash
# Estrutura de diretórios de teste
tests/
├── unit/                    # Testes unitários (rápidos)
│   ├── models/
│   │   ├── test_template_categories.py
│   │   ├── test_template_versions.py
│   │   └── test_audit_log.py
│   ├── services/
│   └── repositories/
├── integration/            # Testes de integração
│   ├── test_database_migrations.py
│   └── test_api_contracts.py
├── e2e/                   # Testes ponta a ponta
│   └── test_template_flow.py
└── fixtures/              # Dados de teste
    ├── categories.json
    ├── templates.json
    └── audit_logs.json
```

### **📊 Metas de Qualidade - Fase 1.5.1**

```yaml
# .github/workflows/quality-gates.yml
quality_requirements:
  unit_tests:
    coverage_threshold: 80%
    max_execution_time: 30s

  integration_tests:
    coverage_threshold: 70%
    max_execution_time: 2m

  mutation_testing:
    survival_rate: 60%
    tools: [mutmut]

  static_analysis:
    tools: [mypy, ruff, bandit]
    max_violations: 0

  performance:
    api_response_time: <200ms
    database_query_time: <50ms
```

---

## 🎯 **Critérios de Aceitação - Fase 1.5.1**

### **✅ Definition of Done**

```markdown
Para considerar a Fase 1.5.1 CONCLUÍDA, todos os itens devem estar ✅:

📊 **Cobertura de Testes**
├── [✅] Unit tests: ≥ 80%
├── [✅] Integration tests: ≥ 70%  
├── [✅] Mutation testing: ≥ 60% survival rate
└── [✅] E2E tests: Cenários críticos funcionando

🏗️ **Infraestrutura**
├── [✅] Migração aplicada sem erros
├── [✅] Rollback testado e funcionando
├── [✅] Dados existentes preservados
└── [✅] Performance mantida ou melhorada

🔧 **Funcionalidades**
├── [✅] Template Categories CRUD completo
├── [✅] Template Versions funcionando
├── [✅] Audit Log capturando mudanças
└── [✅] APIs documentadas no OpenAPI

🚀 **Pipeline**
├── [✅] CI/CD passando em todas as etapas
├── [✅] Quality gates implementados
├── [✅] Documentação atualizada
└── [✅] Deploy em staging funcionando
```

### **🚫 Critérios de Bloqueio**

```markdown
A fase NÃO pode ser considerada concluída se:

❌ Qualquer teste unitário falhando
❌ Cobertura abaixo de 80%
❌ Migração quebrando dados existentes
❌ Performance degradada > 20%
❌ Vulnerabilidades de segurança detectadas
❌ APIs retornando erros não tratados
```

---

## 🚀 **Próximos Passos Imediatos**

### **1. Implementar Bootstrap de Testes (Hoje)**

```bash
# Instalar ferramentas de teste
pip install pytest pytest-cov pytest-asyncio mutmut bandit mypy

# Criar estrutura de testes
mkdir -p tests/{unit,integration,e2e,fixtures}

# Configurar pytest
echo "[tool:pytest]" > pytest.ini
```
