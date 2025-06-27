/**
 * API Service - Integração completa com APIs REST
 * Migração de fetch nativo para Axios com tratamento de erros
 */

import axios from 'axios'

// Configuração base do Axios
const apiClient = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor para tratamento de erros
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    throw error.response?.data || { error: error.message }
  }
)

// Templates API
export const templatesAPI = {
  list: async () => {
    return await apiClient.get('/api/templates/')
  },
  
  get: async (templateId) => {
    return await apiClient.get(`/api/templates/${templateId}`)
  },
  
  getByType: async (documentType) => {
    return await apiClient.get(`/api/templates/by-type/${documentType}`)
  },
  
  getPlaceholders: async (templateId) => {
    return await apiClient.get(`/api/templates/${templateId}/placeholders`)
  },
  
  sync: async (templateId) => {
    return await apiClient.post(`/api/templates/${templateId}/sync`)
  },
  
  validate: async (templateId) => {
    return await apiClient.get(`/api/templates/${templateId}/validate`)
  }
}

// Forms API
export const formsAPI = {
  getSchema: async (templateId) => {
    return await apiClient.get(`/api/forms/${templateId}/schema`)
  },
  
  validate: async (templateId, formData) => {
    return await apiClient.post(`/api/forms/${templateId}/validate`, formData)
  },
  
  getDefaults: async (templateId, clientId = null) => {
    const params = clientId ? { client_id: clientId } : {}
    return await apiClient.get(`/api/forms/${templateId}/defaults`, { params })
  },
  
  saveDefaults: async (templateId, defaults) => {
    return await apiClient.post(`/api/forms/${templateId}/defaults`, defaults)
  },
  
  preview: async (templateId, formData) => {
    return await apiClient.post(`/api/forms/${templateId}/preview`, formData)
  },
  
  getValidationRules: async (templateId) => {
    return await apiClient.get(`/api/forms/${templateId}/validation-rules`)
  },
  
  getDynamicFields: async (templateId, triggers) => {
    return await apiClient.post(`/api/forms/${templateId}/dynamic-fields`, { triggers })
  }
}

// Documents API  
export const documentsAPI = {
  generate: async (templateId, data) => {
    return await apiClient.post(`/api/documents/generate/${templateId}`, data)
  },
  
  getStatus: async (taskId) => {
    return await apiClient.get(`/api/documents/status/${taskId}`)
  },
  
  download: async (documentId) => {
    const response = await apiClient.get(`/api/documents/${documentId}/download`, {
      responseType: 'blob'
    })
    return response
  },
  
  list: async (filters = {}) => {
    return await apiClient.get('/api/documents/', { params: filters })
  },
  
  get: async (documentId) => {
    return await apiClient.get(`/api/documents/${documentId}`)
  },
  
  delete: async (documentId) => {
    return await apiClient.delete(`/api/documents/${documentId}`)
  },
  
  retry: async (documentId) => {
    return await apiClient.post(`/api/documents/${documentId}/retry`)
  },
  
  batchGenerate: async (requests) => {
    return await apiClient.post('/api/documents/batch-generate', { requests })
  },
  
  getMetrics: async (period = '7d') => {
    return await apiClient.get('/api/documents/metrics', { params: { period } })
  }
}

// Clients API (legacy + new endpoints)
export const clientsAPI = {
  search: async (query) => {
    return await apiClient.get('/peticionador/api/clientes', { params: { q: query } })
  },
  
  getByCpf: async (cpf) => {
    return await apiClient.get(`/api/clients/cpf/${cpf}`)
  },
  
  create: async (clientData) => {
    return await apiClient.post('/api/clients/', clientData)
  },
  
  update: async (clientId, clientData) => {
    return await apiClient.put(`/api/clients/${clientId}`, clientData)
  },
  
  suggest: async (partial) => {
    return await apiClient.get('/api/clients/suggest', { params: { q: partial } })
  }
}

// Authorities API (legacy + new endpoints)
export const authoritiesAPI = {
  search: async (query) => {
    return await apiClient.get('/peticionador/api/autoridades', { params: { q: query } })
  },
  
  suggest: async (partial) => {
    return await apiClient.get('/api/authorities/suggest', { params: { q: partial } })
  },
  
  getCommonSets: async (location) => {
    return await apiClient.get('/api/authorities/common-sets', { params: { location } })
  },
  
  validate: async (authorityIds) => {
    return await apiClient.post('/api/authorities/validate', { authority_ids: authorityIds })
  }
}

// Utility para polling de status
export const pollStatus = async (taskId, maxAttempts = 60, interval = 2000) => {
  let attempts = 0
  
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        attempts++
        const status = await documentsAPI.getStatus(taskId)
        
        if (status.state === 'SUCCESS') {
          resolve(status)
        } else if (status.state === 'FAILURE') {
          reject(new Error(status.error || 'Document generation failed'))
        } else if (attempts >= maxAttempts) {
          reject(new Error('Timeout waiting for document generation'))
        } else {
          setTimeout(poll, interval)
        }
      } catch (error) {
        reject(error)
      }
    }
    
    poll()
  })
}
