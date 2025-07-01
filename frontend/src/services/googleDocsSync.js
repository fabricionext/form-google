// services/googleDocsSync.js
class GoogleDocsSync {
  constructor(apiClient) {
    this.api = apiClient
    this.syncQueue = []
    this.isProcessing = false
    this.webhookUrl = process.env.VUE_APP_WEBHOOK_URL
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
      throw new Error(`Erro ao analisar documento: ${error.message}`)
    }
  }

  /**
   * Análise avançada de campos com IA para determinar tipos e validações
   */
  performAdvancedFieldAnalysis(content, rawFields) {
    const fieldAnalysis = {
      fields: [],
      validation_rules: {},
      field_types: {},
      dependencies: [],
      complexity_score: 0,
      estimated_fill_time: 0
    }

    rawFields.forEach(field => {
      const fieldName = field.name
      const context = this.getFieldContext(content, field.position)
      
      // Determinar tipo do campo baseado no contexto
      const fieldType = this.inferFieldType(fieldName, context)
      
      // Gerar regras de validação
      const validationRules = this.generateValidationRules(fieldName, fieldType, context)
      
      // Detectar dependências entre campos
      const dependencies = this.detectFieldDependencies(fieldName, rawFields, content)

      fieldAnalysis.fields.push({
        name: fieldName,
        label: this.generateFieldLabel(fieldName),
        type: fieldType,
        required: this.isFieldRequired(context),
        placeholder: this.generatePlaceholder(fieldName, fieldType),
        hint: this.generateFieldHint(fieldName, context),
        context: context.substring(0, 100), // Contexto limitado
        position: field.position
      })

      fieldAnalysis.validation_rules[fieldName] = validationRules
      fieldAnalysis.field_types[fieldName] = fieldType
      
      if (dependencies.length > 0) {
        fieldAnalysis.dependencies.push({
          field: fieldName,
          depends_on: dependencies
        })
      }
    })

    // Calcular métricas
    fieldAnalysis.complexity_score = this.calculateComplexityScore(fieldAnalysis.fields)
    fieldAnalysis.estimated_fill_time = this.estimateFillTime(fieldAnalysis.fields)

    return fieldAnalysis
  }

  /**
   * Inferência inteligente do tipo de campo
   */
  inferFieldType(fieldName, context) {
    const patterns = {
      cpf: /cpf|documento|registro/i,
      cnpj: /cnpj|empresa|razao.?social/i,
      email: /email|e-mail|correio/i,
      phone: /telefone|celular|contato|fone/i,
      date: /data|nascimento|vencimento|prazo/i,
      money: /valor|preco|salario|renda|quantia|r$|real/i,
      cep: /cep|codigo.?postal/i,
      process_number: /processo|numero.?processo|n[ºª].*processo/i,
      law_article: /artigo|art\.|lei|codigo|inciso/i,
      textarea: /observa|descri|motivo|justifica|relato/i,
      select: /estado|sexo|categoria|tipo|natureza/i,
      boolean: /aceita|concorda|declara|sim.*nao/i
    }

    for (const [type, pattern] of Object.entries(patterns)) {
      if (pattern.test(fieldName) || pattern.test(context)) {
        return type
      }
    }

    // Análise do contexto para tipos específicos
    if (context.includes('R$') || /\d+[,.]?\d*/.test(context)) {
      return 'money'
    }

    if (/\d{2}\/\d{2}\/\d{4}/.test(context)) {
      return 'date'
    }

    if (context.length > 100) {
      return 'textarea'
    }

    return 'text' // Default
  }

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
   * Sistema de sincronização em tempo real com WebSockets
   */
  setupRealtimeSync() {
    this.socket = new WebSocket(this.webhookUrl.replace('http', 'ws'))
    
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.handleRealtimeUpdate(data)
    }

    this.socket.onclose = () => {
      // Reconectar após 5 segundos
      setTimeout(() => this.setupRealtimeSync(), 5000)
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
      throw new Error(`Sync failed: ${error.message}`)
    }
  }

  /**
   * Sistema de cache inteligente para templates
   */
  async getCachedTemplate(templateId, forceRefresh = false) {
    const cacheKey = `template_${templateId}`
    const cached = this.cache.get(cacheKey)

    if (!forceRefresh && cached && !this.isCacheExpired(cached)) {
      return cached.data
    }

    // Carregar do servidor
    const template = await this.api.get(`/api/admin/templates/${templateId}`)
    
    // Armazenar no cache com TTL
    this.cache.set(cacheKey, {
      data: template.data,
      cached_at: Date.now(),
      ttl: 15 * 60 * 1000 // 15 minutos
    })

    return template.data
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
      const response = await this.api.post('/api/admin/documents/smart-defaults', {
        template_id: templateId,
        client_id: clientId
      })

      return {
        defaults: response.data.defaults,
        confidence: response.data.confidence,
        suggestions: response.data.suggestions,
        learning_data: response.data.learning_data
      }
    } catch (error) {
      console.warn('Smart defaults failed:', error)
      return { defaults: {}, confidence: {}, suggestions: [] }
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
    syncItem.retries++
    
    if (syncItem.retries <= syncItem.max_retries) {
      // Recolocar na fila com delay exponencial
      const delay = Math.pow(2, syncItem.retries) * 1000
      setTimeout(() => {
        this.syncQueue.push(syncItem)
      }, delay)
    } else {
      // Falha definitiva
      this.$toast?.error(`Falha na sincronização: ${error.message}`, {
        icon: 'mdi-alert',
        timeout: 5000
      })
    }
  }
}

export default GoogleDocsSync
