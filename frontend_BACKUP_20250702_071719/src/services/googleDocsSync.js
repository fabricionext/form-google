// services/googleDocsSync.js
import ErrorHandler from './errorHandler.js';
import FieldAnalyzer from './fieldAnalyzer.js';
import AsyncProcessor from './asyncProcessor.js';

class GoogleDocsSync {
  constructor(apiClient, config = {}) {
    this.api = apiClient;
    this.syncQueue = [];
    this.isProcessing = false;
    this.socket = null;
    this.reconnectTimer = null;
    this.cache = new Map();
    this.errorHandler = ErrorHandler.getInstance();
    this.fieldAnalyzer = new FieldAnalyzer();
    this.asyncProcessor = new AsyncProcessor({
      batchSize: 3,
      yieldInterval: 16,
      timeout: 10000
    });
    
    // Configuration with defaults
    this.config = {
      maxRetries: 3,
      reconnectInterval: 5000,
      cacheMaxSize: 100,
      cacheTTL: 15 * 60 * 1000, // 15 minutes
      ...config
    };
    
    // Get webhook URL from config instead of environment
    this.webhookUrl = config.webhookUrl || this.getWebhookUrl();
    
    // Bind methods to preserve context
    this.handleRealtimeUpdate = this.handleRealtimeUpdate.bind(this);
    this.handleSocketClose = this.handleSocketClose.bind(this);
    this.handleSocketError = this.handleSocketError.bind(this);
  }

  /**
   * Detecta automaticamente campos variáveis em um documento Google Docs
   * Identifica padrões como {{campo}}, [campo], {campo}, etc.
   */
  async analyzeDocumentFields(documentId) {
    try {
      const response = await this.api.post('/api/admin/google-docs/analyze', {
        document_id: documentId
      })

      const { content, detected_fields, metadata } = response.data

      // Análise avançada de campos
      const fieldAnalysis = this.performAdvancedFieldAnalysis(content, detected_fields)

      return {
        content,
        fields: fieldAnalysis.fields,
        validation_rules: fieldAnalysis.validation_rules,
        field_types: fieldAnalysis.field_types,
        dependencies: fieldAnalysis.dependencies,
        metadata: {
          ...metadata,
          complexity_score: fieldAnalysis.complexity_score,
          estimated_fill_time: fieldAnalysis.estimated_fill_time
        }
      }
    } catch (error) {
      return this.errorHandler.reportError(error, 'GoogleDocsSync', 'analyzeDocumentFields', 'high');
    }
  }

  /**
   * Análise avançada de campos com processamento assíncrono otimizado
   */
  async performAdvancedFieldAnalysis(content, rawFields) {
    const fieldAnalysis = {
      fields: [],
      validation_rules: {},
      field_types: {},
      dependencies: [],
      complexity_score: 0,
      estimated_fill_time: 0
    };

    try {
      // Process fields in batches to avoid UI blocking
      const results = await this.asyncProcessor.processInBatches(
        rawFields,
        async (field) => {
          const fieldName = field.name;
          const context = this.getFieldContext(content, field.position);
          
          // Use optimized field analyzer
          const fieldType = this.fieldAnalyzer.inferFieldType(fieldName, context);
          
          // Generate validation rules
          const validationRules = this.generateValidationRules(fieldName, fieldType, context);
          
          // Detect dependencies (simplified for performance)
          const dependencies = this.detectFieldDependencies(fieldName, rawFields, content);

          return {
            field: {
              name: fieldName,
              label: this.generateFieldLabel(fieldName),
              type: fieldType,
              required: this.isFieldRequired(context),
              placeholder: this.generatePlaceholder(fieldName, fieldType),
              hint: this.generateFieldHint(fieldName, context),
              context: context.substring(0, 100),
              position: field.position
            },
            validationRules,
            fieldType,
            dependencies
          };
        },
        {
          onProgress: (progress) => {
            console.info(`Field analysis progress: ${progress.percentage}%`);
          }
        }
      );

      // Process results
      results.forEach(result => {
        if (result.status === 'fulfilled') {
          const { field, validationRules, fieldType, dependencies } = result.value;
          
          fieldAnalysis.fields.push(field);
          fieldAnalysis.validation_rules[field.name] = validationRules;
          fieldAnalysis.field_types[field.name] = fieldType;
          
          if (dependencies.length > 0) {
            fieldAnalysis.dependencies.push({
              field: field.name,
              depends_on: dependencies
            });
          }
        } else {
          console.warn('Field analysis failed for item:', result.reason);
        }
      });

      // Calculate metrics
      fieldAnalysis.complexity_score = this.calculateComplexityScore(fieldAnalysis.fields);
      fieldAnalysis.estimated_fill_time = this.estimateFillTime(fieldAnalysis.fields);

      return fieldAnalysis;
      
    } catch (error) {
      this.errorHandler.reportError(error, 'GoogleDocsSync', 'performAdvancedFieldAnalysis', 'high');
      // Return safe fallback
      return fieldAnalysis;
    }
  }

  /**
   * Note: inferFieldType method moved to FieldAnalyzer service for better performance
   */

  /**
   * Geração automática de regras de validação
   */
  generateValidationRules(fieldName, fieldType, context) {
    const rules = []

    // Regra obrigatória baseada no contexto
    if (this.isFieldRequired(context)) {
      rules.push(`v => !!v || '${this.generateFieldLabel(fieldName)} é obrigatório'`)
    }

    // Regras específicas por tipo
    switch (fieldType) {
      case 'cpf':
        rules.push(`v => !v || this.isValidCPF(v) || 'CPF inválido'`)
        break
      case 'cnpj':
        rules.push(`v => !v || this.isValidCNPJ(v) || 'CNPJ inválido'`)
        break
      case 'email':
        rules.push(`v => !v || /.+@.+\..+/.test(v) || 'Email inválido'`)
        break
      case 'phone':
        rules.push(`v => !v || /^\(?\d{2}\)?[\s-]?\d{4,5}-?\d{4}$/.test(v) || 'Telefone inválido'`)
        break
      case 'cep':
        rules.push(`v => !v || /^\d{5}-?\d{3}$/.test(v) || 'CEP inválido'`)
        break
      case 'process_number':
        rules.push(`v => !v || /^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$/.test(v) || 'Número de processo inválido'`)
        break
      case 'money':
        rules.push(`v => !v || parseFloat(v.toString().replace(/[^\d,]/g, '').replace(',', '.')) >= 0 || 'Valor inválido'`)
        break
      case 'date':
        rules.push(`v => !v || this.isValidDate(v) || 'Data inválida'`)
        break
    }

    return rules
  }

  /**
   * Sistema de sincronização em tempo real com WebSockets - com cleanup adequado
   */
  setupRealtimeSync() {
    try {
      // Fechar conexão existente se houver
      this.closeWebSocket();
      
      if (!this.webhookUrl) {
        throw new Error('Webhook URL not configured');
      }
      
      const wsUrl = this.webhookUrl.replace(/^http/, 'ws');
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleRealtimeUpdate(data);
        } catch (error) {
          this.errorHandler.reportError(error, 'GoogleDocsSync', 'parseWebSocketMessage', 'medium');
        }
      };
      
      this.socket.onclose = this.handleSocketClose;
      this.socket.onerror = this.handleSocketError;
      
      this.socket.onopen = () => {
        console.info('WebSocket connected successfully');
        // Clear any existing reconnect timer
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };
      
    } catch (error) {
      this.errorHandler.reportError(error, 'GoogleDocsSync', 'setupRealtimeSync', 'high');
    }
  }
  
  handleSocketClose(event) {
    console.info('WebSocket closed:', event.code, event.reason);
    
    // Only reconnect if it wasn't a manual close
    if (event.code !== 1000 && !this.isDestroyed) {
      this.scheduleReconnect();
    }
  }
  
  handleSocketError(error) {
    this.errorHandler.reportError(error, 'GoogleDocsSync', 'webSocketError', 'medium');
  }
  
  scheduleReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    
    this.reconnectTimer = setTimeout(() => {
      if (!this.isDestroyed) {
        console.info('Attempting WebSocket reconnection...');
        this.setupRealtimeSync();
      }
    }, this.config.reconnectInterval);
  }
  
  closeWebSocket() {
    if (this.socket) {
      // Remove event listeners to prevent memory leaks
      this.socket.onmessage = null;
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.onopen = null;
      
      if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
        this.socket.close(1000, 'Component cleanup');
      }
      
      this.socket = null;
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Handler para atualizações em tempo real
   */
  handleRealtimeUpdate(data) {
    switch (data.type) {
      case 'document_modified':
        this.handleDocumentModified(data.document_id)
        break
      case 'template_updated':
        this.handleTemplateUpdated(data.template_id)
        break
      case 'batch_sync_complete':
        this.handleBatchSyncComplete(data.results)
        break
    }
  }

  /**
   * Processamento de documento modificado
   */
  async handleDocumentModified(documentId) {
    const template = this.findTemplateByDocumentId(documentId)
    if (template) {
      await this.queueSync(template.id, 'modified')
    }
  }

  /**
   * Sistema de fila inteligente para sincronização
   */
  async queueSync(templateId, reason = 'manual', priority = 'normal') {
    const syncItem = {
      id: `sync_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      template_id: templateId,
      reason,
      priority,
      created_at: new Date(),
      retries: 0,
      max_retries: 3
    }

    // Inserir na fila baseado na prioridade
    if (priority === 'high') {
      this.syncQueue.unshift(syncItem)
    } else {
      this.syncQueue.push(syncItem)
    }

    // Processar fila se não estiver processando
    if (!this.isProcessing) {
      this.processSyncQueue()
    }

    return syncItem.id
  }

  /**
   * Processamento da fila de sincronização
   */
  async processSyncQueue() {
    if (this.isProcessing || this.syncQueue.length === 0) {
      return
    }

    this.isProcessing = true

    while (this.syncQueue.length > 0) {
      const item = this.syncQueue.shift()
      
      try {
        await this.performSync(item)
        this.notifySyncSuccess(item)
      } catch (error) {
        await this.handleSyncError(item, error)
      }
    }

    this.isProcessing = false
  }

  /**
   * Execução da sincronização
   */
  async performSync(syncItem) {
    const startTime = Date.now()
    
    try {
      // Analisar documento
      const analysis = await this.analyzeDocumentFields(syncItem.template_id)
      
      // Atualizar template no banco
      await this.api.put(`/api/admin/templates/${syncItem.template_id}/sync`, {
        ...analysis,
        sync_metadata: {
          sync_id: syncItem.id,
          sync_reason: syncItem.reason,
          sync_duration: Date.now() - startTime,
          synced_at: new Date().toISOString()
        }
      })

      // Notificar outros componentes
      this.emitSyncEvent('template_synced', {
        template_id: syncItem.template_id,
        sync_id: syncItem.id,
        changes: analysis.fields.length
      })

    } catch (error) {
      throw this.errorHandler.reportError(error, 'GoogleDocsSync', 'performSync', 'high');
    }
  }

  /**
   * Sistema de cache inteligente para templates com cleanup automático
   */
  async getCachedTemplate(templateId, forceRefresh = false) {
    try {
      const cacheKey = `template_${templateId}`;
      const cached = this.cache.get(cacheKey);
      
      // Limpar cache expirado periodicamente
      this.cleanExpiredCache();
      
      if (!forceRefresh && cached && !this.isCacheExpired(cached)) {
        // Update access time for LRU
        cached.lastAccessed = Date.now();
        return cached.data;
      }
      
      // Carregar do servidor com retry
      const template = await this.apiCallWithRetry(
        () => this.api.get(`/api/admin/templates/${templateId}`),
        'getCachedTemplate'
      );
      
      // Evict LRU if cache is full
      if (this.cache.size >= this.config.cacheMaxSize) {
        this.evictLRU();
      }
      
      // Armazenar no cache com TTL
      this.cache.set(cacheKey, {
        data: template.data,
        cachedAt: Date.now(),
        lastAccessed: Date.now(),
        ttl: this.config.cacheTTL
      });
      
      return template.data;
      
    } catch (error) {
      return this.errorHandler.reportError(error, 'GoogleDocsSync', 'getCachedTemplate', 'medium');
    }
  }
  
  isCacheExpired(cached) {
    return Date.now() > (cached.cachedAt + cached.ttl);
  }
  
  cleanExpiredCache() {
    const now = Date.now();
    for (const [key, value] of this.cache.entries()) {
      if (this.isCacheExpired(value)) {
        this.cache.delete(key);
      }
    }
  }
  
  evictLRU() {
    let oldest = Infinity;
    let oldestKey = null;
    
    for (const [key, value] of this.cache.entries()) {
      if (value.lastAccessed < oldest) {
        oldest = value.lastAccessed;
        oldestKey = key;
      }
    }
    
    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  /**
   * Geração de formulário dinâmico baseado na análise
   */
  generateDynamicFormSchema(templateAnalysis) {
    const schema = {
      title: `Formulário: ${templateAnalysis.metadata.title}`,
      description: templateAnalysis.metadata.description,
      sections: [],
      validation_mode: 'aggressive', // lazy, aggressive, realtime
      auto_save: true,
      estimated_time: templateAnalysis.estimated_fill_time
    }

    // Agrupar campos por seção baseado na posição
    const sections = this.groupFieldsBySection(templateAnalysis.fields)

    sections.forEach((sectionFields, index) => {
      const section = {
        id: `section_${index + 1}`,
        title: this.generateSectionTitle(sectionFields),
        description: this.generateSectionDescription(sectionFields),
        fields: [],
        conditional: this.detectConditionalLogic(sectionFields, templateAnalysis.dependencies)
      }

      sectionFields.forEach(field => {
        const formField = {
          name: field.name,
          type: this.mapFieldTypeToComponent(field.type),
          label: field.label,
          placeholder: field.placeholder,
          hint: field.hint,
          required: field.required,
          validation: templateAnalysis.validation_rules[field.name],
          props: this.generateFieldProps(field),
          conditional: this.getFieldConditionals(field.name, templateAnalysis.dependencies),
          auto_complete: this.getAutoCompleteSource(field.name, field.type)
        }

        // Adicionar dados específicos por tipo
        switch (field.type) {
          case 'select':
            formField.options = this.generateSelectOptions(field.name, field.context)
            break
          case 'date':
            formField.props.locale = 'pt-BR'
            formField.props.format = 'DD/MM/YYYY'
            break
          case 'money':
            formField.props.prefix = 'R$'
            formField.props.precision = 2
            break
        }

        section.fields.push(formField)
      })

      schema.sections.push(section)
    })

    return schema
  }

  /**
   * Auto-complete inteligente baseado em dados históricos
   */
  getAutoCompleteSource(fieldName, fieldType) {
    const autoCompleteMap = {
      'cliente_nome': '/api/autocomplete/clients/names',
      'advogado_nome': '/api/autocomplete/lawyers',
      'comarca': '/api/autocomplete/comarcas',
      'vara': '/api/autocomplete/varas',
      'lei_artigo': '/api/autocomplete/laws',
      'cidade': '/api/autocomplete/cities',
      'estado': '/api/autocomplete/states'
    }

    // Busca exata
    if (autoCompleteMap[fieldName]) {
      return autoCompleteMap[fieldName]
    }

    // Busca por tipo
    const typeMap = {
      'law_article': '/api/autocomplete/laws',
      'process_number': '/api/autocomplete/processes'
    }

    return typeMap[fieldType] || null
  }

  /**
   * Sistema de pré-preenchimento inteligente
   */
  async generateSmartDefaults(templateId, clientId) {
    try {
      const response = await this.apiCallWithRetry(
        () => this.api.post('/api/admin/documents/smart-defaults', {
          template_id: templateId,
          client_id: clientId
        }),
        'generateSmartDefaults'
      );

      return {
        defaults: response.data.defaults || {},
        confidence: response.data.confidence || {},
        suggestions: response.data.suggestions || [],
        learning_data: response.data.learning_data || {}
      };
    } catch (error) {
      this.errorHandler.reportError(error, 'GoogleDocsSync', 'generateSmartDefaults', 'low');
      // Return safe defaults instead of failing
      return { defaults: {}, confidence: {}, suggestions: [] };
    }
  }

  /**
   * Otimização de performance para grandes templates
   */
  async optimizeTemplatePerformance(templateId) {
    const template = await this.getCachedTemplate(templateId)
    
    const optimizations = {
      lazy_load_sections: template.fields.length > 20,
      chunk_size: Math.min(template.fields.length, 5),
      enable_virtual_scroll: template.fields.length > 50,
      debounce_validation: true,
      background_save: true
    }

    return optimizations
  }

  /**
   * Análise de qualidade do template
   */
  analyzeTemplateQuality(templateAnalysis) {
    const quality = {
      score: 0,
      issues: [],
      suggestions: [],
      accessibility: this.checkAccessibility(templateAnalysis),
      usability: this.checkUsability(templateAnalysis),
      completeness: this.checkCompleteness(templateAnalysis)
    }

    // Verificar problemas comuns
    if (templateAnalysis.fields.length === 0) {
      quality.issues.push('Template não possui campos dinâmicos')
      quality.score -= 50
    }

    if (templateAnalysis.fields.some(f => !f.label)) {
      quality.issues.push('Alguns campos não possuem labels')
      quality.score -= 10
    }

    if (templateAnalysis.complexity_score > 0.8) {
      quality.suggestions.push('Considere dividir o template em seções menores')
    }

    if (templateAnalysis.estimated_fill_time > 30) {
      quality.suggestions.push('Template muito longo - considere otimizar')
    }

    // Calcular score final
    quality.score = Math.max(0, 100 + quality.score)

    return quality
  }

  /**
   * Utilitários auxiliares
   */
  isFieldRequired(context) {
    const requiredIndicators = [
      'obrigatório', 'obrigatoria', 'required', '*', 'necessário',
      'deve ser', 'é necessário', 'campo obrigatório'
    ]
    
    return requiredIndicators.some(indicator => 
      context.toLowerCase().includes(indicator)
    )
  }

  generateFieldLabel(fieldName) {
    return fieldName
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .trim()
  }

  generatePlaceholder(fieldName, fieldType) {
    const placeholders = {
      cpf: '000.000.000-00',
      cnpj: '00.000.000/0000-00',
      email: 'exemplo@email.com',
      phone: '(11) 99999-9999',
      cep: '00000-000',
      date: 'DD/MM/AAAA',
      money: 'R$ 0,00',
      process_number: '0000000-00.0000.0.00.0000'
    }

    return placeholders[fieldType] || `Digite ${this.generateFieldLabel(fieldName).toLowerCase()}`
  }

  mapFieldTypeToComponent(fieldType) {
    const componentMap = {
      text: 'v-text-field',
      textarea: 'v-textarea', 
      select: 'v-select',
      date: 'v-date-picker',
      boolean: 'v-checkbox',
      money: 'v-currency-field',
      cpf: 'v-cpf-field',
      cnpj: 'v-cnpj-field',
      phone: 'v-phone-field',
      cep: 'v-cep-field'
    }

    return componentMap[fieldType] || 'v-text-field'
  }

  calculateComplexityScore(fields) {
    let score = 0
    
    // Pontuação baseada na quantidade de campos
    score += fields.length * 0.1
    
    // Pontuação baseada em tipos complexos
    fields.forEach(field => {
      if (['date', 'money', 'select'].includes(field.type)) {
        score += 0.2
      }
      if (['textarea', 'law_article'].includes(field.type)) {
        score += 0.3
      }
    })

    return Math.min(score, 1) // Normalizar entre 0 e 1
  }

  estimateFillTime(fields) {
    const timeMap = {
      text: 30,      // 30 segundos
      textarea: 120, // 2 minutos
      select: 15,    // 15 segundos
      date: 20,      // 20 segundos
      boolean: 5,    // 5 segundos
      money: 25,     // 25 segundos
      cpf: 20,       // 20 segundos
      phone: 25      // 25 segundos
    }

    let totalSeconds = 0
    fields.forEach(field => {
      totalSeconds += timeMap[field.type] || 30
    })

    return Math.ceil(totalSeconds / 60) // Retornar em minutos
  }

  /**
   * Eventos e notificações
   */
  emitSyncEvent(eventType, data) {
    // Emitir para componentes Vue via EventBus
    this.$eventBus?.$emit('template-sync', { type: eventType, data })
    
    // Notificar via WebSocket para outros usuários
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        type: 'broadcast',
        event: eventType,
        data
      }))
    }
  }

  notifySyncSuccess(syncItem) {
    this.$toast?.success(`Template sincronizado com sucesso`, {
      icon: 'mdi-sync',
      timeout: 3000
    })
  }

  async handleSyncError(syncItem, error) {
    syncItem.retries++;
    
    if (syncItem.retries <= syncItem.max_retries) {
      // Recolocar na fila com delay exponencial
      const delay = Math.min(Math.pow(2, syncItem.retries) * 1000, 30000); // Max 30s
      
      const timerId = setTimeout(() => {
        if (!this.isDestroyed) {
          this.syncQueue.push(syncItem);
          // Processar fila se não estiver processando
          if (!this.isProcessing) {
            this.processSyncQueue();
          }
        }
      }, delay);
      
      // Store timer for cleanup
      if (!this.retryTimers) {
        this.retryTimers = new Set();
      }
      this.retryTimers.add(timerId);
      
      this.errorHandler.reportError(error, 'GoogleDocsSync', `syncRetry${syncItem.retries}`, 'medium');
    } else {
      // Falha definitiva
      this.errorHandler.reportError(error, 'GoogleDocsSync', 'syncFinalFailure', 'high');
    }
  }

  /**
   * Configuração segura de URLs
   */
  getWebhookUrl() {
    // Never expose environment variables in frontend
    // URL should come from backend config or be relative
    if (process.env.NODE_ENV === 'development') {
      return 'ws://localhost:5000/ws';
    }
    
    // Use relative WebSocket URL in production
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws`;
  }
  
  /**
   * API call with automatic retry and error handling
   */
  async apiCallWithRetry(apiCall, context, maxRetries = 3) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await apiCall();
      } catch (error) {
        lastError = error;
        
        if (attempt === maxRetries || !this.errorHandler.isRetriable(error)) {
          break;
        }
        
        // Wait before retry
        await this.errorHandler.scheduleRetry(error, context, attempt, maxRetries);
      }
    }
    
    throw lastError;
  }
  
  /**
   * Cleanup method - CRITICAL for preventing memory leaks
   */
  destroy() {
    console.info('Destroying GoogleDocsSync instance...');
    
    this.isDestroyed = true;
    
    // Close WebSocket and clear timers
    this.closeWebSocket();
    
    // Clear retry timers
    if (this.retryTimers) {
      this.retryTimers.forEach(timerId => clearTimeout(timerId));
      this.retryTimers.clear();
    }
    
    // Clear cache
    this.cache.clear();
    
    // Clear sync queue
    this.syncQueue.length = 0;
    
    // Clear field analyzer cache
    if (this.fieldAnalyzer) {
      this.fieldAnalyzer.clearCache();
    }
    
    // Reset flags
    this.isProcessing = false;
    
    console.info('GoogleDocsSync instance destroyed');
  }
}

export default GoogleDocsSync;
