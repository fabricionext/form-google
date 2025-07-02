import axios from 'axios';

// Configuração base do axios
const api = axios.create({
  baseURL:
    window.location.hostname === 'localhost'
      ? 'http://localhost:5000'
      : `${window.location.protocol}//${window.location.hostname}`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Para sessões Flask
});

// Interceptor para tratar erros globalmente
api.interceptors.response.use(
  response => response,
  error => {
    console.error('Erro na API:', error);
    return Promise.reject(error);
  }
);

// Serviços de Modelos
export const modeloService = {
  // Listar todos os modelos
  async listar() {
    const response = await api.get('/api/v1/modelos/');
    return response.data;
  },

  // Buscar modelo por ID
  async buscarPorId(id) {
    const response = await api.get(`/api/v1/modelos/${id}`);
    return response.data;
  },

  // Buscar modelo por slug
  async buscarPorSlug(slug) {
    const response = await api.get(`/api/v1/modelos/${slug}`);
    return response.data;
  },

  // Criar novo modelo
  async criar(modelo) {
    const response = await api.post('/api/v1/modelos/', modelo);
    return response.data;
  },

  // Atualizar modelo
  async atualizar(id, modelo) {
    const response = await api.put(`/api/v1/modelos/${id}`, modelo);
    return response.data;
  },

  // Sincronizar placeholders
  async sincronizarPlaceholders(id) {
    const response = await api.post(`/api/v1/modelos/${id}/sincronizar`);
    return response.data;
  },

  // Reordenar placeholders
  async reordenarPlaceholders(id, novaOrdem) {
    const response = await api.post(`/api/v1/modelos/${id}/reordenar`, {
      nova_ordem: novaOrdem,
    });
    return response.data;
  },
};

// Serviços de Clientes
export const clienteService = {
  // Buscar cliente por CPF - usando o endpoint legacy que já funciona
  async buscarPorCpf(cpf) {
    const response = await api.get(
      `/peticionador/api/clientes/busca_cpf?cpf=${cpf}`
    );
    return response.data;
  },

  // Criar novo cliente
  async criar(dadosCliente) {
    try {
      const response = await api.post('/api/public/clientes', dadosCliente);
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(
          error.response.data.message ||
            error.response.data.error ||
            'Erro ao cadastrar cliente'
        );
      }
      throw new Error('Erro de conexão com o servidor');
    }
  },
};

// Serviços de Formulários
export const formularioService = {
  // Buscar dados do formulário por slug
  async buscarPorSlug(slug) {
    const response = await api.get(`/api/v1/formularios/${slug}`);
    return response.data;
  },

  // Gerar documento a partir do formulário preenchido
  async gerarDocumento(slug, dadosFormulario) {
    const response = await api.post(
      `/api/v1/formularios/${slug}/gerar_documento`,
      dadosFormulario
    );
    return response.data;
  },
};

// Serviços do Google Drive
export const googleDriveService = {
  // Criar pasta no Google Drive
  async criarPasta(nomePasta, clienteId) {
    try {
      const response = await api.post('/api/google-drive/criar-pasta', {
        nome_pasta: nomePasta,
        cliente_id: clienteId,
      });
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(
          error.response.data.message ||
            error.response.data.error ||
            'Erro ao criar pasta no Google Drive'
        );
      }
      throw new Error('Erro de conexão com o servidor');
    }
  },
};

export default api;
