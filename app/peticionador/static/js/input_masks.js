// Biblioteca IMask para máscaras de input
// Carrega IMask via CDN se não estiver disponível
if (typeof IMask === 'undefined') {
  const script = document.createElement('script');
  script.src = 'https://unpkg.com/imask@7.5.0/dist/imask.min.js';
  document.head.appendChild(script);
}

// Funções simples de máscara para CPF e CEP (vanilla JS)
// Aplica automaticamente ao ganhar foco em inputs com data-mask="cpf" ou "cep"

function aplicarMascaraCPF(valor) {
  return valor
    .replace(/\D/g, '') // remove tudo que não é dígito
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}

function aplicarMascaraCEP(valor) {
  return valor.replace(/\D/g, '').replace(/(\d{5})(\d)/, '$1-$2');
}

function aplicarMascaraTelefone(valor) {
  return valor
    .replace(/\D/g, '')
    .replace(/(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d)/, '$1-$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
}

function aplicarMascaraCNPJ(valor) {
  return valor
    .replace(/\D/g, '')
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
}

document.addEventListener('DOMContentLoaded', () => {
  // Máscaras com vanilla JS
  const cpfInputs = document.querySelectorAll('input[data-mask="cpf"]');
  cpfInputs.forEach(input => {
    input.addEventListener('input', e => {
      e.target.value = aplicarMascaraCPF(e.target.value);
    });
  });

  const cepInputs = document.querySelectorAll('input[data-mask="cep"]');
  cepInputs.forEach(input => {
    input.addEventListener('input', e => {
      e.target.value = aplicarMascaraCEP(e.target.value);
    });
  });

  const telefoneInputs = document.querySelectorAll(
    'input[data-mask="telefone"]'
  );
  telefoneInputs.forEach(input => {
    input.addEventListener('input', e => {
      e.target.value = aplicarMascaraTelefone(e.target.value);
    });
  });

  const cnpjInputs = document.querySelectorAll('input[data-mask="cnpj"]');
  cnpjInputs.forEach(input => {
    input.addEventListener('input', e => {
      e.target.value = aplicarMascaraCNPJ(e.target.value);
    });
  });

  // Máscaras com IMask (quando disponível)
  if (typeof IMask !== 'undefined') {
    // Máscara para CPF
    const cpfInputsIMask = document.querySelectorAll(
      'input[id*="cpf"], input[name*="cpf"]'
    );
    cpfInputsIMask.forEach(input => {
      if (!input.hasAttribute('data-mask')) {
        IMask(input, {
          mask: '000.000.000-00',
        });
      }
    });

    // Máscara para CEP
    const cepInputsIMask = document.querySelectorAll(
      'input[id*="cep"], input[name*="cep"]'
    );
    cepInputsIMask.forEach(input => {
      if (!input.hasAttribute('data-mask')) {
        IMask(input, {
          mask: '00000-000',
        });
      }
    });

    // Máscara para telefone
    const telefoneInputsIMask = document.querySelectorAll(
      'input[id*="telefone"], input[name*="telefone"]'
    );
    telefoneInputsIMask.forEach(input => {
      if (!input.hasAttribute('data-mask')) {
        IMask(input, {
          mask: '(00) 00000-0000',
        });
      }
    });

    // Máscara para CNPJ
    const cnpjInputsIMask = document.querySelectorAll(
      'input[id*="cnpj"], input[name*="cnpj"]'
    );
    cnpjInputsIMask.forEach(input => {
      if (!input.hasAttribute('data-mask')) {
        IMask(input, {
          mask: '00.000.000/0000-00',
        });
      }
    });
  }
});

// Função para aplicar máscaras em elementos específicos
function aplicarMascarasElementos() {
  if (typeof IMask !== 'undefined') {
    // Aplicar máscaras em elementos que podem ter sido criados dinamicamente
    const elementos = document.querySelectorAll('input[type="text"]');
    elementos.forEach(elemento => {
      const id = elemento.id || '';
      const name = elemento.name || '';

      if (id.includes('cpf') || name.includes('cpf')) {
        if (!elemento._imask) {
          IMask(elemento, { mask: '000.000.000-00' });
        }
      } else if (id.includes('cep') || name.includes('cep')) {
        if (!elemento._imask) {
          IMask(elemento, { mask: '00000-000' });
        }
      } else if (id.includes('telefone') || name.includes('telefone')) {
        if (!elemento._imask) {
          IMask(elemento, { mask: '(00) 00000-0000' });
        }
      } else if (id.includes('cnpj') || name.includes('cnpj')) {
        if (!elemento._imask) {
          IMask(elemento, { mask: '00.000.000/0000-00' });
        }
      }
    });
  }
}

// Exportar função para uso global
window.aplicarMascarasElementos = aplicarMascarasElementos;
