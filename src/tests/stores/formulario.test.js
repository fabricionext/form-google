import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useFormularioStore } from '../../stores/formulario.js';
import * as api from '../../services/api.js';

// Mock the API services
vi.mock('../../services/api.js', () => ({
  templatesAPI: {
    list: vi.fn(),
    get: vi.fn(),
  },
  formsAPI: {
    getSchema: vi.fn(),
    validate: vi.fn(),
  },
  documentsAPI: {
    generate: vi.fn(),
    getStatus: vi.fn(),
  },
  clientsAPI: {
    search: vi.fn(),
    suggest: vi.fn(),
    getByCpf: vi.fn(),
  },
  authoritiesAPI: {
    search: vi.fn(),
    suggest: vi.fn(),
  },
  pollStatus: vi.fn(),
}));

describe('Formulario Store', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useFormularioStore();
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('has correct initial state', () => {
      expect(store.formData).toEqual({});
      expect(store.clientes).toEqual([]);
      expect(store.autoridades).toEqual([]);
      expect(store.campos).toEqual([]);
      expect(store.dataChanged).toBe(false);
      expect(store.submitting).toBe(false);
      expect(store.templates).toEqual([]);
      expect(store.currentTemplate).toBe(null);
      expect(store.formSchema).toBe(null);
      expect(store.validationErrors).toEqual({});
      expect(store.loading).toBe(false);
      expect(store.documentGeneration.status).toBe(null);
    });
  });

  describe('Templates Management', () => {
    it('loads templates successfully', async () => {
      const mockTemplates = [
        { id: 1, name: 'Template 1' },
        { id: 2, name: 'Template 2' },
      ];

      api.templatesAPI.list.mockResolvedValue(mockTemplates);

      await store.loadTemplates();

      expect(store.templates).toEqual(mockTemplates);
      expect(store.loading).toBe(false);
    });

    it('handles template loading errors', async () => {
      api.templatesAPI.list.mockRejectedValue(new Error('API Error'));

      await expect(store.loadTemplates()).rejects.toThrow('API Error');
      expect(store.loading).toBe(false);
    });

    it('loads specific template with schema', async () => {
      const mockTemplate = { id: 1, name: 'Template 1' };
      const mockSchema = {
        fields: [
          { name: 'nome', label: 'Nome', type: 'text', required: true },
          { name: 'cpf', label: 'CPF', type: 'cpf', required: true },
        ],
      };

      api.templatesAPI.get.mockResolvedValue(mockTemplate);
      api.formsAPI.getSchema.mockResolvedValue(mockSchema);

      await store.loadTemplate(1);

      expect(store.currentTemplate).toEqual(mockTemplate);
      expect(store.formSchema).toEqual(mockSchema);
      expect(store.campos).toHaveLength(2);
      expect(store.campos[0].chave).toBe('nome');
      expect(store.campos[1].chave).toBe('cpf');
    });
  });

  describe('Form Validation', () => {
    beforeEach(() => {
      store.currentTemplate = { id: 1 };
      store.formData = { nome: 'João', cpf: '123.456.789-01' };
    });

    it('validates form successfully', async () => {
      const mockResponse = { valid: true, errors: {} };
      api.formsAPI.validate.mockResolvedValue(mockResponse);

      const result = await store.validateForm();

      expect(result).toBe(true);
      expect(store.validationErrors).toEqual({});
      expect(api.formsAPI.validate).toHaveBeenCalledWith(1, store.formData);
    });

    it('handles validation errors', async () => {
      const mockResponse = {
        valid: false,
        errors: { nome: ['Campo obrigatório'] },
      };
      api.formsAPI.validate.mockResolvedValue(mockResponse);

      const result = await store.validateForm();

      expect(result).toBe(false);
      expect(store.validationErrors).toEqual(mockResponse.errors);
    });

    it('requires template to validate', async () => {
      store.currentTemplate = null;

      const result = await store.validateForm();

      expect(result).toBe(false);
      expect(api.formsAPI.validate).not.toHaveBeenCalled();
    });
  });

  describe('Document Generation', () => {
    beforeEach(() => {
      store.currentTemplate = { id: 1 };
      store.formData = { nome: 'João', cpf: '123.456.789-01' };
    });

    it('generates document successfully', async () => {
      const mockValidationResponse = { valid: true, errors: {} };
      const mockGenerationResponse = { task_id: 'task-123' };
      const mockPollResult = {
        document_id: 'doc-456',
        download_url: 'https://example.com/download',
      };

      api.formsAPI.validate.mockResolvedValue(mockValidationResponse);
      api.documentsAPI.generate.mockResolvedValue(mockGenerationResponse);
      api.pollStatus.mockResolvedValue(mockPollResult);

      const result = await store.generateDocument();

      expect(store.submitting).toBe(false);
      expect(store.documentGeneration.status).toBe('SUCCESS');
      expect(store.documentGeneration.taskId).toBe('task-123');
      expect(store.documentGeneration.documentId).toBe('doc-456');
      expect(result).toEqual(mockPollResult);
    });

    it('fails when form is invalid', async () => {
      const mockValidationResponse = {
        valid: false,
        errors: { nome: ['Campo obrigatório'] },
      };

      api.formsAPI.validate.mockResolvedValue(mockValidationResponse);

      await expect(store.generateDocument()).rejects.toThrow(
        'Formulário contém erros de validação'
      );
      expect(api.documentsAPI.generate).not.toHaveBeenCalled();
    });

    it('handles generation errors', async () => {
      const mockValidationResponse = { valid: true, errors: {} };

      api.formsAPI.validate.mockResolvedValue(mockValidationResponse);
      api.documentsAPI.generate.mockRejectedValue(
        new Error('Generation failed')
      );

      await expect(store.generateDocument()).rejects.toThrow(
        'Generation failed'
      );
      expect(store.documentGeneration.status).toBe('FAILURE');
      expect(store.submitting).toBe(false);
    });

    it('requires template to generate', async () => {
      store.currentTemplate = null;

      await expect(store.generateDocument()).rejects.toThrow(
        'Template não selecionado'
      );
    });
  });

  describe('Client Search', () => {
    it('searches clients with modern API', async () => {
      const mockResults = [
        { id: 1, nome_completo: 'João Silva', cpf: '123.456.789-01' },
      ];

      api.clientsAPI.suggest.mockResolvedValue(mockResults);

      const results = await store.searchClients('João');

      expect(results).toEqual(mockResults);
      expect(api.clientsAPI.suggest).toHaveBeenCalledWith('João');
    });

    it('falls back to legacy API when modern fails', async () => {
      const mockLegacyResults = [
        { id: 1, nome_completo: 'João Silva', cpf: '123.456.789-01' },
      ];

      api.clientsAPI.suggest.mockRejectedValue(new Error('Not found'));
      api.clientsAPI.search.mockResolvedValue(mockLegacyResults);

      const results = await store.searchClients('João');

      expect(store.clientes).toEqual(mockLegacyResults);
      expect(api.clientsAPI.search).toHaveBeenCalledWith('João');
    });

    it('requires minimum query length', async () => {
      const results = await store.searchClients('Jo');

      expect(results).toEqual([]);
      expect(api.clientsAPI.suggest).not.toHaveBeenCalled();
    });

    it('gets client by CPF', async () => {
      const mockClient = {
        id: 1,
        nome_completo: 'João Silva',
        cpf: '123.456.789-01',
      };

      api.clientsAPI.getByCpf.mockResolvedValue(mockClient);

      const result = await store.getClientByCpf('123.456.789-01');

      expect(result).toEqual(mockClient);
      expect(api.clientsAPI.getByCpf).toHaveBeenCalledWith('123.456.789-01');
    });
  });

  describe('Authority Search', () => {
    it('searches authorities with modern API', async () => {
      const mockResults = [
        { id: 1, nome: 'DETRAN-SP', cidade: 'São Paulo', estado: 'SP' },
      ];

      api.authoritiesAPI.suggest.mockResolvedValue(mockResults);

      const results = await store.searchAuthorities('DETRAN');

      expect(results).toEqual(mockResults);
      expect(api.authoritiesAPI.suggest).toHaveBeenCalledWith('DETRAN');
    });

    it('falls back to legacy API when modern fails', async () => {
      const mockLegacyResults = [
        { id: 1, nome: 'DETRAN-SP', cidade: 'São Paulo', estado: 'SP' },
      ];

      api.authoritiesAPI.suggest.mockRejectedValue(new Error('Not found'));
      api.authoritiesAPI.search.mockResolvedValue(mockLegacyResults);

      const results = await store.searchAuthorities('DETRAN');

      expect(store.autoridades).toEqual(mockLegacyResults);
      expect(api.authoritiesAPI.search).toHaveBeenCalledWith('DETRAN');
    });
  });

  describe('Form Data Management', () => {
    it('updates field data', () => {
      store.atualizarCampo('nome', 'João Silva');

      expect(store.formData.nome).toBe('João Silva');
      expect(store.dataChanged).toBe(true);
    });

    it('fills client data correctly', () => {
      const clientData = {
        nome_completo: 'João Silva',
        cpf: '123.456.789-01',
        email: 'joao@example.com',
        endereco_cidade: 'São Paulo',
      };

      store.preencherCampoCliente(clientData);

      expect(store.formData.nome).toBe('João Silva');
      expect(store.formData.cpf).toBe('123.456.789-01');
      expect(store.formData.email).toBe('joao@example.com');
      expect(store.formData.endereco_cidade).toBe('São Paulo');
      expect(store.dataChanged).toBe(true);
    });

    it('fills client data for specific author', () => {
      const clientData = {
        nome_completo: 'João Silva',
        cpf: '123.456.789-01',
      };

      store.preencherCampoCliente(clientData, 2);

      expect(store.formData.autor_2_nome).toBe('João Silva');
      expect(store.formData.autor_2_cpf).toBe('123.456.789-01');
    });

    it('fills authority data correctly', () => {
      const authorityData = {
        nome: 'DETRAN-SP',
        cnpj: '12.345.678/0001-90',
        cidade: 'São Paulo',
        estado: 'SP',
      };

      store.preencherCampoAutoridade(authorityData, 1);

      expect(store.formData.orgao_transito_1_nome).toBe('DETRAN-SP');
      expect(store.formData.orgao_transito_1_cnpj).toBe('12.345.678/0001-90');
      expect(store.formData.orgao_transito_1_endereco_cidade).toBe('São Paulo');
      expect(store.dataChanged).toBe(true);
    });
  });

  describe('Draft Management', () => {
    beforeEach(() => {
      // Mock window.location.pathname
      Object.defineProperty(window, 'location', {
        value: { pathname: '/test-form' },
        writable: true,
      });
    });

    it('saves draft to localStorage', () => {
      store.formData = { nome: 'João', cpf: '123.456.789-01' };

      store.salvarRascunho();

      expect(localStorage.setItem).toHaveBeenCalledWith(
        'draft_/test-form',
        expect.stringContaining('João')
      );
    });

    it('loads draft from localStorage', () => {
      const mockDraft = {
        data: { nome: 'João', cpf: '123.456.789-01' },
        timestamp: new Date().toISOString(),
      };

      localStorage.getItem.mockReturnValue(JSON.stringify(mockDraft));

      const loaded = store.carregarRascunho();

      expect(loaded).toBe(true);
      expect(store.formData.nome).toBe('João');
      expect(store.formData.cpf).toBe('123.456.789-01');
    });

    it('handles missing draft gracefully', () => {
      localStorage.getItem.mockReturnValue(null);

      const loaded = store.carregarRascunho();

      expect(loaded).toBe(false);
    });
  });

  describe('State Management', () => {
    it('clears validation errors', () => {
      store.validationErrors = { nome: ['Erro'] };

      store.clearValidationErrors();

      expect(store.validationErrors).toEqual({});
    });

    it('resets document generation state', () => {
      store.documentGeneration = {
        status: 'SUCCESS',
        taskId: 'task-123',
        progress: 100,
        error: null,
      };

      store.resetDocumentGeneration();

      expect(store.documentGeneration.status).toBe(null);
      expect(store.documentGeneration.taskId).toBe(null);
      expect(store.documentGeneration.progress).toBe(0);
      expect(store.documentGeneration.error).toBe(null);
    });
  });

  describe('Computed Properties', () => {
    beforeEach(() => {
      store.campos = [
        { chave: 'nome', categoria: 'cliente' },
        { chave: 'endereco_cidade', categoria: 'endereco' },
        { chave: 'autor_1_nome', categoria: 'autor_dados' },
        { chave: 'autor_1_endereco_cidade', categoria: 'autor_endereco' },
        { chave: 'orgao_transito_1_nome', categoria: 'autoridades' },
      ];
    });

    it('organizes fields correctly', () => {
      const organized = store.camposOrganizados;

      expect(organized.cliente).toHaveLength(1);
      expect(organized.endereco).toHaveLength(1);
      expect(organized.autoridades).toHaveLength(1);
      expect(organized.autores[1]).toBeDefined();
      expect(organized.autores[1].dados).toHaveLength(1);
      expect(organized.autores[1].endereco).toHaveLength(1);
    });
  });
});
