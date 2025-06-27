/**
 * Validadores para o Formulário Dinâmico
 * Sistema de validação em tempo real para melhorar UX
 */

class FormValidators {
  constructor() {
    this.patterns = {
      cpf: /^[0-9]{3}\.?[0-9]{3}\.?[0-9]{3}-?[0-9]{2}$/,
      cnpj: /^[0-9]{2}\.?[0-9]{3}\.?[0-9]{3}\/?[0-9]{4}-?[0-9]{2}$/,
      cep: /^[0-9]{5}-?[0-9]{3}$/,
      telefone: /^(\(?[0-9]{2}\)?\s?)?[0-9]{4,5}-?[0-9]{4}$/,
      email: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
      cnh: /^[0-9]{11}$/,
      rg: /^[0-9]{1,2}\.?[0-9]{3}\.?[0-9]{3}-?[0-9X]$/i,
    };

    this.messages = {
      required: 'Este campo é obrigatório',
      cpfInvalid: 'CPF inválido',
      cnpjInvalid: 'CNPJ inválido',
      emailInvalid: 'Email inválido',
      cepInvalid: 'CEP inválido',
      telefoneInvalid: 'Telefone inválido',
      cnhInvalid: 'CNH inválida',
      rgInvalid: 'RG inválido',
      minLength: 'Mínimo de {min} caracteres',
      maxLength: 'Máximo de {max} caracteres',
    };
  }

  /**
   * Valida CPF
   */
  validaCPF(cpf) {
    if (!cpf) return { valid: true, message: '' }; // Campo opcional

    const cleanCPF = cpf.replace(/\D/g, '');

    if (cleanCPF.length !== 11) {
      return { valid: false, message: this.messages.cpfInvalid };
    }

    // Verifica se todos os dígitos são iguais
    if (/^(\d)\1{10}$/.test(cleanCPF)) {
      return { valid: false, message: this.messages.cpfInvalid };
    }

    // Validação dos dígitos verificadores
    let sum = 0;
    for (let i = 0; i < 9; i++) {
      sum += parseInt(cleanCPF.charAt(i)) * (10 - i);
    }
    let digit1 = 11 - (sum % 11);
    if (digit1 > 9) digit1 = 0;

    sum = 0;
    for (let i = 0; i < 10; i++) {
      sum += parseInt(cleanCPF.charAt(i)) * (11 - i);
    }
    let digit2 = 11 - (sum % 11);
    if (digit2 > 9) digit2 = 0;

    const valid =
      digit1 === parseInt(cleanCPF.charAt(9)) &&
      digit2 === parseInt(cleanCPF.charAt(10));

    return {
      valid,
      message: valid ? '' : this.messages.cpfInvalid,
    };
  }

  /**
   * Valida CNPJ
   */
  validaCNPJ(cnpj) {
    if (!cnpj) return { valid: true, message: '' };

    const cleanCNPJ = cnpj.replace(/\D/g, '');

    if (cleanCNPJ.length !== 14) {
      return { valid: false, message: this.messages.cnpjInvalid };
    }

    // Algoritmo de validação do CNPJ
    const digits = cleanCNPJ.split('').map(Number);

    // Primeiro dígito verificador
    let sum = 0;
    const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    for (let i = 0; i < 12; i++) {
      sum += digits[i] * weights1[i];
    }
    const digit1 = sum % 11 < 2 ? 0 : 11 - (sum % 11);

    // Segundo dígito verificador
    sum = 0;
    const weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    for (let i = 0; i < 13; i++) {
      sum += digits[i] * weights2[i];
    }
    const digit2 = sum % 11 < 2 ? 0 : 11 - (sum % 11);

    const valid = digit1 === digits[12] && digit2 === digits[13];

    return {
      valid,
      message: valid ? '' : this.messages.cnpjInvalid,
    };
  }

  /**
   * Valida Email
   */
  validaEmail(email) {
    if (!email) return { valid: true, message: '' };

    const valid = this.patterns.email.test(email);
    return {
      valid,
      message: valid ? '' : this.messages.emailInvalid,
    };
  }

  /**
   * Valida CEP
   */
  validaCEP(cep) {
    if (!cep) return { valid: true, message: '' };

    const valid = this.patterns.cep.test(cep);
    return {
      valid,
      message: valid ? '' : this.messages.cepInvalid,
    };
  }

  /**
   * Valida Telefone
   */
  validaTelefone(telefone) {
    if (!telefone) return { valid: true, message: '' };

    const valid = this.patterns.telefone.test(telefone);
    return {
      valid,
      message: valid ? '' : this.messages.telefoneInvalid,
    };
  }

  /**
   * Valida CNH
   */
  validaCNH(cnh) {
    if (!cnh) return { valid: true, message: '' };

    const cleanCNH = cnh.replace(/\D/g, '');
    const valid = cleanCNH.length === 11;

    return {
      valid,
      message: valid ? '' : this.messages.cnhInvalid,
    };
  }

  /**
   * Valida RG
   */
  validaRG(rg) {
    if (!rg) return { valid: true, message: '' };

    const valid = this.patterns.rg.test(rg);
    return {
      valid,
      message: valid ? '' : this.messages.rgInvalid,
    };
  }

  /**
   * Valida campo obrigatório
   */
  validaObrigatorio(value, fieldName) {
    const valid = value && value.trim() !== '';
    return {
      valid,
      message: valid ? '' : this.messages.required,
    };
  }

  /**
   * Valida comprimento mínimo
   */
  validaComprimentoMinimo(value, min) {
    if (!value) return { valid: true, message: '' };

    const valid = value.length >= min;
    return {
      valid,
      message: valid ? '' : this.messages.minLength.replace('{min}', min),
    };
  }

  /**
   * Valida comprimento máximo
   */
  validaComprimentoMaximo(value, max) {
    if (!value) return { valid: true, message: '' };

    const valid = value.length <= max;
    return {
      valid,
      message: valid ? '' : this.messages.maxLength.replace('{max}', max),
    };
  }

  /**
   * Valida um campo baseado em seu tipo/nome
   */
  validaCampo(fieldName, value) {
    const validations = [];

    // Detectar tipo de campo pelo nome
    if (fieldName.includes('cpf')) {
      validations.push(this.validaCPF(value));
    } else if (fieldName.includes('cnpj')) {
      validations.push(this.validaCNPJ(value));
    } else if (fieldName.includes('email')) {
      validations.push(this.validaEmail(value));
    } else if (fieldName.includes('cep')) {
      validations.push(this.validaCEP(value));
    } else if (
      fieldName.includes('telefone') ||
      fieldName.includes('celular')
    ) {
      validations.push(this.validaTelefone(value));
    } else if (fieldName.includes('cnh')) {
      validations.push(this.validaCNH(value));
    } else if (fieldName.includes('rg') && !fieldName.includes('cargo')) {
      validations.push(this.validaRG(value));
    }

    // Validações específicas por campo
    if (fieldName.includes('nome') && value) {
      validations.push(this.validaComprimentoMinimo(value, 2));
      validations.push(this.validaComprimentoMaximo(value, 100));
    }

    // Retorna a primeira validação que falhou ou sucesso
    const failed = validations.find(v => !v.valid);
    return failed || { valid: true, message: '' };
  }

  /**
   * Adiciona listeners de validação a um formulário
   */
  setupFormValidation(formSelector) {
    const form = document.querySelector(formSelector);
    if (!form) return;

    const inputs = form.querySelectorAll('input, select, textarea');

    inputs.forEach(input => {
      // Validação em tempo real (blur)
      input.addEventListener('blur', e => {
        this.validateField(e.target);
      });

      // Validação durante digitação (debounced)
      let debounceTimer;
      input.addEventListener('input', e => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          this.validateField(e.target);
        }, 500);
      });
    });
  }

  /**
   * Valida um campo específico e mostra o resultado
   */
  validateField(field) {
    const fieldName = field.name;
    const value = field.value;

    const validation = this.validaCampo(fieldName, value);

    // Remove mensagens de erro anteriores
    this.clearFieldError(field);

    // Adiciona classe de validação
    field.classList.remove('is-valid', 'is-invalid');

    if (value) {
      // Só mostra validação se há conteúdo
      if (validation.valid) {
        field.classList.add('is-valid');
      } else {
        field.classList.add('is-invalid');
        this.showFieldError(field, validation.message);
      }
    }

    return validation;
  }

  /**
   * Mostra erro do campo
   */
  showFieldError(field, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    errorDiv.setAttribute('data-validation-error', 'true');

    // Inserir após o campo
    field.parentNode.appendChild(errorDiv);
  }

  /**
   * Remove erro do campo
   */
  clearFieldError(field) {
    const existingError = field.parentNode.querySelector(
      '[data-validation-error="true"]'
    );
    if (existingError) {
      existingError.remove();
    }
  }

  /**
   * Valida todo o formulário
   */
  validateForm(formSelector) {
    const form = document.querySelector(formSelector);
    if (!form) return { valid: false, errors: ['Formulário não encontrado'] };

    const inputs = form.querySelectorAll('input, select, textarea');
    const errors = [];
    let allValid = true;

    inputs.forEach(input => {
      const validation = this.validateField(input);
      if (!validation.valid) {
        allValid = false;
        errors.push(`${input.name}: ${validation.message}`);
      }
    });

    return {
      valid: allValid,
      errors,
    };
  }
}

// Instância global dos validadores
window.FormValidators = new FormValidators();
