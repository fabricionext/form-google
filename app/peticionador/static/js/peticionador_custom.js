/**
 * JavaScript personalizado para o módulo Peticionador
 * Funcionalidades: máscaras de entrada, drag & drop, busca automática
 */

document.addEventListener('DOMContentLoaded', function () {
  initializeMasks();
  initializeFormValidation();
  initializeHelpers();
});

/**
 * Inicializa máscaras de entrada para os campos
 */
function initializeMasks() {
  // Máscara para CPF
  const cpfFields = document.querySelectorAll('.cpf-mask, input[name*="cpf"]');
  cpfFields.forEach(field => {
    field.addEventListener('input', function (e) {
      let value = e.target.value.replace(/\D/g, '');
      value = value.replace(/(\d{3})(\d)/, '$1.$2');
      value = value.replace(/(\d{3})(\d)/, '$1.$2');
      value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
      e.target.value = value;
    });
  });

  // Máscara para CNPJ
  const cnpjFields = document.querySelectorAll(
    '.cnpj-mask, input[name*="cnpj"]'
  );
  cnpjFields.forEach(field => {
    field.addEventListener('input', function (e) {
      let value = e.target.value.replace(/\D/g, '');
      value = value.replace(/(\d{2})(\d)/, '$1.$2');
      value = value.replace(/(\d{3})(\d)/, '$1.$2');
      value = value.replace(/(\d{3})(\d)/, '$1/$2');
      value = value.replace(/(\d{4})(\d{1,2})$/, '$1-$2');
      e.target.value = value;
    });
  });

  // Máscara para CEP
  const cepFields = document.querySelectorAll('.cep-mask, input[name*="cep"]');
  cepFields.forEach(field => {
    field.addEventListener('input', function (e) {
      let value = e.target.value.replace(/\D/g, '');
      value = value.replace(/(\d{5})(\d)/, '$1-$2');
      e.target.value = value;
    });

    // Busca automática de endereço por CEP
    field.addEventListener('blur', function (e) {
      const cep = e.target.value.replace(/\D/g, '');
      if (cep.length === 8) {
        buscarEnderecoPorCEP(cep);
      }
    });
  });

  // Máscara para telefone
  const phoneFields = document.querySelectorAll(
    '.phone-mask, input[name*="telefone"], input[name*="celular"]'
  );
  phoneFields.forEach(field => {
    field.addEventListener('input', function (e) {
      let value = e.target.value.replace(/\D/g, '');

      if (value.length <= 10) {
        // Telefone fixo: (11) 1234-5678
        value = value.replace(/(\d{2})(\d)/, '($1) $2');
        value = value.replace(/(\d{4})(\d)/, '$1-$2');
      } else {
        // Celular: (11) 91234-5678
        value = value.replace(/(\d{2})(\d)/, '($1) $2');
        value = value.replace(/(\d{5})(\d)/, '$1-$2');
      }
      e.target.value = value;
    });
  });

  // Máscara para RG
  const rgFields = document.querySelectorAll('.rg-mask, input[name*="rg"]');
  rgFields.forEach(field => {
    field.addEventListener('input', function (e) {
      let value = e.target.value.replace(/\D/g, '');
      value = value.replace(/(\d{2})(\d)/, '$1.$2');
      value = value.replace(/(\d{3})(\d)/, '$1.$2');
      value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
      e.target.value = value;
    });
  });

  // Máscara para CNH
  const cnhFields = document.querySelectorAll('.cnh-mask, input[name*="cnh"]');
  cnhFields.forEach(field => {
    field.addEventListener('input', function (e) {
      let value = e.target.value.replace(/\D/g, '');
      if (value.length > 11) {
        value = value.substring(0, 11);
      }
      e.target.value = value;
    });
  });
}

/**
 * Busca endereço automaticamente pelo CEP
 */
function buscarEnderecoPorCEP(cep) {
  const loadingIndicator = showLoading('Buscando endereço...');

  fetch(`https://viacep.com.br/ws/${cep}/json/`)
    .then(response => response.json())
    .then(data => {
      if (!data.erro) {
        preencherCamposEndereco(data);
        showSuccess('Endereço encontrado!');
      } else {
        showWarning('CEP não encontrado.');
      }
    })
    .catch(error => {
      console.error('Erro ao buscar CEP:', error);
      showError('Erro ao buscar CEP. Tente novamente.');
    })
    .finally(() => {
      hideLoading(loadingIndicator);
    });
}

/**
 * Preenche campos de endereço com dados do CEP
 */
function preencherCamposEndereco(dadosEndereco) {
  const fieldMappings = {
    logradouro: ['endereco_logradouro', 'logradouro'],
    bairro: ['endereco_bairro', 'bairro'],
    localidade: ['endereco_cidade', 'cidade'],
    uf: ['endereco_estado', 'estado', 'uf'],
  };

  Object.keys(fieldMappings).forEach(key => {
    if (dadosEndereco[key]) {
      fieldMappings[key].forEach(fieldName => {
        const field = document.querySelector(
          `input[name="${fieldName}"], select[name="${fieldName}"]`
        );
        if (field && !field.value) {
          field.value = dadosEndereco[key];
          field.dispatchEvent(new Event('change'));
        }
      });
    }
  });
}

/**
 * Inicializa validação de formulários
 */
function initializeFormValidation() {
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function (e) {
      // Pular validação para formulários de exclusão/desativação
      const deleteAction =
        this.action &&
        (this.action.includes('/excluir_') ||
          this.action.includes('/delete') ||
          this.action.includes('/remove'));
      const deleteButton =
        this.querySelector('button[class*="danger"]') ||
        this.querySelector('button[onclick*="confirm"]');

      if (deleteAction || deleteButton) {
        return true; // Permitir submit sem validação
      }

      if (!validateForm(this)) {
        e.preventDefault();
        return false;
      }
    });
  });
}

/**
 * Valida formulário
 */
function validateForm(form) {
  let isValid = true;
  const errors = [];

  // Validar CPF
  const cpfFields = form.querySelectorAll('input[name*="cpf"]');
  cpfFields.forEach(field => {
    if (field.value && !isValidCPF(field.value)) {
      errors.push('CPF inválido');
      markFieldAsInvalid(field);
      isValid = false;
    } else {
      markFieldAsValid(field);
    }
  });

  // Validar CNPJ
  const cnpjFields = form.querySelectorAll('input[name*="cnpj"]');
  cnpjFields.forEach(field => {
    if (field.value && !isValidCNPJ(field.value)) {
      errors.push('CNPJ inválido');
      markFieldAsInvalid(field);
      isValid = false;
    } else {
      markFieldAsValid(field);
    }
  });

  // Validar email
  const emailFields = form.querySelectorAll('input[type="email"]');
  emailFields.forEach(field => {
    if (field.value && !isValidEmail(field.value)) {
      errors.push('Email inválido');
      markFieldAsInvalid(field);
      isValid = false;
    } else {
      markFieldAsValid(field);
    }
  });

  if (!isValid) {
    showError(
      'Por favor, corrija os erros no formulário:<br>' + errors.join('<br>')
    );
  }

  return isValid;
}

/**
 * Validadores
 */
function isValidCPF(cpf) {
  cpf = cpf.replace(/\D/g, '');
  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) {return false;}

  let sum = 0;
  for (let i = 0; i < 9; i++) {sum += parseInt(cpf.charAt(i)) * (10 - i);}
  let rev = 11 - (sum % 11);
  if (rev === 10 || rev === 11) {rev = 0;}
  if (rev !== parseInt(cpf.charAt(9))) {return false;}

  sum = 0;
  for (let i = 0; i < 10; i++) {sum += parseInt(cpf.charAt(i)) * (11 - i);}
  rev = 11 - (sum % 11);
  if (rev === 10 || rev === 11) {rev = 0;}
  return rev === parseInt(cpf.charAt(10));
}

function isValidCNPJ(cnpj) {
  cnpj = cnpj.replace(/\D/g, '');
  if (cnpj.length !== 14) {return false;}

  const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

  let sum = 0;
  for (let i = 0; i < 12; i++) {sum += parseInt(cnpj.charAt(i)) * weights1[i];}
  let rev = sum % 11 < 2 ? 0 : 11 - (sum % 11);
  if (rev !== parseInt(cnpj.charAt(12))) {return false;}

  sum = 0;
  for (let i = 0; i < 13; i++) {sum += parseInt(cnpj.charAt(i)) * weights2[i];}
  rev = sum % 11 < 2 ? 0 : 11 - (sum % 11);
  return rev === parseInt(cnpj.charAt(13));
}

function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Marca campo como inválido
 */
function markFieldAsInvalid(field) {
  field.classList.add('is-invalid');
  field.classList.remove('is-valid');
}

/**
 * Marca campo como válido
 */
function markFieldAsValid(field) {
  field.classList.add('is-valid');
  field.classList.remove('is-invalid');
}

/**
 * Funções auxiliares para notificações
 */
function showLoading(message) {
  const loader = document.createElement('div');
  loader.className =
    'loading-indicator position-fixed top-50 start-50 translate-middle bg-primary text-white p-3 rounded';
  loader.style.zIndex = '9999';
  loader.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${message}`;
  document.body.appendChild(loader);
  return loader;
}

function hideLoading(loader) {
  if (loader && loader.parentNode) {
    loader.parentNode.removeChild(loader);
  }
}

function showSuccess(message) {
  showToast(message, 'success');
}

function showWarning(message) {
  showToast(message, 'warning');
}

function showError(message) {
  showToast(message, 'danger');
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed top-0 end-0 m-3`;
  toast.style.zIndex = '9999';
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

  document.body.appendChild(toast);

  const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
  bsToast.show();

  toast.addEventListener('hidden.bs.toast', function () {
    document.body.removeChild(toast);
  });
}

/**
 * Inicializa funcionalidades auxiliares
 */
function initializeHelpers() {
  // Auto-focus no primeiro campo visível
  const firstInput = document.querySelector(
    'input:not([type="hidden"]):not([readonly]), select:not([readonly]), textarea:not([readonly])'
  );
  if (firstInput) {
    setTimeout(() => firstInput.focus(), 100);
  }

  // Confirmação para ações destrutivas
  const deleteButtons = document.querySelectorAll(
    '.btn-danger, .btn-outline-danger, [data-action="delete"]'
  );
  deleteButtons.forEach(button => {
    button.addEventListener('click', function (e) {
      if (!confirm('Tem certeza que deseja executar esta ação?')) {
        e.preventDefault();
        return false;
      }
    });
  });

  // Melhorar acessibilidade
  const requiredFields = document.querySelectorAll('[required]');
  requiredFields.forEach(field => {
    const label = document.querySelector(`label[for="${field.id}"]`);
    if (label && !label.textContent.includes('*')) {
      label.innerHTML += ' <span class="text-danger">*</span>';
    }
  });
}

/**
 * Funções globais para uso em templates
 */
window.peticionadorUtils = {
  showLoading,
  hideLoading,
  showSuccess,
  showWarning,
  showError,
  showToast,
  isValidCPF,
  isValidCNPJ,
  isValidEmail,
  buscarEnderecoPorCEP,
};
