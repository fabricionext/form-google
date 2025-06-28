/**
 * useFormValidation - Composable para validação de formulários em tempo real
 * Integra com as APIs REST e fornece validação reativa
 */

import { ref, computed, watch } from 'vue';
import { formsAPI } from '../services/api.js';

export function useFormValidation(templateId, formData) {
  // Estado reativo
  const validationErrors = ref({});
  const validationRules = ref({});
  const isValidating = ref(false);
  const lastValidation = ref(null);

  // Debounce timeout
  const debounceTimeout = ref(null);

  // Computed properties
  const isFormValid = computed(() => {
    return Object.keys(validationErrors.value).length === 0;
  });

  const hasErrors = computed(() => {
    return Object.keys(validationErrors.value).length > 0;
  });

  const errorCount = computed(() => {
    return Object.keys(validationErrors.value).length;
  });

  const getFieldErrors = computed(() => {
    return fieldName => validationErrors.value[fieldName] || [];
  });

  const hasFieldError = computed(() => {
    return fieldName => {
      const errors = validationErrors.value[fieldName];
      return Boolean(errors && errors.length > 0);
    };
  });

  // Validation rules cache
  const loadValidationRules = async (templateIdParam = null) => {
    const id = templateIdParam || templateId.value;
    if (!id) {return;}

    try {
      validationRules.value = await formsAPI.getValidationRules(id);
    } catch (error) {
      console.error('Erro ao carregar regras de validação:', error);
    }
  };

  // Main validation function
  const validateForm = async (templateIdParam = null) => {
    const id = templateIdParam || templateId.value;
    if (!id || !formData.value) {return false;}

    try {
      isValidating.value = true;

      const result = await formsAPI.validate(id, formData.value);

      validationErrors.value = result.errors || {};
      lastValidation.value = new Date();

      return result.valid || false;
    } catch (error) {
      console.error('Erro na validação do formulário:', error);
      validationErrors.value = {
        _general: ['Erro na validação do formulário'],
      };
      return false;
    } finally {
      isValidating.value = false;
    }
  };

  // Field-specific validation
  const validateField = async (fieldName, value, templateIdParam = null) => {
    const id = templateIdParam || templateId.value;
    if (!id) {return true;}

    try {
      // Create a partial form data object with just this field
      const partialData = { [fieldName]: value };

      const result = await formsAPI.validate(id, partialData);

      if (result.errors && result.errors[fieldName]) {
        validationErrors.value = {
          ...validationErrors.value,
          [fieldName]: result.errors[fieldName],
        };
        return false;
      } else {
        // Clear errors for this field
        const newErrors = { ...validationErrors.value };
        delete newErrors[fieldName];
        validationErrors.value = newErrors;
        return true;
      }
    } catch (error) {
      console.error(`Erro na validação do campo ${fieldName}:`, error);
      return false;
    }
  };

  // Debounced validation
  const validateFieldDebounced = (fieldName, value, delay = 500) => {
    clearTimeout(debounceTimeout.value);

    debounceTimeout.value = setTimeout(() => {
      validateField(fieldName, value);
    }, delay);
  };

  // Client-side validation rules
  const clientValidators = {
    required: (value, fieldName) => {
      if (!value || (typeof value === 'string' && value.trim() === '')) {
        return `${fieldName} é obrigatório`;
      }
      return null;
    },

    email: value => {
      if (!value) {return null;}
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) {
        return 'Email inválido';
      }
      return null;
    },

    cpf: value => {
      if (!value) {return null;}

      // Remove formatting
      const numbers = value.replace(/\D/g, '');

      if (numbers.length !== 11) {
        return 'CPF deve ter 11 dígitos';
      }

      // Validate CPF algorithm
      if (!isValidCpf(numbers)) {
        return 'CPF inválido';
      }

      return null;
    },

    cnpj: value => {
      if (!value) {return null;}

      const numbers = value.replace(/\D/g, '');

      if (numbers.length !== 14) {
        return 'CNPJ deve ter 14 dígitos';
      }

      if (!isValidCnpj(numbers)) {
        return 'CNPJ inválido';
      }

      return null;
    },

    phone: value => {
      if (!value) {return null;}

      const numbers = value.replace(/\D/g, '');

      if (numbers.length < 10 || numbers.length > 11) {
        return 'Telefone deve ter 10 ou 11 dígitos';
      }

      return null;
    },

    cep: value => {
      if (!value) {return null;}

      const numbers = value.replace(/\D/g, '');

      if (numbers.length !== 8) {
        return 'CEP deve ter 8 dígitos';
      }

      return null;
    },

    minLength: (value, min) => {
      if (!value) {return null;}
      if (value.length < min) {
        return `Mínimo de ${min} caracteres`;
      }
      return null;
    },

    maxLength: (value, max) => {
      if (!value) {return null;}
      if (value.length > max) {
        return `Máximo de ${max} caracteres`;
      }
      return null;
    },
  };

  // Client-side validation
  const validateFieldClient = (fieldName, value, rules = []) => {
    const errors = [];

    // Get field rules from validation rules if available
    const fieldRules = validationRules.value[fieldName] || rules;

    if (Array.isArray(fieldRules)) {
      fieldRules.forEach(rule => {
        let error = null;

        if (typeof rule === 'string') {
          // Simple rule name
          if (clientValidators[rule]) {
            error = clientValidators[rule](value, fieldName);
          }
        } else if (typeof rule === 'object') {
          // Rule with parameters
          const ruleName = rule.type || rule.name;
          const params = rule.params || rule.value;

          if (clientValidators[ruleName]) {
            error = clientValidators[ruleName](value, params, fieldName);
          }
        }

        if (error) {
          errors.push(error);
        }
      });
    }

    return errors;
  };

  // Utility functions
  const clearErrors = () => {
    validationErrors.value = {};
  };

  const clearFieldError = fieldName => {
    if (validationErrors.value[fieldName]) {
      const newErrors = { ...validationErrors.value };
      delete newErrors[fieldName];
      validationErrors.value = newErrors;
    }
  };

  const setFieldError = (fieldName, errors) => {
    validationErrors.value = {
      ...validationErrors.value,
      [fieldName]: Array.isArray(errors) ? errors : [errors],
    };
  };

  const addFieldError = (fieldName, error) => {
    const currentErrors = validationErrors.value[fieldName] || [];
    validationErrors.value = {
      ...validationErrors.value,
      [fieldName]: [...currentErrors, error],
    };
  };

  // Watch for template changes
  watch(
    templateId,
    newTemplateId => {
      if (newTemplateId) {
        clearErrors();
        loadValidationRules(newTemplateId);
      }
    },
    { immediate: true }
  );

  // Auto-validation on form data changes (debounced)
  watch(
    formData,
    () => {
      if (Object.keys(validationErrors.value).length > 0) {
        // Only re-validate if there are existing errors
        clearTimeout(debounceTimeout.value);
        debounceTimeout.value = setTimeout(() => {
          validateForm();
        }, 1000);
      }
    },
    { deep: true }
  );

  return {
    // State
    validationErrors,
    validationRules,
    isValidating,
    lastValidation,

    // Computed
    isFormValid,
    hasErrors,
    errorCount,
    getFieldErrors,
    hasFieldError,

    // Methods
    validateForm,
    validateField,
    validateFieldDebounced,
    validateFieldClient,
    loadValidationRules,
    clearErrors,
    clearFieldError,
    setFieldError,
    addFieldError,
  };
}

// Helper functions for CPF/CNPJ validation
function isValidCpf(cpf) {
  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) {
    return false;
  }

  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(cpf.charAt(i)) * (10 - i);
  }

  let digit = 11 - (sum % 11);
  if (digit === 10 || digit === 11) {digit = 0;}
  if (digit !== parseInt(cpf.charAt(9))) {return false;}

  sum = 0;
  for (let i = 0; i < 10; i++) {
    sum += parseInt(cpf.charAt(i)) * (11 - i);
  }

  digit = 11 - (sum % 11);
  if (digit === 10 || digit === 11) {digit = 0;}
  if (digit !== parseInt(cpf.charAt(10))) {return false;}

  return true;
}

function isValidCnpj(cnpj) {
  if (cnpj.length !== 14 || /^(\d)\1{13}$/.test(cnpj)) {
    return false;
  }

  const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const weights2 = [6, 7, 8, 9, 2, 3, 4, 5, 6, 7, 8, 9];

  let sum = 0;
  for (let i = 0; i < 12; i++) {
    sum += parseInt(cnpj.charAt(i)) * weights1[i];
  }

  let digit = sum % 11;
  digit = digit < 2 ? 0 : 11 - digit;
  if (digit !== parseInt(cnpj.charAt(12))) {return false;}

  sum = 0;
  for (let i = 0; i < 13; i++) {
    sum += parseInt(cnpj.charAt(i)) * weights2[i];
  }

  digit = sum % 11;
  digit = digit < 2 ? 0 : 11 - digit;
  if (digit !== parseInt(cnpj.charAt(13))) {return false;}

  return true;
}

// Validation presets for common field types
export const validationPresets = {
  cliente: {
    nome: ['required', { type: 'minLength', params: 2 }],
    cpf: ['required', 'cpf'],
    email: ['email'],
    telefone: ['phone'],
  },

  endereco: {
    logradouro: ['required'],
    numero: ['required'],
    bairro: ['required'],
    cidade: ['required'],
    estado: ['required'],
    cep: ['required', 'cep'],
  },

  processo: {
    numero_processo: ['required'],
    data_infracao: ['required'],
    artigo: ['required'],
  },

  autoridade: {
    nome: ['required'],
    cnpj: ['cnpj'],
    cidade: ['required'],
    estado: ['required'],
  },
};

export default useFormValidation;
