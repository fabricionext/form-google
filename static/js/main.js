// main.js - Lógica do frontend ADV
// Autor: Windsurf AI + Estevão
// Refatorado por Windsurf AI para UX, acessibilidade e segurança aprimoradas

// --- Máscaras ---
function maskCNPJ(v) {
  return v
    .replace(/\D/g, '')
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2')
    .slice(0, 18);
}
function maskCPF(v) {
  return v
    .replace(/\D/g, '')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}
function maskCEP(v) {
  return v
    .replace(/\D/g, '')
    .replace(/(\d{5})(\d)/, '$1-$2')
    .slice(0, 9);
}
function maskPhone(v) {
  v = v.replace(/\D/g, '');
  if (v.length <= 10)
    return v.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3').replace(/-$/, '');
  return v.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3').replace(/-$/, '');
}
function maskRG(v) {
  return v
    .replace(/\D/g, '')
    .replace(/(\d{2})(\d{3})(\d{3})([\dXx]{1})/, '$1.$2.$3-$4')
    .slice(0, 12);
}
function maskCNH(v) {
  return v.replace(/\D/g, '').slice(0, 11);
}

// --- Acessibilidade: foco visível ---
document.addEventListener('keydown', function (e) {
  if (e.key === 'Tab') document.body.classList.add('user-is-tabbing');
});
document.addEventListener('mousedown', function () {
  document.body.classList.remove('user-is-tabbing');
});

// --- Inicialização ---
document.addEventListener('DOMContentLoaded', () => {
  setLoading(false);

  // --- Máscaras de campos ---
  applyInputMasks();

  // --- Contador de caracteres ---
  applyCharCounters();

  // --- Validação em tempo real e feedback visual ---
  setupRealtimeValidation();

  // --- Progresso detalhado ---
  document
    .querySelectorAll('#clientForm input, #clientForm select')
    .forEach(input => {
      input.addEventListener('input', updateProgress);
      input.addEventListener('blur', updateProgress);
    });
  updateProgress();

  // --- Foco automático no primeiro campo ---
  const firstField = document.querySelector(
    '#clientForm input, #clientForm select'
  );
  if (firstField) firstField.focus();

  // --- Botão fixo mobile ---
  fixMobileSubmitButton();

  // --- Limitação de tentativas de envio ---
  let submitAttempts = 0;
  const MAX_ATTEMPTS = 5;

  // --- Lógica de Toggle PF/PJ ---
  const tipoPessoaPF = document.getElementById('tipoPessoaPF');
  const tipoPessoaPJ = document.getElementById('tipoPessoaPJ');
  const camposPessoaFisicaDiv = document.getElementById('camposPessoaFisica');
  const camposPessoaJuridicaDiv = document.getElementById(
    'camposPessoaJuridica'
  );

  const pfRequiredIds = [
    'primeiroNome',
    'sobrenome',
    'cpf',
    'email',
    'telefoneCelular',
    'cep',
    'logradouro',
    'numero',
    'bairro',
    'cidade',
    'estado',
  ];
  const pjRequiredIds = [
    'razaoSocial',
    'cnpj',
    'nomeRepresentante',
    'cpfRepresentante',
    'email',
    'telefoneCelular',
    'cep',
    'logradouro',
    'numero',
    'bairro',
    'cidade',
    'estado',
  ];

  function clearAllValidationFeedback() {
    document
      .querySelectorAll('#clientForm .error-message, #clientForm .success-icon')
      .forEach(el => el.remove());
    document
      .querySelectorAll('#clientForm input, #clientForm select')
      .forEach(el => {
        el.classList.remove('error', 'success');
        el.removeAttribute('aria-invalid');
      });
  }

  function toggleTipoPessoaFields() {
    const isPF = tipoPessoaPF.checked;

    camposPessoaFisicaDiv.style.display = isPF ? '' : 'none';
    camposPessoaJuridicaDiv.style.display = isPF ? 'none' : '';

    // Limpa validações ao trocar o tipo, pois os campos required mudam
    clearAllValidationFeedback();

    // Habilita/desabilita campos e ajusta 'required'
    camposPessoaFisicaDiv.querySelectorAll('input, select').forEach(input => {
      input.disabled = !isPF;
      if (pfRequiredIds.includes(input.id)) {
        isPF
          ? input.setAttribute('required', '')
          : input.removeAttribute('required');
      } else {
        input.removeAttribute('required'); // Garante que não requeridos não tenham o atributo
      }
    });

    camposPessoaJuridicaDiv.querySelectorAll('input, select').forEach(input => {
      input.disabled = isPF;
      if (pjRequiredIds.includes(input.id)) {
        !isPF
          ? input.setAttribute('required', '')
          : input.removeAttribute('required');
      } else {
        input.removeAttribute('required');
      }
    });

    // As máscaras são aplicadas uma vez no DOMContentLoaded e os listeners permanecem ativos.
    updateProgress(); // Atualiza a barra de progresso com base nos novos campos required
  }

  if (
    tipoPessoaPF &&
    tipoPessoaPJ &&
    camposPessoaFisicaDiv &&
    camposPessoaJuridicaDiv
  ) {
    tipoPessoaPF.addEventListener('change', toggleTipoPessoaFields);
    tipoPessoaPJ.addEventListener('change', toggleTipoPessoaFields);
    toggleTipoPessoaFields(); // Configuração inicial
  }

  // --- Submissão do formulário ---
  document
    .getElementById('clientForm')
    .addEventListener('submit', function (e) {
      e.preventDefault();
      if (!validateForm()) {
        showToast(
          'Corrija os campos destacados antes de enviar.',
          'error',
          4000
        );
        return;
      }
      submitAttempts++;
      if (submitAttempts > MAX_ATTEMPTS) {
        showToast(
          'Muitas tentativas. Aguarde antes de tentar novamente.',
          'warning',
          6000
        );
        return;
      }
      setLoading(true);
      showToast('Enviando dados...', 'info', 2000);
      const form = e.target;
      const formData = new FormData(form);
      const data = Object.fromEntries(formData.entries());

      // Compatibilidade: monta campo 'endereco' legado se necessário
      if (!data.endereco && data.logradouro) {
        data.endereco = `${data.logradouro}${data.numero ? ', ' + data.numero : ''}${data.complemento ? ', ' + data.complemento : ''}`;
      }
      // --- Resumo antes do envio ---
      if (!confirmSubmission(data)) {
        setLoading(false);
        return;
      }

      // Prepara o payload no formato esperado pelo backend
      const selectedTipoPessoa = document
        .querySelector('input[name="tipoPessoa"]:checked')
        .value.toLowerCase();
      const payload = {
        tipoPessoa: selectedTipoPessoa,
        dadosCliente: data,
      };

      console.log('Payload enviado:', JSON.stringify(payload, null, 2));

      fetch('/api/gerar-documento', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
        .then(async resp => {
          setLoading(false);
          if (!resp.ok)
            throw new Error('Erro ao processar. Tente novamente mais tarde.');
          return resp.json();
        })
        .then(result => {
          showToast('Documento gerado com sucesso!', 'success');
          if (result && result.link) {
            const link = document.createElement('a');
            link.href = result.link;
            link.textContent = 'Acessar documento gerado';
            link.target = '_blank';
            link.className = 'btn btn-primary mt-xl';
            document.querySelector('.app-container').appendChild(link);
          }
          form.reset();
          updateProgress();
        })
        .catch(() => {
          setLoading(false);
          showToast(
            'Erro ao cadastrar/generar documento. Tente novamente.',
            'error',
            6000
          );
        });
    });
});

// --- Funções auxiliares ---

function applyInputMasks() {
  if (document.getElementById('cpf'))
    document
      .getElementById('cpf')
      .addEventListener(
        'input',
        e => (e.target.value = maskCPF(e.target.value))
      );
  if (document.getElementById('cnpj'))
    document
      .getElementById('cnpj')
      .addEventListener(
        'input',
        e => (e.target.value = maskCNPJ(e.target.value))
      );
  if (document.getElementById('cpfRepresentante'))
    document
      .getElementById('cpfRepresentante')
      .addEventListener(
        'input',
        e => (e.target.value = maskCPF(e.target.value))
      );
  const cep = document.getElementById('cep');
  if (cep) {
    cep.addEventListener('input', function () {
      this.value = maskCEP(this.value);
    });
    cep.addEventListener('blur', () => {
      if (cep.value.replace(/\D/g, '').length === 8) {
        fetch(`/api/cep/${cep.value.replace(/\D/g, '')}`)
          .then(r => r.json())
          .then(data => {
            if (data && !data.erro) {
              document.getElementById('logradouro').value =
                data.logradouro || '';
              document.getElementById('bairro').value = data.bairro || '';
              document.getElementById('cidade').value = data.localidade || '';
              document.getElementById('estado').value = data.uf || '';
              document.getElementById('complemento').value =
                data.complemento || '';
            }
          });
      }
    });
  }
  const tel1 = document.getElementById('telefoneCelular');
  if (tel1) {
    tel1.addEventListener('input', function () {
      this.value = maskPhone(this.value);
    });
  }
  const tel2 = document.getElementById('outroTelefone');
  if (tel2) {
    tel2.addEventListener('input', function () {
      this.value = maskPhone(this.value);
    });
  }
  const rg = document.getElementById('rg');
  if (rg) {
    rg.addEventListener('input', function () {
      this.value = maskRG(this.value);
    });
  }
  const cnh = document.getElementById('cnh');
  if (cnh) {
    cnh.addEventListener('input', function () {
      this.value = maskCNH(this.value);
    });
  }
}

function applyCharCounters() {
  document
    .querySelectorAll(
      '#clientForm input[maxlength], #clientForm textarea[maxlength]'
    )
    .forEach(input => {
      const counter = input.parentElement.querySelector('.character-count');
      if (counter) {
        const update = () => {
          counter.textContent = `${input.value.length}/${input.maxLength}`;
        };
        input.addEventListener('input', update);
        update();
      }
    });
}

function setupRealtimeValidation() {
  document
    .querySelectorAll('#clientForm input, #clientForm select')
    .forEach(input => {
      input.addEventListener('input', () => validateField(input));
      input.addEventListener('blur', () => validateField(input));
    });
}

function validateField(input) {
  const value = input.value.trim();
  const isRequired = input.hasAttribute('required');
  let valid = true,
    msg = '';
  if (isRequired && !value) {
    valid = false;
    msg = 'Campo obrigatório';
  }
  if (input.type === 'email' && value) {
    valid = /^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$/.test(value);
    if (!valid) msg = 'E-mail inválido';
  }
  if (input.id === 'cpf' && value) {
    valid = /^\d{3}\.\d{3}\.\d{3}-\d{2}$/.test(value);
    if (!valid) msg = 'CPF inválido';
  }
  if (input.id === 'cep' && value) {
    valid = /^\d{5}-\d{3}$/.test(value);
    if (!valid) msg = 'CEP inválido';
  }
  if (input.id === 'telefoneCelular' && value) {
    valid = /^\(\d{2}\) \d{5}-\d{4}$/.test(value);
    if (!valid) msg = 'Celular inválido';
  }
  // Visual feedback
  input.classList.toggle('error', !valid);
  input.classList.toggle('success', valid && value);
  let errorMsg = input.parentElement.querySelector('.error-message');
  if (!valid) {
    if (!errorMsg) {
      errorMsg = document.createElement('div');
      errorMsg.className = 'error-message';
      input.parentElement.appendChild(errorMsg);
    }
    errorMsg.textContent = msg;
    input.setAttribute('aria-invalid', 'true');
  } else {
    if (errorMsg) errorMsg.remove();
    input.removeAttribute('aria-invalid');
  }
  // Ícone sucesso
  let icon = input.parentElement.querySelector('.success-icon');
  if (valid && value) {
    if (!icon) {
      icon = document.createElement('span');
      icon.className = 'success-icon';
      icon.innerHTML = '<i class="fas fa-check-circle"></i>';
      input.parentElement.appendChild(icon);
    }
  } else {
    if (icon) icon.remove();
  }
  return valid;
}

function validateForm() {
  let valid = true;
  document
    .querySelectorAll('#clientForm input, #clientForm select')
    .forEach(input => {
      if (!validateField(input)) valid = false;
    });
  return valid;
}

function confirmSubmission(data) {
  // Adiciona o tipo de pessoa aos dados para uso na confirmação
  const tipoPessoaSelecionado = document.querySelector(
    'input[name="tipoPessoa"]:checked'
  ).value;

  let msg = 'Confirme seus dados antes de enviar:\n';
  msg += `Tipo de Cadastro: ${tipoPessoaSelecionado === 'PF' ? 'Pessoa Física' : 'Pessoa Jurídica'}\n\n`;

  if (tipoPessoaSelecionado === 'PF') {
    msg += `Nome Completo: ${data.primeiroNome || ''} ${data.sobrenome || ''}\n`;
    msg += `CPF: ${data.cpf || ''}\n`;
  } else {
    // PJ
    msg += `Razão Social: ${data.razaoSocial || ''}\n`;
    msg += `CNPJ: ${data.cnpj || ''}\n`;
    msg += `Nome do Representante: ${data.nomeRepresentante || ''}\n`;
    msg += `CPF do Representante: ${data.cpfRepresentante || ''}\n`;
  }

  msg += `\n--- Contato ---\n`;
  msg += `E-mail: ${data.email || ''}\n`;
  msg += `Telefone Celular: ${data.telefoneCelular || ''}\n`;

  msg += `\n--- Endereço ---\n`;
  const enderecoCompleto = `${data.logradouro || ''}${data.numero ? ', ' + data.numero : ''}${data.complemento ? ' - ' + data.complemento : ''}`;
  msg += `Endereço: ${enderecoCompleto || 'N/A'}\n`;
  msg += `Bairro: ${data.bairro || ''}\n`;
  msg += `Cidade: ${data.cidade || ''} - ${data.estado || ''}\n`;
  msg += `CEP: ${data.cep || ''}\n`;

  return window.confirm(msg);
}

function fixMobileSubmitButton() {
  const submitBtn = document.getElementById('submitBtn');
  if (!submitBtn) return;
  function checkMobile() {
    if (window.innerWidth < 600) {
      submitBtn.style.position = 'fixed';
      submitBtn.style.bottom = '0';
      submitBtn.style.left = '0';
      submitBtn.style.width = '100vw';
      submitBtn.style.zIndex = '100';
      submitBtn.style.borderRadius = '0';
    } else {
      submitBtn.style.position = '';
      submitBtn.style.bottom = '';
      submitBtn.style.left = '';
      submitBtn.style.width = '';
      submitBtn.style.zIndex = '';
      submitBtn.style.borderRadius = '';
    }
  }
  window.addEventListener('resize', checkMobile);
  checkMobile();
}

// Funções utilitárias
function showToast(message, type = 'info', duration = 4000) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  setTimeout(() => {
    toast.className = 'toast';
  }, duration);
}

function setLoading(visible) {
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) {
    overlay.classList.toggle('active', visible);
  }
}

function updateProgress() {
  const progressBar = document.getElementById('progressBar');
  const required = document.querySelectorAll('#clientForm [required]');
  let filled = 0;
  required.forEach(input => {
    if (input.type === 'radio') {
      if (input.checked) filled++;
    } else if (input.value && input.value.trim() !== '') {
      filled++;
    }
  });
  const percent = Math.round((filled / required.length) * 100);
  progressBar.style.width = percent + '%';
  progressBar.setAttribute('data-progress', percent + '%');
  progressBar.setAttribute('aria-valuenow', percent);
}
