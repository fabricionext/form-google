import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref } from 'vue';
import { useFormValidation } from '../../composables/useFormValidation.js';
import { formsAPI } from '../../services/api.js';

// Mock the API
vi.mock('../../services/api.js', () => ({
  formsAPI: {
    validate: vi.fn(),
    getValidationRules: vi.fn(),
  },
}));

describe('useFormValidation', () => {
  let templateId, formData;

  beforeEach(() => {
    templateId = ref(1);
    formData = ref({
      nome: 'João Silva',
      cpf: '123.456.789-01',
      email: 'joao@example.com',
    });

    vi.clearAllMocks();
  });

  describe('Form Validation', () => {
    it('validates form successfully', async () => {
      const mockResponse = {
        valid: true,
        errors: {},
      };

      formsAPI.validate.mockResolvedValue(mockResponse);

      const { validateForm, isFormValid } = useFormValidation(
        templateId,
        formData
      );

      const result = await validateForm();

      expect(result).toBe(true);
      expect(isFormValid.value).toBe(true);
      expect(formsAPI.validate).toHaveBeenCalledWith(1, formData.value);
    });

    it('handles validation errors', async () => {
      const mockResponse = {
        valid: false,
        errors: {
          nome: ['Campo obrigatório'],
          cpf: ['CPF inválido'],
        },
      };

      formsAPI.validate.mockResolvedValue(mockResponse);

      const { validateForm, validationErrors, isFormValid } = useFormValidation(
        templateId,
        formData
      );

      const result = await validateForm();

      expect(result).toBe(false);
      expect(isFormValid.value).toBe(false);
      expect(validationErrors.value).toEqual(mockResponse.errors);
    });

    it('handles API errors gracefully', async () => {
      formsAPI.validate.mockRejectedValue(new Error('API Error'));

      const { validateForm, validationErrors } = useFormValidation(
        templateId,
        formData
      );

      const result = await validateForm();

      expect(result).toBe(false);
      expect(validationErrors.value).toHaveProperty('_general');
    });
  });

  describe('Field Validation', () => {
    it('validates individual field', async () => {
      const mockResponse = {
        valid: true,
        errors: {},
      };

      formsAPI.validate.mockResolvedValue(mockResponse);

      const { validateField, validationErrors } = useFormValidation(
        templateId,
        formData
      );

      const result = await validateField('nome', 'João Silva');

      expect(result).toBe(true);
      expect(validationErrors.value.nome).toBeUndefined();
      expect(formsAPI.validate).toHaveBeenCalledWith(1, { nome: 'João Silva' });
    });

    it('handles field validation errors', async () => {
      const mockResponse = {
        valid: false,
        errors: {
          nome: ['Campo muito curto'],
        },
      };

      formsAPI.validate.mockResolvedValue(mockResponse);

      const { validateField, validationErrors } = useFormValidation(
        templateId,
        formData
      );

      const result = await validateField('nome', 'Jo');

      expect(result).toBe(false);
      expect(validationErrors.value.nome).toEqual(['Campo muito curto']);
    });
  });

  describe('Client-side Validation', () => {
    it('validates required fields', () => {
      const { validateFieldClient } = useFormValidation(templateId, formData);

      const errors = validateFieldClient('nome', '', ['required']);

      expect(errors).toContain('nome é obrigatório');
    });

    it('validates email format', () => {
      const { validateFieldClient } = useFormValidation(templateId, formData);

      const errors = validateFieldClient('email', 'invalid-email', ['email']);

      expect(errors).toContain('Email inválido');
    });

    it('validates CPF format', () => {
      const { validateFieldClient } = useFormValidation(templateId, formData);

      const errors = validateFieldClient('cpf', '123', ['cpf']);

      expect(errors).toContain('CPF deve ter 11 dígitos');
    });

    it('validates CPF algorithm', () => {
      const { validateFieldClient } = useFormValidation(templateId, formData);

      // Invalid CPF (all same digits)
      const errors = validateFieldClient('cpf', '11111111111', ['cpf']);

      expect(errors).toContain('CPF inválido');
    });

    it('validates CNPJ format', () => {
      const { validateFieldClient } = useFormValidation(templateId, formData);

      const errors = validateFieldClient('cnpj', '123456', ['cnpj']);

      expect(errors).toContain('CNPJ deve ter 14 dígitos');
    });

    it('validates phone format', () => {
      const { validateFieldClient } = useFormValidation(templateId, formData);

      const errors = validateFieldClient('telefone', '123', ['phone']);

      expect(errors).toContain('Telefone deve ter 10 ou 11 dígitos');
    });

    it('validates CEP format', () => {
      const { validateFieldClient } = useFormValidation(templateId, formData);

      const errors = validateFieldClient('cep', '12345', ['cep']);

      expect(errors).toContain('CEP deve ter 8 dígitos');
    });

    it('validates minimum length', () => {
      const { validateFieldClient } = useFormValidation(templateId, formData);

      const errors = validateFieldClient('nome', 'Jo', [
        { type: 'minLength', params: 3 },
      ]);

      expect(errors).toContain('Mínimo de 3 caracteres');
    });

    it('validates maximum length', () => {
      const { validateFieldClient } = useFormValidation(templateId, formData);

      const errors = validateFieldClient('nome', 'Nome muito longo', [
        { type: 'maxLength', params: 10 },
      ]);

      expect(errors).toContain('Máximo de 10 caracteres');
    });
  });

  describe('Error Management', () => {
    it('clears all errors', () => {
      const { validationErrors, clearErrors } = useFormValidation(
        templateId,
        formData
      );

      validationErrors.value = {
        nome: ['Erro 1'],
        cpf: ['Erro 2'],
      };

      clearErrors();

      expect(validationErrors.value).toEqual({});
    });

    it('clears specific field error', () => {
      const { validationErrors, clearFieldError } = useFormValidation(
        templateId,
        formData
      );

      validationErrors.value = {
        nome: ['Erro 1'],
        cpf: ['Erro 2'],
      };

      clearFieldError('nome');

      expect(validationErrors.value).toEqual({
        cpf: ['Erro 2'],
      });
    });

    it('sets field error', () => {
      const { validationErrors, setFieldError } = useFormValidation(
        templateId,
        formData
      );

      setFieldError('nome', 'Campo obrigatório');

      expect(validationErrors.value.nome).toEqual(['Campo obrigatório']);
    });

    it('adds error to existing field errors', () => {
      const { validationErrors, addFieldError } = useFormValidation(
        templateId,
        formData
      );

      validationErrors.value = {
        nome: ['Erro 1'],
      };

      addFieldError('nome', 'Erro 2');

      expect(validationErrors.value.nome).toEqual(['Erro 1', 'Erro 2']);
    });
  });

  describe('Computed Properties', () => {
    it('calculates isFormValid correctly', () => {
      const { validationErrors, isFormValid } = useFormValidation(
        templateId,
        formData
      );

      expect(isFormValid.value).toBe(true);

      validationErrors.value = { nome: ['Erro'] };
      expect(isFormValid.value).toBe(false);
    });

    it('calculates hasErrors correctly', () => {
      const { validationErrors, hasErrors } = useFormValidation(
        templateId,
        formData
      );

      expect(hasErrors.value).toBe(false);

      validationErrors.value = { nome: ['Erro'] };
      expect(hasErrors.value).toBe(true);
    });

    it('calculates errorCount correctly', () => {
      const { validationErrors, errorCount } = useFormValidation(
        templateId,
        formData
      );

      expect(errorCount.value).toBe(0);

      validationErrors.value = {
        nome: ['Erro 1'],
        cpf: ['Erro 2'],
      };
      expect(errorCount.value).toBe(2);
    });

    it('gets field errors correctly', () => {
      const { validationErrors, getFieldErrors } = useFormValidation(
        templateId,
        formData
      );

      validationErrors.value = {
        nome: ['Erro 1', 'Erro 2'],
      };

      expect(getFieldErrors.value('nome')).toEqual(['Erro 1', 'Erro 2']);
      expect(getFieldErrors.value('cpf')).toEqual([]);
    });

    it('checks if field has error correctly', () => {
      const { validationErrors, hasFieldError } = useFormValidation(
        templateId,
        formData
      );

      validationErrors.value = {
        nome: ['Erro 1'],
      };

      expect(hasFieldError.value('nome')).toBe(true);
      expect(hasFieldError.value('cpf')).toBe(false);
    });
  });

  describe('Validation Rules Loading', () => {
    it('loads validation rules for template', async () => {
      const mockRules = {
        nome: ['required', { type: 'minLength', params: 2 }],
        cpf: ['required', 'cpf'],
      };

      formsAPI.getValidationRules.mockResolvedValue(mockRules);

      const { loadValidationRules, validationRules } = useFormValidation(
        templateId,
        formData
      );

      await loadValidationRules();

      expect(validationRules.value).toEqual(mockRules);
      expect(formsAPI.getValidationRules).toHaveBeenCalledWith(1);
    });

    it('handles validation rules loading errors', async () => {
      formsAPI.getValidationRules.mockRejectedValue(new Error('API Error'));

      const { loadValidationRules, validationRules } = useFormValidation(
        templateId,
        formData
      );

      await loadValidationRules();

      expect(validationRules.value).toEqual({});
    });
  });
});
