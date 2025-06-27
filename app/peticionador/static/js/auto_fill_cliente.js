/**
 * Sistema de Preenchimento Automático por CPF e Nome
 * Funcionalidade para buscar e preencher dados do cliente automaticamente
 */

class AutoFillCliente {
    constructor() {
        this.isSearching = false;
        this.debounceTimeout = null;
        this.cache = new Map();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Aguardar DOM estar carregado
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        console.log('🚀 AutoFillCliente inicializado');
        
        // Configurar busca por CPF
        this.setupCPFSearch();
        
        // Configurar busca por nome
        this.setupNameSearch();
        
        // Adicionar botões de busca
        this.addSearchButtons();
    }

    setupCPFSearch() {
        // Procurar campos de CPF
        const cpfFields = this.findFieldsByPattern(['cpf', 'proprietario_cpf', 'autor_1_cpf']);
        
        cpfFields.forEach(field => {
            this.addCPFSearchToField(field);
        });
    }

    setupNameSearch() {
        // Procurar campos de nome
        const nomeFields = this.findFieldsByPattern(['primeiro_nome', 'nome', 'proprietario_nome']);
        const sobrenomeFields = this.findFieldsByPattern(['sobrenome', 'proprietario_sobrenome']);
        
        // Adicionar busca por nome aos campos relevantes
        [...nomeFields, ...sobrenomeFields].forEach(field => {
            this.addNameSearchToField(field);
        });
    }

    addCPFSearchToField(field) {
        const container = this.createSearchContainer(field, 'cpf');
        const button = container.querySelector('.search-button');
        
        button.addEventListener('click', () => {
            this.searchByCPF(field.value, field);
        });

        // Busca automática ao digitar CPF completo
        field.addEventListener('input', (e) => {
            const cpf = e.target.value.replace(/\D/g, '');
            if (cpf.length === 11) {
                clearTimeout(this.debounceTimeout);
                this.debounceTimeout = setTimeout(() => {
                    this.searchByCPF(cpf, field);
                }, 500);
            }
        });
    }

    addNameSearchToField(field) {
        const container = this.createSearchContainer(field, 'name');
        const button = container.querySelector('.search-button');
        
        button.addEventListener('click', () => {
            this.searchByName(field);
        });

        // Busca automática após 3 caracteres
        field.addEventListener('input', (e) => {
            if (e.target.value.length >= 3) {
                clearTimeout(this.debounceTimeout);
                this.debounceTimeout = setTimeout(() => {
                    this.searchByName(field);
                }, 800);
            }
        });
    }

    createSearchContainer(field, type) {
        const container = document.createElement('div');
        container.className = 'input-group';
        
        // Envolver o campo original
        field.parentNode.insertBefore(container, field);
        container.appendChild(field);
        
        // Adicionar botão de busca
        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'input-group-append';
        
        const button = document.createElement('button');
        button.className = 'btn btn-outline-secondary search-button';
        button.type = 'button';
        button.title = type === 'cpf' ? 'Buscar por CPF' : 'Buscar por Nome';
        button.innerHTML = '<i class="fas fa-search"></i>';
        
        buttonGroup.appendChild(button);
        container.appendChild(buttonGroup);
        
        return container;
    }

    async searchByCPF(cpf, triggerField) {
        if (this.isSearching) return;
        
        const cleanCPF = cpf.replace(/\D/g, '');
        if (cleanCPF.length !== 11) {
            this.showToast('CPF deve ter 11 dígitos', 'warning');
            return;
        }

        // Verificar cache
        if (this.cache.has(cleanCPF)) {
            this.fillClientData(this.cache.get(cleanCPF), triggerField);
            return;
        }

        this.isSearching = true;
        this.showSearching(triggerField, true);

        try {
            const response = await fetch(`/peticionador/api/clientes/busca_cpf?cpf=${cleanCPF}`);
            const result = await response.json();

            if (result.success && result.cliente) {
                this.cache.set(cleanCPF, result.cliente);
                this.fillClientData(result.cliente, triggerField);
                this.showToast(`Cliente ${result.cliente.nome_completo} carregado!`, 'success');
            } else {
                this.showToast(result.error || 'Cliente não encontrado', 'warning');
            }
        } catch (error) {
            console.error('Erro na busca por CPF:', error);
            this.showToast('Erro ao buscar cliente', 'error');
        } finally {
            this.isSearching = false;
            this.showSearching(triggerField, false);
        }
    }

    async searchByName(triggerField) {
        if (this.isSearching) return;

        const fieldName = triggerField.name.toLowerCase();
        let searchParams = {};

        // Determinar se é nome ou sobrenome
        if (fieldName.includes('sobrenome')) {
            searchParams.sobrenome = triggerField.value;
        } else {
            searchParams.primeiro_nome = triggerField.value;
        }

        // Tentar pegar sobrenome se estivermos no campo nome
        if (fieldName.includes('nome') && !fieldName.includes('sobrenome')) {
            const sobrenomeField = this.findRelatedField(triggerField, 'sobrenome');
            if (sobrenomeField && sobrenomeField.value) {
                searchParams.sobrenome = sobrenomeField.value;
            }
        }

        if (!searchParams.primeiro_nome && !searchParams.sobrenome) {
            this.showToast('Digite um nome para buscar', 'warning');
            return;
        }

        this.isSearching = true;
        this.showSearching(triggerField, true);

        try {
            const params = new URLSearchParams(searchParams);
            const response = await fetch(`/peticionador/api/clientes/busca_nome?${params}`);
            const result = await response.json();

            if (result.success && result.clientes && result.clientes.length > 0) {
                if (result.clientes.length === 1) {
                    // Apenas um resultado, preencher automaticamente
                    this.fillClientData(result.clientes[0], triggerField);
                    this.showToast(`Cliente ${result.clientes[0].nome_completo} carregado!`, 'success');
                } else {
                    // Múltiplos resultados, mostrar seletor
                    this.showClientSelector(result.clientes, triggerField);
                }
            } else {
                this.showToast(result.error || 'Nenhum cliente encontrado', 'warning');
            }
        } catch (error) {
            console.error('Erro na busca por nome:', error);
            this.showToast('Erro ao buscar cliente', 'error');
        } finally {
            this.isSearching = false;
            this.showSearching(triggerField, false);
        }
    }

    fillClientData(clienteData, triggerField) {
        console.log('Preenchendo dados do cliente:', clienteData);

        // Determinar prefixo do campo (ex: proprietario_, autor_1_, etc.)
        const prefix = this.getFieldPrefix(triggerField);

        // Mapeamento de campos
        const fieldMapping = {
            [`${prefix}primeiro_nome`]: clienteData.primeiro_nome,
            [`${prefix}sobrenome`]: clienteData.sobrenome,
            [`${prefix}nome`]: clienteData.nome_completo,
            [`${prefix}cpf`]: clienteData.cpf,
            [`${prefix}rg`]: clienteData.rg_numero,
            [`${prefix}email`]: clienteData.email,
            [`${prefix}telefone`]: clienteData.telefone_celular || clienteData.telefone_outro,
            [`${prefix}telefone_celular`]: clienteData.telefone_celular,
            [`${prefix}data_nascimento`]: clienteData.data_nascimento,
            [`${prefix}nacionalidade`]: clienteData.nacionalidade,
            [`${prefix}estado_civil`]: clienteData.estado_civil,
            [`${prefix}profissao`]: clienteData.profissao,
            [`${prefix}cnh_numero`]: clienteData.cnh_numero,
            [`${prefix}endereco_logradouro`]: clienteData.endereco_logradouro,
            [`${prefix}endereco_numero`]: clienteData.endereco_numero,
            [`${prefix}endereco_complemento`]: clienteData.endereco_complemento,
            [`${prefix}endereco_bairro`]: clienteData.endereco_bairro,
            [`${prefix}endereco_cidade`]: clienteData.endereco_cidade,
            [`${prefix}endereco_estado`]: clienteData.endereco_estado,
            [`${prefix}endereco_cep`]: clienteData.endereco_cep
        };

        // Preencher campos encontrados
        let preenchidos = 0;
        Object.keys(fieldMapping).forEach(fieldName => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (field && fieldMapping[fieldName]) {
                field.value = fieldMapping[fieldName];
                field.dispatchEvent(new Event('input', { bubbles: true }));
                preenchidos++;
            }
        });

        console.log(`${preenchidos} campos preenchidos automaticamente`);
    }

    showClientSelector(clientes, triggerField) {
        // Criar modal de seleção de cliente
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Selecionar Cliente</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Múltiplos clientes encontrados. Selecione o correto:</p>
                        <div class="list-group">
                            ${clientes.map((cliente, index) => `
                                <button type="button" class="list-group-item list-group-item-action" data-index="${index}">
                                    <strong>${cliente.nome_completo}</strong><br>
                                    <small class="text-muted">CPF: ${cliente.cpf} | Email: ${cliente.email}</small>
                                </button>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Configurar eventos
        modal.querySelectorAll('.list-group-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.fillClientData(clientes[index], triggerField);
                modal.remove();
                this.showToast(`Cliente ${clientes[index].nome_completo} selecionado!`, 'success');
            });
        });

        // Mostrar modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        // Remover modal quando fechado
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    // Utilitários
    findFieldsByPattern(patterns) {
        const fields = [];
        patterns.forEach(pattern => {
            const elements = document.querySelectorAll(`[name*="${pattern}"]`);
            fields.push(...Array.from(elements));
        });
        return fields;
    }

    findRelatedField(triggerField, type) {
        const prefix = this.getFieldPrefix(triggerField);
        return document.querySelector(`[name="${prefix}${type}"]`);
    }

    getFieldPrefix(field) {
        const name = field.name;
        const match = name.match(/^(.+?)(?:primeiro_nome|sobrenome|nome|cpf)$/);
        return match ? match[1] : '';
    }

    showSearching(field, show) {
        const button = field.parentNode.querySelector('.search-button');
        if (button) {
            if (show) {
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                button.disabled = true;
            } else {
                button.innerHTML = '<i class="fas fa-search"></i>';
                button.disabled = false;
            }
        }
    }

    showToast(message, type = 'info') {
        // Criar toast
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} toast-message`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 300px;
            animation: slideIn 0.3s ease;
        `;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'warning' ? 'exclamation-triangle' : 'info'}-circle"></i>
            ${message}
        `;

        document.body.appendChild(toast);

        // Remover após 3 segundos
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// CSS para animações
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .search-button {
        border-left: none !important;
    }
    
    .input-group .form-control:focus {
        border-color: #4e73df;
        box-shadow: 0 0 0 0.2rem rgba(78, 115, 223, 0.25);
    }
`;
document.head.appendChild(style);

// Inicializar quando DOM estiver pronto
window.AutoFillCliente = AutoFillCliente;

// Auto-inicializar
document.addEventListener('DOMContentLoaded', () => {
    window.autoFillCliente = new AutoFillCliente();
});