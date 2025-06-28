/* global Sortable, Fuse, interact, bootstrap, Event */

/**
 * Formulário Dinâmico Refatorado
 * Sistema modular e bem organizado para o formulário dinâmico
 */

/**** SafeStorage Fallback ****/
(function () {
  let safeLS;
  try {
    const testKey = '__storage_test__';
    window.localStorage.setItem(testKey, testKey);
    window.localStorage.removeItem(testKey);
    // localStorage funcional
    safeLS = window.localStorage;
  } catch (e) {
    console.warn('⚠️ localStorage indisponível, usando fallback em memória.');
    const memory = {};
    safeLS = {
      getItem: k => (k in memory ? memory[k] : null),
      setItem: (k, v) => (memory[k] = String(v)),
      removeItem: k => delete memory[k],
      key: i => Object.keys(memory)[i] || null,
      clear: () => Object.keys(memory).forEach(k => delete memory[k]),
      get length() {
        return Object.keys(memory).length;
      },
    };
    // Substitui para que código existente continue usando localStorage
    window.localStorage = safeLS;
  }
  window.SafeStorage = safeLS;
})();

class FormularioApp {
  constructor() {
    this.validators = window.FormValidators;
    this.dataChanged = false;
    this.originalFormData = null;
    this.submitting = false;
    this.clientesData = [];
    this.autoridadesData = [];
    this.fuseInstance = null;
    this.authorityFuseInstance = null;
    // Utilitários disponíveis desde o início
    this.utils = this.createUtils();
  }

  init() {
    console.log('🚀 FormulárioApp inicializado com sistema modular');
    this.utils = this.createUtils();
    this.setupDataChangeTracking();
    this.setupUnloadProtection();
    this.setupInteractJS();
    this.loadSearchData();
    this.loadDraft();
    if (this.validators) {
      this.validators.setupFormValidation('#peticao_form');
    }
  }

  // === MÓDULO: RASTREAMENTO DE MUDANÇAS ===
  setupDataChangeTracking() {
    // Capturar estado inicial do formulário
    setTimeout(() => {
      this.captureOriginalState();
    }, 1000);

    // Rastrear mudanças nos campos
    const form = document.getElementById('peticao_form');
    if (form) {
      form.addEventListener('input', () => {
        if (!this.dataChanged && !this._disableChangeTracking) {
          this.dataChanged = true;
          this.showDataChangeIndicator();
        }
      });

      form.addEventListener('change', () => {
        if (!this.dataChanged && !this._disableChangeTracking) {
          this.dataChanged = true;
          this.showDataChangeIndicator();
        }
      });
    }
  }

  captureOriginalState() {
    const form = document.getElementById('peticao_form');
    if (!form) {return;}

    const formData = new FormData(form);
    this.originalFormData = {};

    for (const [key, value] of formData.entries()) {
      if (key !== 'csrf_token') {
        this.originalFormData[key] = value;
      }
    }
  }

  showDataChangeIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'unsaved-indicator';
    indicator.className =
      'position-fixed bg-warning text-dark px-3 py-2 rounded';
    indicator.style.cssText = `
      top: 10px; left: 50%; transform: translateX(-50%);
      z-index: 9999; font-size: 0.875rem;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    `;
    indicator.innerHTML = `
      <i class="fas fa-exclamation-triangle me-2"></i>
      Alterações não salvas
    `;

    const existing = document.getElementById('unsaved-indicator');
    if (existing) {existing.remove();}

    document.body.appendChild(indicator);
  }

  removeDataChangeIndicator() {
    const indicator = document.getElementById('unsaved-indicator');
    if (indicator) {indicator.remove();}
    this.dataChanged = false;
  }

  // === MÓDULO: PROTEÇÃO CONTRA PERDA DE DADOS ===
  setupUnloadProtection() {
    window.addEventListener('beforeunload', event => {
      if (this.dataChanged && !this.submitting) {
        event.preventDefault();
        event.returnValue =
          'Você tem alterações não salvas. Tem certeza que deseja sair?';
        return event.returnValue;
      }
    });
  }

  // === MÓDULO: BUSCA DE CLIENTE ===
  createClientSearch() {
    return {
      cpfBusca: '',
      loading: false,
      encontrado: false,
      erro: false,
      cliente: null,

      async search() {
        if (!this.cpfBusca || this.cpfBusca.length < 11) {
          this.reset();
          return;
        }

        const cpf = this.cpfBusca.replace(/\D/g, '');
        if (cpf.length !== 11) {return;}

        // Validar CPF antes de buscar
        const cpfValidation = window.FormValidators.validaCPF(cpf);
        if (!cpfValidation.valid) {
          this.erro = true;
          this.encontrado = false;
          return;
        }

        this.loading = true;
        this.erro = false;

        try {
          // Busca fuzzy offline primeiro
          if (
            window.formularioApp.fuseInstance &&
            window.formularioApp.clientesData.length > 0
          ) {
            const results = window.formularioApp.fuseInstance.search(cpf);
            if (results.length > 0 && results[0].score < 0.1) {
              this.cliente = results[0].item;
              this.encontrado = true;
              this.loading = false;
              return;
            }
          }

          // Busca online
          const response = await fetch(
            `/peticionador/api/clientes/busca_cpf?cpf=${cpf}`
          );
          const data = await response.json();

          if (data.success) {
            this.cliente = data.cliente;
            this.encontrado = true;
            this.erro = false;
          } else {
            this.erro = true;
            this.encontrado = false;
          }
        } catch (error) {
          console.error('Erro na busca:', error);
          this.erro = true;
          this.encontrado = false;
        } finally {
          this.loading = false;
        }
      },

      reset() {
        this.encontrado = false;
        this.erro = false;
        this.cliente = null;
      },

      get nomeCompleto() {
        if (!this.cliente) {return '';}
        return (
          this.cliente.nome_completo ||
          `${this.cliente.primeiro_nome || ''} ${this.cliente.sobrenome || ''}`.trim() ||
          'Cliente sem nome'
        );
      },
    };
  }

  // === MÓDULO: BUSCA DE AUTORIDADES ===
  createAuthoritySearch() {
    return {
      busca: '',
      selecionada: null,
      sugestoes: [],
      loading: false,

      async search() {
        if (!this.busca || this.busca.length < 2) {
          this.sugestoes = [];
          return;
        }

        this.loading = true;

        try {
          // Busca fuzzy offline primeiro
          if (
            window.formularioApp.authorityFuseInstance &&
            window.formularioApp.autoridadesData.length > 0
          ) {
            const results = window.formularioApp.authorityFuseInstance.search(
              this.busca
            );
            if (results.length > 0) {
              this.sugestoes = results.slice(0, 5).map(r => r.item);
              if (results[0].score < 0.3) {
                this.selecionada = results[0].item;
              }
              this.loading = false;
              return;
            }
          }

          // Busca online
          const response = await fetch(
            `/peticionador/api/autoridades/busca?nome=${encodeURIComponent(this.busca)}&autocomplete=1`
          );
          const data = await response.json();

          if (data.success && data.sugestoes.length > 0) {
            this.sugestoes = data.sugestoes;
            this.selecionada = data.sugestoes[0];
          }
        } catch (error) {
          console.error('Erro na busca de autoridades:', error);
        } finally {
          this.loading = false;
        }
      },

      select(autoridade) {
        this.selecionada = autoridade;
        this.busca = autoridade.nome;
        this.sugestoes = [];
      },
    };
  }

  // === MÓDULO: ESTADO DO FORMULÁRIO ===
  createFormState() {
    return {
      clienteCarregado: false,
      clienteId: '',
      submitting: false,
      saving: false,
      previewLoading: false,
      previewContent: '',

      resetCliente() {
        this.clienteCarregado = false;
        this.clienteId = '';
        window.formularioApp.clientSearch.reset();
        window.formularioApp.clientSearch.cpfBusca = '';
      },

      async submitForm() {
        if (!this.clienteCarregado) {
          window.FormValidators.showToast(
            'Por favor, carregue os dados de um cliente antes de gerar o documento.',
            'warning'
          );
          return;
        }

        // Validar formulário antes de enviar
        const validation = window.FormValidators.validateForm('#peticao_form');
        if (!validation.valid) {
          window.FormValidators.showToast(
            'Por favor, corrija os erros no formulário antes de continuar.',
            'error'
          );
          console.log('Erros encontrados:', validation.errors);
          return;
        }

        this.submitting = true;

        try {
          const formData = new FormData(
            document.getElementById('peticao_form')
          );
          const response = await fetch(window.location.href, {
            method: 'POST',
            body: formData,
          });

          const data = await response.json();

          if (data.success) {
            window.open(data.link, '_blank');
            window.FormValidators.showToast(
              'Documento gerado com sucesso!',
              'success'
            );
            window.formularioApp.removeDataChangeIndicator();
          } else {
            throw new Error(data.error);
          }
        } catch (error) {
          window.FormValidators.showToast(
            'Erro ao gerar documento: ' + error.message,
            'error'
          );
        } finally {
          this.submitting = false;
        }
      },

      async saveDraft() {
        this.saving = true;

        try {
          const formData = new FormData(
            document.getElementById('peticao_form')
          );
          const draftData = {};

          for (const [key, value] of formData.entries()) {
            if (key !== 'csrf_token') {
              draftData[key] = value;
            }
          }

          const slug = window.location.pathname.split('/').pop();
          localStorage.setItem(`draft_${slug}`, JSON.stringify(draftData));
          localStorage.setItem(`draft_${slug}_timestamp`, Date.now());

          window.FormValidators.showToast(
            'Rascunho salvo localmente!',
            'success'
          );
          window.formularioApp.removeDataChangeIndicator();
        } catch (error) {
          window.FormValidators.showToast('Erro ao salvar rascunho', 'error');
        } finally {
          this.saving = false;
        }
      },
    };
  }

  // === MÓDULO: UTILITÁRIOS ===
  createUtils() {
    return {
      fillField(fieldName, value, overwrite = false) {
        const field = document.querySelector(
          `#peticao_form [name="${fieldName}"]`
        );

        if (!field) {
          return false;
        }

        if (value === undefined || value === null) {
          return false;
        }

        const valorLimpo = String(value).trim();

        if (!overwrite && field.value.trim()) {
          return false;
        }

        if (valorLimpo === '' && !field.value.trim()) {
          return false;
        }

        try {
          // Desabilitar máscara temporariamente para evitar conflito
          field._maskDisabled = true;

          field.value = valorLimpo;
          field.setAttribute('value', valorLimpo);
          field.defaultValue = valorLimpo;

          // Usar um timeout para garantir que o valor foi definido antes de
          // reativar máscaras e validações.
          setTimeout(() => {
            // 1. Reativar a máscara
            field._maskDisabled = false;

            // 2. Disparar o evento 'input' para aplicar a máscara (se houver)
            field.dispatchEvent(new Event('input', { bubbles: true }));

            // 3. Disparar o evento 'change' para notificar outros listeners
            field.dispatchEvent(new Event('change', { bubbles: true }));

            // 4. Acionar a validação do campo
            if (window.FormValidators) {
              window.FormValidators.validateField(field);
            }
          }, 50); // Reduzido o tempo, 50ms é suficiente

          return true;
        } catch (error) {
          console.error(`❌ Erro ao preencher campo [${fieldName}]:`, error);
          return false;
        }
      },

      showToast(message, type = 'info') {
        const colors = {
          success: '#28a745',
          error: '#dc3545',
          info: '#17a2b8',
          warning: '#ffc107',
        };

        const toast = document.createElement('div');
        toast.className = 'position-fixed';
        toast.style.cssText = `
          top: 20px; right: 20px; z-index: 9999;
          background: ${colors[type]}; color: white;
          padding: 1rem 1.5rem; border-radius: 0.375rem;
          box-shadow: 0 0.25rem 0.5rem rgba(0,0,0,0.15);
          transform: translateX(100%); transition: transform 0.3s ease;
        `;

        toast.innerHTML = `
          <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
            <span>${message}</span>
          </div>
        `;

        document.body.appendChild(toast);

        setTimeout(() => (toast.style.transform = 'translateX(0)'), 100);
        setTimeout(() => {
          toast.style.transform = 'translateX(100%)';
          setTimeout(() => toast.remove(), 300);
        }, 3000);
      },
    };
  }

  // === CARREGAMENTO DE DADOS ===
  loadClienteData(cliente, autorIndex) {
    // Caso base: Preenchimento geral e do primeiro autor
    if (!autorIndex) {
      console.log('📋 Iniciando preenchimento geral do formulário:', cliente);

      // Capturar o contexto correto para usar dentro da função aninhada
      const self = this;

      // Função robusta para aguardar a inicialização do Alpine.js
      const waitForAlpineAndFill = (retries = 20, delay = 50) => {
        try {
          // Verifica se o Alpine já criou sua instância global
          if (
            window.formularioApp &&
            typeof window.formularioApp === 'object' &&
            !Array.isArray(window.formularioApp)
          ) {
            const alpineApp = window.formularioApp;

            // Proteção extra: garante que as propriedades existem antes de atribuir
            if (alpineApp) {
              alpineApp.clienteCarregado = true;
              alpineApp.clienteId = cliente.id;
              alpineApp.cliente = cliente;
              alpineApp.clienteEncontrado = true;
            }

            console.log('✅ Alpine.js pronto! Estado atualizado.');

            // Desabilitar rastreamento de mudanças temporariamente
            self._disableChangeTracking = true;

            // Preencher data atual uma única vez
            if (!self.utils) {
              // Fallback de segurança para garantir utils disponível
              self.utils = self.createUtils();
            }
            if (
              self.utils &&
              typeof self.utils.fillField === 'function' &&
              self.utils.fillField(
                'data_atual',
                new Date().toISOString().split('T')[0],
                true
              )
            ) {
              console.log('📅 Data atual preenchida.');
            }

            // Delega o preenchimento dos campos do primeiro autor
            self.loadClienteData(cliente, 1);

            // Reabilitar rastreamento após delay para permitir preenchimento completo
            setTimeout(() => {
              self._disableChangeTracking = false;
              // Capturar novo estado como "original" após preenchimento
              self.captureOriginalState();
            }, 2000);
          } else if (retries > 0) {
            // Alpine ainda não está pronto, faz nova tentativa
            setTimeout(() => waitForAlpineAndFill(retries - 1, delay), delay);
          } else {
            console.error(
              '❌ FATAL: A instância do Alpine.js (window.formularioApp) não foi encontrada. O preenchimento automático foi abortado.'
            );
          }
        } catch (e) {
          console.error('Erro ao tentar acessar Alpine.js:', e);
          if (retries > 0) {
            setTimeout(() => waitForAlpineAndFill(retries - 1, delay), delay);
          }
        }
      };

      // Inicia a verificação
      waitForAlpineAndFill();
      return;
    }

    // Preenchimento específico do autor
    console.log(
      `📋 Preenchendo dados do Autor ${autorIndex} com o cliente:`,
      cliente
    );

    const mapeamento = {
      primeiro_nome: `_nome`,
      sobrenome: `_sobrenome`,
      nome_completo: `_nome_completo`,
      cpf: `_cpf`,
      rg: `_rg`,
      cnh_numero: `_cnh`,
      email: `_email`,
      telefone_celular: `_telefone`,
      nacionalidade: `_nacionalidade`,
      profissao: `_profissão`,
      estado_civil: `_estado_civil`,
      rg_uf_emissor: `_estado_emissor_do_rg`,
      endereco_logradouro: `_endereço_logradouro`,
      endereco_numero: `_endereço_numero`,
      endereco_complemento: `_endereço_complemento`,
      endereco_bairro: `_endereço_bairro`,
      endereco_cidade: `_endereço_cidade`,
      endereco_estado: `_endereço_uf`,
      endereco_cep: `_endereço_cep`,
    };

    let camposPreenchidos = 0;
    Object.keys(mapeamento).forEach(clienteKey => {
      const valor = cliente[clienteKey];
      const sufixoCampo = mapeamento[clienteKey];
      const nomeCampo = `autor_${autorIndex}${sufixoCampo}`;

      if (
        valor !== undefined &&
        valor !== null &&
        String(valor).trim() !== ''
      ) {
        if (this.utils.fillField(nomeCampo, valor, true)) {
          camposPreenchidos++;
        }
      }
    });

    this.utils.showToast(
      `Autor ${autorIndex} carregado com ${camposPreenchidos} campos.`,
      'success'
    );
  }

  loadAuthorityData(autoridade, index) {
    const autoridadeMap = {
      nome: autoridade.nome,
      cnpj: autoridade.cnpj,
      logradouro: autoridade.logradouro,
      numero: autoridade.numero,
      cidade: autoridade.cidade,
      estado: autoridade.estado,
      cep: autoridade.cep,
    };

    let preenchidos = 0;
    Object.entries(autoridadeMap).forEach(([campoChave, valor]) => {
      const fieldName = `orgao_transito_${index}_${campoChave}`;
      if (this.utils.fillField(fieldName, valor, true)) {
        preenchidos++;
      }
    });

    const dropZone = document.querySelector(
      `.authority-drop-zone[data-authority-index="${index}"]`
    );
    if (dropZone) {
      dropZone.classList.add('filled');
      dropZone.querySelector('.status-indicator')?.classList.add('filled');
    }

    this.utils.showToast(
      `Autoridade ${index} carregada (${preenchidos} campos)!`,
      'success'
    );
  }

  // === SETUP INTERACT.JS ===
  setupInteractJS() {
    if (typeof interact === 'undefined') {return;}

    interact('.draggable-card').draggable({
      autoScroll: true,
      listeners: {
        start: event => event.target.classList.add('dragging'),
        move: event => {
          const target = event.target;
          const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
          const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
          target.style.transform = `translate(${x}px, ${y}px)`;
          target.setAttribute('data-x', x);
          target.setAttribute('data-y', y);
        },
        end: event => {
          event.target.classList.remove('dragging');
          event.target.style.transform = '';
          event.target.removeAttribute('data-x');
          event.target.removeAttribute('data-y');
        },
      },
    });

    // Drop zones (com bind correto do contexto)
    const self = this; // Preservar contexto

    interact('#drop_placeholder').dropzone({
      accept: '[data-type="cliente"]',
      ondragenter: event => event.target.classList.add('drop-active'),
      ondragleave: event => event.target.classList.remove('drop-active'),
      ondrop: event => {
        event.target.classList.remove('drop-active');
        const clienteData = JSON.parse(event.relatedTarget.dataset.cliente);
        self.loadClienteData(clienteData);
      },
    });

    interact('.autor-drop-zone-wrapper').dropzone({
      accept: '[data-type="cliente"]',
      ondrop: event => {
        const clienteData = JSON.parse(event.relatedTarget.dataset.cliente);
        const autorIndex = event.target.dataset.autorIndex;
        self.loadClienteData(clienteData, autorIndex);
        event.target.classList.remove('drop-active', 'drop-target');
      },
      ondragenter: event =>
        event.target.classList.add('drop-active', 'drop-target'),
      ondragleave: event =>
        event.target.classList.remove('drop-active', 'drop-target'),
    });

    interact('.authority-drop-zone').dropzone({
      accept: '[data-type="autoridade"]',
      ondragenter: event => event.target.classList.add('drop-target'),
      ondragleave: event => event.target.classList.remove('drop-target'),
      ondrop: event => {
        event.target.classList.remove('drop-target');
        const authorityData = JSON.parse(
          event.relatedTarget.dataset.autoridade
        );
        const authorityIndex = event.target.dataset.authorityIndex;
        self.loadAuthorityData(authorityData, authorityIndex);
      },
    });
  }

  // === BUSCA FUZZY E CARREGAMENTO DE DADOS ===
  async loadSearchData() {
    try {
      // Carregar clientes
      const clientesResponse = await fetch('/peticionador/api/clientes/todos');
      const clientesData = await clientesResponse.json();

      if (clientesData.success) {
        this.clientesData = clientesData.clientes;
        this.setupFuseSearch();
        console.log(
          `✅ ${clientesData.total} clientes carregados para busca offline`
        );
      }

      // Carregar autoridades
      const autoridadesResponse = await fetch(
        '/peticionador/api/autoridades/todas'
      );
      const autoridadesData = await autoridadesResponse.json();

      if (autoridadesData.success) {
        this.autoridadesData = autoridadesData.autoridades;
        this.setupAuthorityFuseSearch();
        console.log(
          `✅ ${autoridadesData.total} autoridades carregadas para busca offline`
        );
      }
    } catch (error) {
      console.warn('⚠️ Busca offline não disponível:', error.message);
    }
  }

  setupFuseSearch() {
    if (this.clientesData.length === 0 || typeof Fuse === 'undefined') {return;}

    const options = {
      keys: [
        { name: 'primeiro_nome', weight: 0.3 },
        { name: 'sobrenome', weight: 0.3 },
        { name: 'nome_completo', weight: 0.4 },
        { name: 'cpf', weight: 0.6 },
        { name: 'email', weight: 0.2 },
      ],
      threshold: 0.4,
      includeScore: true,
    };

    this.fuseInstance = new Fuse(this.clientesData, options);
  }

  setupAuthorityFuseSearch() {
    if (this.autoridadesData.length === 0 || typeof Fuse === 'undefined')
      {return;}

    const options = {
      keys: [
        { name: 'nome', weight: 0.6 },
        { name: 'cidade', weight: 0.2 },
        { name: 'estado', weight: 0.1 },
      ],
      threshold: 0.4,
      includeScore: true,
    };

    this.authorityFuseInstance = new Fuse(this.autoridadesData, options);
  }

  // === LIMPEZA E CARREGAMENTO DE RASCUNHO ===
  cleanCorruptedDrafts() {
    try {
      const keysToRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('draft_')) {
          if (key.endsWith('_timestamp')) {
            const timestamp = localStorage.getItem(key);
            if (!timestamp || isNaN(parseInt(timestamp))) {
              keysToRemove.push(key);
              keysToRemove.push(key.replace('_timestamp', ''));
            }
          }
        }
      }

      keysToRemove.forEach(key => {
        console.log(`🧹 Removendo rascunho corrompido: ${key}`);
        localStorage.removeItem(key);
      });

      if (keysToRemove.length > 0) {
        console.log(
          `✅ ${keysToRemove.length} rascunhos corrompidos removidos`
        );
      }
    } catch (error) {
      console.error('❌ Erro ao limpar rascunhos corrompidos:', error);
    }
  }

  loadDraft() {
    // Limpar rascunhos corrompidos primeiro
    this.cleanCorruptedDrafts();
    const slug = window.location.pathname.split('/').pop();
    const savedDraft = localStorage.getItem(`draft_${slug}`);
    const timestamp = localStorage.getItem(`draft_${slug}_timestamp`);

    if (savedDraft && timestamp) {
      try {
        const draftData = JSON.parse(savedDraft);
        const draftTimestamp = Number(timestamp);

        // Verificação robusta do timestamp e da data
        const draftDate = new Date(draftTimestamp);
        if (isNaN(draftTimestamp) || isNaN(draftDate.getTime())) {
          console.warn(
            '⚠️ Timestamp do rascunho inválido ou data corrompida, limpando...'
          );
          localStorage.removeItem(`draft_${slug}`);
          localStorage.removeItem(`draft_${slug}_timestamp`);
          return;
        }

        const timeAgo = Math.round(
          (Date.now() - draftDate.getTime()) / (1000 * 60)
        );

        // Verificar se o cálculo do tempo é válido (redundante, mas seguro)
        if (isNaN(timeAgo) || timeAgo < 0) {
          console.warn('⚠️ Cálculo de tempo do rascunho inválido, limpando...');
          localStorage.removeItem(`draft_${slug}`);
          localStorage.removeItem(`draft_${slug}_timestamp`);
          return;
        }

        // Se o rascunho for muito antigo (mais de 24 horas), limpar automaticamente
        if (timeAgo > 1440) {
          // 24 horas = 1440 minutos
          console.log('🗑️ Rascunho muito antigo, removendo automaticamente...');
          localStorage.removeItem(`draft_${slug}`);
          localStorage.removeItem(`draft_${slug}_timestamp`);
          return;
        }

        const timeDisplay =
          timeAgo < 60
            ? `${timeAgo} minutos`
            : `${Math.round(timeAgo / 60)} horas`;

        const querCarregar = confirm(
          `Encontramos um rascunho salvo há ${timeDisplay}. Deseja carregá-lo?`
        );

        // Sempre remover o rascunho após a pergunta para evitar pop-ups repetidos
        localStorage.removeItem(`draft_${slug}`);
        localStorage.removeItem(`draft_${slug}_timestamp`);

        if (querCarregar) {
          let camposCarregados = 0;
          Object.keys(draftData).forEach(key => {
            if (this.utils && this.utils.fillField(key, draftData[key])) {
              camposCarregados++;
            }
          });
          console.log(
            `✅ Rascunho carregado com sucesso! ${camposCarregados} campos preenchidos.`
          );
        }
      } catch (error) {
        console.error('❌ Erro ao carregar rascunho:', error);
        // Limpar dados corrompidos em caso de erro
        const slug = window.location.pathname.split('/').pop();
        localStorage.removeItem(`draft_${slug}`);
        localStorage.removeItem(`draft_${slug}_timestamp`);
      }
    }
  }

  // === SISTEMA DE ORGANIZAÇÃO DE CAMPOS ===
  initFieldOrganizer() {
    console.log('🔧 Inicializando organizador de campos...');

    // Buscar todas as seções e campos do formulário
    this.buildFieldSections();

    // Carregar ordem personalizada salva
    this.loadCustomFieldOrder();

    // Aplicar ordem personalizada se existir
    this.applyFieldOrder();

    // Inicializar drag-and-drop
    this.initSortable();
  }

  buildFieldSections() {
    const sections = [
      { id: 'dados_pessoais', title: 'Dados Pessoais', fields: [] },
      { id: 'endereco', title: 'Endereço', fields: [] },
      { id: 'documentos', title: 'Documentos', fields: [] },
      { id: 'autoridade', title: 'Autoridade', fields: [] },
      { id: 'outros', title: 'Outros', fields: [] },
    ];

    // Categorizar campos baseado nos labels
    const formFields = document.querySelectorAll(
      '.form-section .form-group, .form-section .form-row .form-group'
    );

    formFields.forEach(group => {
      const label = group.querySelector('label');
      const input = group.querySelector('input, select, textarea');

      if (!label || !input) {return;}

      const fieldData = {
        name: input.name || input.id,
        label: label.textContent.trim(),
        element: group,
      };

      // Categorizar por palavras-chave
      const labelLower = fieldData.label.toLowerCase();

      if (
        labelLower.includes('nome') ||
        labelLower.includes('cpf') ||
        labelLower.includes('rg') ||
        labelLower.includes('nascimento') ||
        labelLower.includes('estado civil') ||
        labelLower.includes('telefone')
      ) {
        sections[0].fields.push(fieldData);
      } else if (
        labelLower.includes('endereço') ||
        labelLower.includes('cep') ||
        labelLower.includes('cidade') ||
        labelLower.includes('bairro') ||
        labelLower.includes('logradouro') ||
        labelLower.includes('estado')
      ) {
        sections[1].fields.push(fieldData);
      } else if (
        labelLower.includes('cnh') ||
        labelLower.includes('carteira') ||
        labelLower.includes('categoria') ||
        labelLower.includes('documento')
      ) {
        sections[2].fields.push(fieldData);
      } else if (
        labelLower.includes('autoridade') ||
        labelLower.includes('orgao') ||
        labelLower.includes('cnpj')
      ) {
        sections[3].fields.push(fieldData);
      } else {
        sections[4].fields.push(fieldData);
      }
    });

    // Remover seções vazias
    this.fieldSections = sections.filter(section => section.fields.length > 0);

    // Salvar ordem original
    this.originalFieldOrder = this.fieldSections.flatMap(section =>
      section.fields.map(field => field.name)
    );

    console.log('📊 Seções de campos construídas:', this.fieldSections);
  }

  toggleOrganizer() {
    this.organizerVisible = !this.organizerVisible;

    if (this.organizerVisible && this.fieldSections.length === 0) {
      this.initFieldOrganizer();
    }
  }

  initSortable() {
    // Usar SortableJS se disponível
    if (typeof Sortable !== 'undefined') {
      this.fieldSections.forEach(section => {
        const container = document.querySelector(
          `[data-section="${section.id}"]`
        );
        if (container) {
          new Sortable(container, {
            group: 'shared',
            animation: 150,
            onEnd: evt => this.handleFieldReorder(evt),
          });
        }
      });
    } else {
      // Fallback manual drag-and-drop
      this.setupManualDragDrop();
    }
  }

  setupManualDragDrop() {
    // Implementação simples de drag-and-drop
    document.addEventListener('mousedown', e => {
      const fieldItem = e.target.closest('.field-item');
      if (!fieldItem) {return;}

      this.isDragging = true;
      fieldItem.classList.add('dragging');

      const mouseMoveHandler = e => {
        // Lógica de arraste simplificada
      };

      const mouseUpHandler = e => {
        this.isDragging = false;
        fieldItem.classList.remove('dragging');
        document.removeEventListener('mousemove', mouseMoveHandler);
        document.removeEventListener('mouseup', mouseUpHandler);
      };

      document.addEventListener('mousemove', mouseMoveHandler);
      document.addEventListener('mouseup', mouseUpHandler);
    });
  }

  handleFieldReorder(evt) {
    console.log('📝 Campo reordenado:', evt);

    // Atualizar ordem dos campos no DOM do formulário
    this.updateFormFieldOrder();

    // Salvar nova ordem
    this.saveCustomFieldOrder();
  }

  updateFormFieldOrder() {
    const formContainer = document.querySelector('.form-section');
    if (!formContainer) {return;}

    // Reordenar elementos do formulário baseado na nova ordem do organizador
    this.fieldSections.forEach(section => {
      section.fields.forEach(field => {
        const element = field.element;
        if (element && element.parentNode) {
          formContainer.appendChild(element);
        }
      });
    });
  }

  saveCustomFieldOrder() {
    const order = this.fieldSections.flatMap(section =>
      section.fields.map(field => ({
        name: field.name,
        section: section.id,
      }))
    );

    const storageKey = `field_order_${this.modelo?.id || 'default'}`;
    this.utils.safeStorage.setItem(storageKey, JSON.stringify(order));

    console.log('💾 Ordem de campos salva:', order);
  }

  loadCustomFieldOrder() {
    const storageKey = `field_order_${this.modelo?.id || 'default'}`;
    const saved = this.utils.safeStorage.getItem(storageKey);

    if (saved) {
      try {
        this.customFieldOrder = JSON.parse(saved);
        console.log('📖 Ordem personalizada carregada:', this.customFieldOrder);
      } catch (e) {
        console.warn('⚠️ Erro ao carregar ordem de campos:', e);
      }
    }
  }

  applyFieldOrder() {
    if (!this.customFieldOrder) {return;}

    // Aplicar ordem personalizada salvs
    console.log('🔄 Aplicando ordem personalizada de campos');
    this.updateFormFieldOrder();
  }

  resetFieldOrder() {
    // Restaurar ordem original
    const storageKey = `field_order_${this.modelo?.id || 'default'}`;
    this.utils.safeStorage.removeItem(storageKey);

    this.customFieldOrder = null;
    this.buildFieldSections();

    console.log('🔄 Ordem de campos restaurada');
  }
}

// Instância global
window.FormularioAppClass = FormularioApp;

// === FUNÇÃO PRINCIPAL PARA ALPINE.JS ===
function formularioApp(modeloData, documentoGerado, linkDocumento) {
  const app = new FormularioApp();

  // Criar objeto Alpine.js
  const alpineInstance = {
    // =================================
    // ESTADO REATIVO DO COMPONENTE
    // =================================

    // --- Dados vindos do Backend ---
    modelo: modeloData,
    documento_gerado: documentoGerado,
    link_documento: linkDocumento,

    // --- Controle de UI ---
    formLoaded: false,
    currentStep: 1,
    organizerVisible: false,
    showPreview: false,
    previewContent: '',
    showClienteModal: false,
    showAutoridadeModal: false,
    showSearchResults: false,

    // --- Estado do Formulário ---
    isValid: false,
    isDirty: false,
    submitting: false,
    saving: false,
    previewLoading: false,
    isGenerating: false,
    generatedDocLink: '',

    // --- Dados do Cliente ---
    cliente: null,
    clienteId: null,
    cpfBusca: '',
    clienteCarregado: false,
    clienteLoading: false,
    clienteEncontrado: false,
    clienteErro: false,
    selectedCliente: null,
    searchResults: [],
    searchQuery: '',

    // --- Dados da Autoridade ---
    autoridadeBusca: '',
    autoridadeSugestoes: [],
    autoridadeLoading: false,
    autoridadeSelecionada: null,
    autoridadeCarregada: false,

    // --- Organização de Campos ---
    fieldSections: [],
    originalFieldOrder: [],
    customFieldOrder: null,
    isDragging: false,

    // =================================
    // MÉTODOS E LÓGICA
    // =================================

    // Inicialização
    init() {
      // Salvar referência global para comunicação entre sistemas (usar o proxy "this")
      window.formularioApp = this;
      app.init();
    },

    // Busca de cliente
    async searchCliente() {
      if (!this.cpfBusca || this.cpfBusca.length < 11) {
        this.resetClienteState();
        return;
      }

      const cpf = this.cpfBusca.replace(/\D/g, '');
      if (cpf.length !== 11) {return;}

      // Validar CPF antes de buscar
      if (window.FormValidators) {
        const cpfValidation = window.FormValidators.validaCPF(cpf);
        if (!cpfValidation.valid) {
          this.clienteErro = true;
          this.clienteEncontrado = false;
          return;
        }
      }

      this.clienteLoading = true;
      this.clienteErro = false;

      try {
        // Busca fuzzy offline primeiro
        if (app.fuseInstance && app.clientesData.length > 0) {
          const results = app.fuseInstance.search(cpf);
          if (results.length > 0 && results[0].score < 0.1) {
            this.cliente = results[0].item;
            this.clienteEncontrado = true;
            this.clienteLoading = false;
            return;
          }
        }

        // Busca online
        const response = await fetch(
          `/peticionador/api/clientes/busca_cpf?cpf=${cpf}`
        );
        const data = await response.json();

        if (data.success) {
          this.cliente = data.cliente;
          this.clienteEncontrado = true;
          this.clienteErro = false;
        } else {
          this.clienteErro = true;
          this.clienteEncontrado = false;
        }
      } catch (error) {
        console.error('Erro na busca:', error);
        this.clienteErro = true;
        this.clienteEncontrado = false;
      } finally {
        this.clienteLoading = false;
      }
    },

    resetClienteState() {
      this.clienteEncontrado = false;
      this.clienteErro = false;
      this.cliente = null;
    },

    // Busca de autoridades
    async searchAutoridades() {
      if (!this.autoridadeBusca || this.autoridadeBusca.length < 2) {
        this.autoridadeSugestoes = [];
        return;
      }

      this.autoridadeLoading = true;

      try {
        // Busca fuzzy offline primeiro
        if (app.authorityFuseInstance && app.autoridadesData.length > 0) {
          const results = app.authorityFuseInstance.search(
            this.autoridadeBusca
          );
          if (results.length > 0) {
            this.autoridadeSugestoes = results.slice(0, 5).map(r => r.item);
            if (results[0].score < 0.3) {
              this.autoridadeSelecionada = results[0].item;
            }
            this.autoridadeLoading = false;
            return;
          }
        }

        // Busca online
        const response = await fetch(
          `/peticionador/api/autoridades/busca?nome=${encodeURIComponent(this.autoridadeBusca)}&autocomplete=1`
        );
        const data = await response.json();

        if (data.success && data.sugestoes.length > 0) {
          this.autoridadeSugestoes = data.sugestoes;
          this.autoridadeSelecionada = data.sugestoes[0];
        }
      } catch (error) {
        console.error('Erro na busca de autoridades:', error);
      } finally {
        this.autoridadeLoading = false;
      }
    },

    selectAutoridade(autoridade) {
      this.autoridadeSelecionada = autoridade;
      this.autoridadeBusca = autoridade.nome;
      this.autoridadeSugestoes = [];
    },

    // Computed properties
    get clienteNomeCompleto() {
      if (!this.cliente) {return '';}
      return (
        this.cliente.nome_completo ||
        `${this.cliente.primeiro_nome || ''} ${this.cliente.sobrenome || ''}`.trim() ||
        'Cliente sem nome'
      );
    },

    // Ações do formulário
    resetCliente() {
      this.clienteCarregado = false;
      this.cliente = null;
      this.clienteId = '';
      this.cpfBusca = '';
      this.resetClienteState();
    },

    resetForm() {
      if (confirm('Tem certeza que deseja limpar todo o formulário?')) {
        location.reload();
      }
    },

    async submitForm() {
      if (!this.clienteCarregado) {
        app.utils.showToast(
          'Por favor, carregue os dados de um cliente antes de gerar o documento.',
          'warning'
        );
        return;
      }

      // Validar formulário antes de enviar (client-side + server-side)
      if (window.FormValidators) {
        const validation = window.FormValidators.validateForm('#peticao_form');
        if (!validation.valid) {
          app.utils.showToast(
            'Por favor, corrija os erros no formulário antes de continuar.',
            'error'
          );
          console.log('Erros encontrados:', validation.errors);
          return;
        }
      }

      // Validação adicional no servidor
      try {
        const formData = new FormData(document.getElementById('peticao_form'));
        const formObj = {};
        const requiredFields = [];

        // Converter FormData para objeto
        for (const [key, value] of formData.entries()) {
          if (key !== 'csrf_token') {
            formObj[key] = value;

            // Detectar campos obrigatórios (pode ser melhorado com metadados do backend)
            const field = document.querySelector(`[name="${key}"]`);
            if (field && field.hasAttribute('required')) {
              requiredFields.push(key);
            }
          }
        }

        const validationResponse = await fetch(
          '/peticionador/api/validate-form',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              form_data: formObj,
              required_fields: requiredFields,
            }),
          }
        );

        const validationResult = await validationResponse.json();

        if (
          !validationResult.success ||
          !validationResult.validation_result.valid
        ) {
          const errors = validationResult.validation_result?.errors || {};
          let errorMessage = 'Erros de validação encontrados:\n';

          Object.entries(errors).forEach(([field, fieldErrors]) => {
            fieldErrors.forEach(error => {
              errorMessage += `• ${field}: ${error}\n`;
            });
          });

          app.utils.showToast(errorMessage.trim(), 'error');
          return;
        }
      } catch (validationError) {
        console.warn('Erro na validação server-side:', validationError);
        // Continuar mesmo se a validação server-side falhar (fallback)
      }

      this.submitting = true;
      app.submitting = true;

      try {
        const formData = new FormData(document.getElementById('peticao_form'));
        const response = await fetch(window.location.href, {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();

        if (data.success) {
          window.open(data.link, '_blank');
          app.utils.showToast('Documento gerado com sucesso!', 'success');
          app.removeDataChangeIndicator();
        } else {
          throw new Error(data.error);
        }
      } catch (error) {
        app.utils.showToast(
          'Erro ao gerar documento: ' + error.message,
          'error'
        );
      } finally {
        this.submitting = false;
        app.submitting = false;
      }
    },

    async saveDraft() {
      this.saving = true;

      try {
        const formData = new FormData(document.getElementById('peticao_form'));
        const draftData = {};

        for (const [key, value] of formData.entries()) {
          if (key !== 'csrf_token') {
            draftData[key] = value;
          }
        }

        const slug = window.location.pathname.split('/').pop();
        localStorage.setItem(`draft_${slug}`, JSON.stringify(draftData));
        localStorage.setItem(`draft_${slug}_timestamp`, Date.now());

        app.utils.showToast('Rascunho salvo localmente!', 'success');
        app.removeDataChangeIndicator();
      } catch (error) {
        app.utils.showToast('Erro ao salvar rascunho', 'error');
      } finally {
        this.saving = false;
      }
    },

    async togglePreview() {
      await this.generatePreview();
      const modal = new bootstrap.Modal(
        document.getElementById('previewModal')
      );
      modal.show();
    },

    async generatePreview() {
      this.previewLoading = true;

      try {
        const formData = new FormData(document.getElementById('peticao_form'));
        const response = await fetch('/peticionador/api/preview-document', {
          method: 'POST',
          body: formData,
        });

        this.previewContent = await response.text();
      } catch (error) {
        this.previewContent = `
          <div class="alert alert-danger">
            <h5>Erro ao gerar preview</h5>
            <p>${error.message}</p>
          </div>
        `;
      } finally {
        this.previewLoading = false;
      }
    },
  };

  return alpineInstance;
}
