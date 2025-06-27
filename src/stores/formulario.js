import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import Fuse from 'fuse.js'
import { 
  templatesAPI, 
  formsAPI, 
  documentsAPI, 
  clientsAPI, 
  authoritiesAPI,
  pollStatus 
} from '../services/api.js'

export const useFormularioStore = defineStore('formulario', () => {
  // Estado reativo
  const formData = ref({})
  const clientes = ref([])
  const autoridades = ref([])
  const campos = ref([])
  const dataChanged = ref(false)
  const submitting = ref(false)
  
  // Novos estados para integração com APIs
  const templates = ref([])
  const currentTemplate = ref(null)
  const formSchema = ref(null)
  const validationErrors = ref({})
  const loading = ref(false)
  const documentGeneration = ref({
    status: null,
    taskId: null,
    progress: 0,
    error: null
  })
  
  // Instâncias Fuse.js para busca fuzzy
  const clienteFuse = ref(null)
  const autoridadeFuse = ref(null)
  
  // Computed
  const camposOrganizados = computed(() => {
    const grupos = {
      autores: {},
      cliente: [],
      endereco: [],
      processo: [],
      autoridades: [],
      polo_ativo: [],
      polo_passivo: [],
      terceiros: [],
      outros: []
    }
    
    // Organizar campos por categoria usando a lógica existente
    campos.value.forEach(campo => {
      const categoria = categorizarCampo(campo.chave)
      
      if (categoria === 'autor_dados' || categoria === 'autor_endereco') {
        const match = campo.chave.match(/autor_(\d+)_(.+)/)
        if (match) {
          const autorNum = parseInt(match[1])
          if (!grupos.autores[autorNum]) {
            grupos.autores[autorNum] = { dados: [], endereco: [] }
          }
          
          if (categoria === 'autor_endereco') {
            grupos.autores[autorNum].endereco.push(campo)
          } else {
            grupos.autores[autorNum].dados.push(campo)
          }
        } else {
          // Fallback para cliente
          if (campo.chave.includes('endereco')) {
            grupos.endereco.push(campo)
          } else {
            grupos.cliente.push(campo)
          }
        }
      } else if (grupos[categoria]) {
        grupos[categoria].push(campo)
      } else {
        grupos.outros.push(campo)
      }
    })
    
    return grupos
  })
  
  // Actions
  const inicializarBuscas = () => {
    if (clientes.value.length > 0) {
      clienteFuse.value = new Fuse(clientes.value, {
        keys: ['nome_completo', 'primeiro_nome', 'sobrenome', 'email', 'cpf'],
        threshold: 0.3,
        includeScore: true
      })
    }
    
    if (autoridades.value.length > 0) {
      autoridadeFuse.value = new Fuse(autoridades.value, {
        keys: ['nome', 'cidade', 'estado'],
        threshold: 0.4,
        includeScore: true
      })
    }
  }
  
  const buscarClientes = (query) => {
    if (!clienteFuse.value || !query.trim()) return []
    
    const results = clienteFuse.value.search(query)
    return results.slice(0, 10).map(result => result.item)
  }
  
  const buscarAutoridades = (query) => {
    if (!autoridadeFuse.value || !query.trim()) return []
    
    const results = autoridadeFuse.value.search(query)
    return results.slice(0, 10).map(result => result.item)
  }
  
  const preencherCampoCliente = (clienteData, autorIndex = null) => {
    const prefixo = autorIndex ? `autor_${autorIndex}_` : ''
    
    // Mapear dados do cliente para campos do formulário
    const mapeamento = {
      [`${prefixo}nome`]: clienteData.nome_completo || `${clienteData.primeiro_nome || ''} ${clienteData.sobrenome || ''}`.trim(),
      [`${prefixo}primeiro_nome`]: clienteData.primeiro_nome,
      [`${prefixo}sobrenome`]: clienteData.sobrenome,
      [`${prefixo}cpf`]: clienteData.cpf,
      [`${prefixo}rg`]: clienteData.rg_numero,
      [`${prefixo}email`]: clienteData.email,
      [`${prefixo}telefone`]: clienteData.telefone_celular || clienteData.telefone_outro,
      [`${prefixo}endereco_logradouro`]: clienteData.endereco_logradouro,
      [`${prefixo}endereco_numero`]: clienteData.endereco_numero,
      [`${prefixo}endereco_complemento`]: clienteData.endereco_complemento,
      [`${prefixo}endereco_bairro`]: clienteData.endereco_bairro,
      [`${prefixo}endereco_cidade`]: clienteData.endereco_cidade,
      [`${prefixo}endereco_estado`]: clienteData.endereco_estado,
      [`${prefixo}endereco_cep`]: clienteData.endereco_cep,
      [`${prefixo}nacionalidade`]: clienteData.nacionalidade,
      [`${prefixo}estado_civil`]: clienteData.estado_civil,
      [`${prefixo}profissao`]: clienteData.profissao,
      [`${prefixo}cnh_numero`]: clienteData.cnh_numero,
    }
    
    // Aplicar mapeamento aos dados do formulário
    Object.keys(mapeamento).forEach(chave => {
      if (mapeamento[chave] !== undefined && mapeamento[chave] !== null) {
        formData.value[chave] = mapeamento[chave]
      }
    })
    
    dataChanged.value = true
  }
  
  const preencherCampoAutoridade = (autoridadeData, index = 1) => {
    const prefixo = `orgao_transito_${index}_`
    
    const mapeamento = {
      [`${prefixo}nome`]: autoridadeData.nome,
      [`${prefixo}cnpj`]: autoridadeData.cnpj,
      [`${prefixo}endereco_logradouro`]: autoridadeData.logradouro,
      [`${prefixo}endereco_numero`]: autoridadeData.numero,
      [`${prefixo}endereco_complemento`]: autoridadeData.complemento,
      [`${prefixo}endereco_cidade`]: autoridadeData.cidade,
      [`${prefixo}endereco_estado`]: autoridadeData.estado,
      [`${prefixo}endereco_cep`]: autoridadeData.cep,
    }
    
    Object.keys(mapeamento).forEach(chave => {
      if (mapeamento[chave] !== undefined && mapeamento[chave] !== null) {
        formData.value[chave] = mapeamento[chave]
      }
    })
    
    dataChanged.value = true
  }
  
  const atualizarCampo = (chave, valor) => {
    formData.value[chave] = valor
    dataChanged.value = true
  }
  
  const salvarRascunho = () => {
    try {
      const rascunho = {
        data: formData.value,
        timestamp: new Date().toISOString()
      }
      localStorage.setItem(`draft_${window.location.pathname}`, JSON.stringify(rascunho))
    } catch (error) {
      console.warn('Erro ao salvar rascunho:', error)
    }
  }
  
  const carregarRascunho = () => {
    try {
      const rascunho = localStorage.getItem(`draft_${window.location.pathname}`)
      if (rascunho) {
        const dados = JSON.parse(rascunho)
        formData.value = { ...formData.value, ...dados.data }
        return true
      }
    } catch (error) {
      console.warn('Erro ao carregar rascunho:', error)
    }
    return false
  }
  
  // Novas actions para integração com APIs
  const loadTemplates = async () => {
    try {
      loading.value = true
      templates.value = await templatesAPI.list()
    } catch (error) {
      console.error('Erro ao carregar templates:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const loadTemplate = async (templateId) => {
    try {
      loading.value = true
      currentTemplate.value = await templatesAPI.get(templateId)
      formSchema.value = await formsAPI.getSchema(templateId)
      
      // Atualizar campos baseado no schema
      if (formSchema.value?.fields) {
        campos.value = formSchema.value.fields.map(field => ({
          chave: field.name,
          nome: field.label,
          tipo: field.type,
          obrigatorio: field.required || false,
          opcoes: field.options || null,
          descricao: field.description || '',
          categoria: field.category || categorizarCampo(field.name)
        }))
      }
    } catch (error) {
      console.error('Erro ao carregar template:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const validateForm = async (templateId = null) => {
    if (!templateId && !currentTemplate.value) return false
    
    try {
      const id = templateId || currentTemplate.value.id
      const result = await formsAPI.validate(id, formData.value)
      
      validationErrors.value = result.errors || {}
      return result.valid || false
    } catch (error) {
      console.error('Erro na validação:', error)
      validationErrors.value = { general: ['Erro na validação do formulário'] }
      return false
    }
  }
  
  const generateDocument = async (templateId = null) => {
    if (!templateId && !currentTemplate.value) {
      throw new Error('Template não selecionado')
    }
    
    try {
      submitting.value = true
      const id = templateId || currentTemplate.value.id
      
      // Validar antes de gerar
      const isValid = await validateForm(id)
      if (!isValid) {
        throw new Error('Formulário contém erros de validação')
      }
      
      // Iniciar geração
      const response = await documentsAPI.generate(id, formData.value)
      
      documentGeneration.value = {
        status: 'PENDING',
        taskId: response.task_id,
        progress: 0,
        error: null
      }
      
      // Monitorar progresso
      const result = await pollStatus(response.task_id)
      
      documentGeneration.value = {
        status: 'SUCCESS',
        taskId: response.task_id,
        progress: 100,
        error: null,
        documentId: result.document_id,
        downloadUrl: result.download_url
      }
      
      return result
    } catch (error) {
      documentGeneration.value = {
        status: 'FAILURE',
        taskId: documentGeneration.value.taskId,
        progress: 0,
        error: error.message
      }
      throw error
    } finally {
      submitting.value = false
    }
  }
  
  const searchClients = async (query) => {
    try {
      if (query.length < 3) return []
      
      // Tentar busca moderna primeiro
      try {
        const results = await clientsAPI.suggest(query)
        return results.slice(0, 10)
      } catch {
        // Fallback para busca legacy
        const response = await clientsAPI.search(query)
        clientes.value = response
        inicializarBuscas()
        return buscarClientes(query)
      }
    } catch (error) {
      console.error('Erro na busca de clientes:', error)
      return []
    }
  }
  
  const searchAuthorities = async (query) => {
    try {
      if (query.length < 3) return []
      
      // Tentar busca moderna primeiro
      try {
        const results = await authoritiesAPI.suggest(query)
        return results.slice(0, 10)
      } catch {
        // Fallback para busca legacy
        const response = await authoritiesAPI.search(query)
        autoridades.value = response
        inicializarBuscas()
        return buscarAutoridades(query)
      }
    } catch (error) {
      console.error('Erro na busca de autoridades:', error)
      return []
    }
  }
  
  const getClientByCpf = async (cpf) => {
    try {
      return await clientsAPI.getByCpf(cpf)
    } catch (error) {
      console.error('Erro ao buscar cliente por CPF:', error)
      return null
    }
  }
  
  const clearValidationErrors = () => {
    validationErrors.value = {}
  }
  
  const resetDocumentGeneration = () => {
    documentGeneration.value = {
      status: null,
      taskId: null,
      progress: 0,
      error: null
    }
  }
  
  // Watcher para auto-save quando dados mudam
  watch(formData, () => {
    if (dataChanged.value) {
      salvarRascunho()
    }
  }, { deep: true })
  
  return {
    // Estado original
    formData,
    clientes,
    autoridades,
    campos,
    dataChanged,
    submitting,
    
    // Novos estados
    templates,
    currentTemplate,
    formSchema,
    validationErrors,
    loading,
    documentGeneration,
    
    // Computed
    camposOrganizados,
    
    // Actions originais
    inicializarBuscas,
    buscarClientes,
    buscarAutoridades,
    preencherCampoCliente,
    preencherCampoAutoridade,
    atualizarCampo,
    salvarRascunho,
    carregarRascunho,
    
    // Novas actions
    loadTemplates,
    loadTemplate,
    validateForm,
    generateDocument,
    searchClients,
    searchAuthorities,
    getClientByCpf,
    clearValidationErrors,
    resetDocumentGeneration
  }
})

// Função auxiliar para categorização de campos (replicada da lógica backend)
function categorizarCampo(chave) {
  const chaveLower = chave.toLowerCase()
  
  // Autoridades de trânsito (primeira prioridade)
  if (chaveLower.includes('orgao_transito') || chaveLower.includes('autoridade')) {
    return 'autoridades'
  }
  
  // Autores numerados
  if (chaveLower.startsWith('autor_')) {
    const match = chaveLower.match(/autor_(\d+)_(.+)/)
    if (match) {
      const campoResto = match[2]
      if (campoResto.includes('endereco') || campoResto.includes('endereço')) {
        return 'autor_endereco'
      } else {
        return 'autor_dados'
      }
    } else {
      return chaveLower.includes('endereco') ? 'autor_endereco' : 'autor_dados'
    }
  }
  
  // Polo ativo
  const poloAtivoKeywords = [
    'requerente', 'impetrante', 'exequente', 'embargante', 
    'recorrente', 'agravante', 'apelante', 'substituido'
  ]
  if (poloAtivoKeywords.some(keyword => chaveLower.includes(keyword))) {
    return 'polo_ativo'
  }
  
  // Polo passivo
  const poloPassivoKeywords = [
    'reu', 'requerido', 'impetrado', 'executado', 'embargado',
    'recorrido', 'agravado', 'apelado', 'substituidor'
  ]
  if (poloPassivoKeywords.some(keyword => chaveLower.includes(keyword))) {
    return 'polo_passivo'
  }
  
  // Terceiros
  const terceirosKeywords = [
    'assistente', 'opoente', 'curador', 'tutor', 'ministerio_publico',
    'defensor', 'advogado', 'procurador'
  ]
  if (terceirosKeywords.some(keyword => chaveLower.includes(keyword)) ||
      chaveLower.includes('_mp_') || chaveLower.startsWith('mp_') || 
      chaveLower.endsWith('_mp') || chaveLower === 'mp') {
    return 'terceiros'
  }
  
  // Processo
  const processoKeywords = [
    'processo', 'infracao', 'artigo', 'multa', 'penalidade', 'data_infracao',
    'local', 'hora', 'comarca', 'vara', 'juiz', 'veiculo', 'placa', 'autos',
    'valor', 'saldo', 'detalhamento', 'pronome', 'data_atual', 'total_pontos'
  ]
  if (processoKeywords.some(keyword => chaveLower.includes(keyword))) {
    return 'processo'
  }
  
  // Endereço genérico
  const enderecoKeywords = [
    'endereco', 'logradouro', 'numero', 'complemento', 'bairro',
    'cidade', 'estado', 'cep', 'uf'
  ]
  if (enderecoKeywords.some(keyword => chaveLower.includes(keyword)) &&
      !chaveLower.startsWith('orgao_transito') && !chaveLower.startsWith('autor_') &&
      !chaveLower.includes('autoridade')) {
    return 'endereco'
  }
  
  // Cliente
  const clienteKeywords = [
    'primeiro_nome', 'sobrenome', 'nome', 'cpf', 'rg', 'cnh',
    'nacionalidade', 'profissao', 'estado_civil', 'proprietario', 'condutor'
  ]
  if (clienteKeywords.some(keyword => chaveLower.includes(keyword))) {
    return 'cliente'
  }
  
  // Datas
  const dataKeywords = ['data', '_dt', 'nascimento']
  if (dataKeywords.some(keyword => chaveLower.includes(keyword))) {
    return 'data'
  }
  
  return 'outros'
}