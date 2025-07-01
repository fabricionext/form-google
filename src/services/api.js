const API_BASE = '/api'; // Ou o prefixo da sua API

/**
 * Função helper para chamadas fetch
 */
async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ message: response.statusText }));
    throw new Error(errorData.message || 'Erro na API');
  }

  return response.json();
}

/**
 * API de Templates
 */
export const templatesAPI = {
  list: () => apiFetch(`${API_BASE}/templates`),
  get: id => apiFetch(`${API_base}/templates/${id}`),
};

/**
 * API de Formulários
 */
export const formsAPI = {
  getSchema: templateId =>
    apiFetch(`${API_BASE}/templates/${templateId}/schema`),
  validate: (templateId, data) =>
    apiFetch(`${API_BASE}/templates/${templateId}/validate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

/**
 * API de Documentos
 */
export const documentsAPI = {
  generate: (templateId, data) =>
    apiFetch(`${API_BASE}/documents/generate`, {
      method: 'POST',
      body: JSON.stringify({ template_id: templateId, data }),
    }),
  getStatus: taskId => apiFetch(`${API_BASE}/tasks/${taskId}/status`),
};

/**
 * API de Clientes (com fallback para legacy)
 */
export const clientsAPI = {
  search: query => apiFetch(`/peticionador/api/clientes?q=${query}`), // Rota legada
  suggest: query => apiFetch(`${API_BASE}/clients/suggest?q=${query}`),
  getByCpf: cpf => apiFetch(`${API_BASE}/clients/cpf/${cpf}`),
};

/**
 * API de Autoridades
 */
export const authoritiesAPI = {
  search: query => apiFetch(`/peticionador/api/autoridades?q=${query}`), // Rota legada
  suggest: query => apiFetch(`${API_BASE}/authorities/suggest?q=${query}`),
};

/**
 * Função de polling para status de tarefas
 */
export async function pollStatus(taskId, interval = 2000, maxAttempts = 30) {
  let attempts = 0;
  while (attempts < maxAttempts) {
    try {
      const result = await documentsAPI.getStatus(taskId);
      if (result.status === 'SUCCESS' || result.status === 'FAILURE') {
        return result;
      }
    } catch (error) {
      console.error('Polling error:', error);
      // Decide se quer parar ou continuar em caso de erro de rede
    }
    await new Promise(resolve => setTimeout(resolve, interval));
    attempts++;
  }
  throw new Error('Polling timed out');
}
