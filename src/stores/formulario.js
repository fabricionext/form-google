import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import * as api from '@/services/api.js';

export const useFormularioStore = defineStore('formulario', () => {
  // --- STATE ---
  const formData = ref({});
  const clientes = ref([]);
  const autoridades = ref([]);
  const campos = ref([]);
  const dataChanged = ref(false);
  const submitting = ref(false);
  const templates = ref([]);
  const currentTemplate = ref(null);
  const formSchema = ref(null);
  const validationErrors = ref({});
  const loading = ref(false);
  const documentGeneration = ref({
    status: null,
    taskId: null,
    documentId: null,
    error: null,
  });

  // --- GETTERS (Computed) ---
  const camposOrganizados = computed(() => {
    // Implementação de exemplo, pode precisar de ajuste
    return campos.value.reduce((acc, campo) => {
      const secao = campo.secao || 'geral';
      if (!acc[secao]) {
        acc[secao] = [];
      }
      acc[secao].push(campo);
      return acc;
    }, {});
  });

  // --- ACTIONS ---
  function atualizarCampo(chave, valor) {
    formData.value[chave] = valor;
    dataChanged.value = true;
  }

  async function loadTemplates() {
    loading.value = true;
    try {
      templates.value = await api.templatesAPI.list();
    } catch (error) {
      console.error('Failed to load templates:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function loadTemplate(templateId) {
    loading.value = true;
    try {
      const template = await api.templatesAPI.get(templateId);
      const schema = await api.formsAPI.getSchema(templateId);
      currentTemplate.value = template;
      formSchema.value = schema;
      // Extrair campos do schema para a lista de campos
      campos.value = schema.fields.map(f => ({
        chave: f.name,
        label: f.label,
        tipo: f.type,
        obrigatorio: f.required,
      }));
    } catch (error) {
      console.error(`Failed to load template ${templateId}:`, error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function validateForm() {
    if (!currentTemplate.value) return false;
    validationErrors.value = {};
    try {
      const response = await api.formsAPI.validate(
        currentTemplate.value.id,
        formData.value
      );
      if (!response.valid) {
        validationErrors.value = response.errors;
        return false;
      }
      return true;
    } catch (error) {
      console.error('Validation API error:', error);
      return false;
    }
  }

  async function generateDocument() {
    submitting.value = true;
    documentGeneration.value = {
      status: 'STARTED',
      taskId: null,
      documentId: null,
      error: null,
    };

    if (!currentTemplate.value) {
      documentGeneration.value.status = 'FAILURE';
      throw new Error('Template não selecionado');
    }

    const isValid = await validateForm();
    if (!isValid) {
      submitting.value = false;
      documentGeneration.value.status = 'FAILURE';
      throw new Error('Formulário contém erros de validação');
    }

    try {
      const response = await api.documentsAPI.generate(
        currentTemplate.value.id,
        formData.value
      );
      documentGeneration.value.taskId = response.task_id;
      documentGeneration.value.status = 'PENDING';

      // Polling for result
      const pollResult = await api.pollStatus(response.task_id);
      documentGeneration.value.documentId = pollResult.document_id;
      documentGeneration.value.status = 'SUCCESS';
      submitting.value = false;
      return pollResult;
    } catch (error) {
      documentGeneration.value.status = 'FAILURE';
      documentGeneration.value.error = error.message;
      submitting.value = false;
      console.error('Document generation failed:', error);
      throw error;
    }
  }

  async function searchClients(query) {
    if (query.length < 3) return [];
    try {
      // Tenta a API moderna primeiro
      return await api.clientsAPI.suggest(query);
    } catch (e) {
      // Fallback para a API legada
      console.warn('Modern client search failed, falling back to legacy.');
      const legacyResults = await api.clientsAPI.search(query);
      clientes.value = legacyResults; // Atualiza o state
      return legacyResults;
    }
  }

  async function getClientByCpf(cpf) {
    try {
      return await api.clientsAPI.getByCpf(cpf);
    } catch (error) {
      console.error('Failed to get client by CPF:', error);
      return null;
    }
  }

  // --- EXPORTS ---
  return {
    formData,
    clientes,
    autoridades,
    campos,
    dataChanged,
    submitting,
    templates,
    currentTemplate,
    formSchema,
    validationErrors,
    loading,
    documentGeneration,
    camposOrganizados,
    atualizarCampo,
    loadTemplates,
    loadTemplate,
    validateForm,
    generateDocument,
    searchClients,
    getClientByCpf,
  };
});
