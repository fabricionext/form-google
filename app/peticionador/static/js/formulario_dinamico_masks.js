/**
 * Máscaras para formulários dinâmicos
 * Aplicadas automaticamente aos campos de CPF, CNPJ, CEP e telefone
 */

document.addEventListener('DOMContentLoaded', function () {
  // Aplicar máscaras iniciais
  aplicarMascarasFormulario();

  // Observar mudanças no DOM para aplicar máscaras em novos elementos
  const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === Node.ELEMENT_NODE) {
            aplicarMascarasFormulario(node);
          }
        });
      }
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
});

function aplicarMascarasFormulario(scope = document) {
  // Máscara para CPF
  const cpfFields = scope.querySelectorAll(
    'input[name*="cpf"], input[name*="_cpf"], .cpf-mask, [data-mask="cpf"]'
  );
  cpfFields.forEach(field => {
    if (!field._maskApplied) {
      field.addEventListener('input', mascaraCPF);
      field._maskApplied = true;
    }
  });

  // Máscara para CNPJ
  const cnpjFields = scope.querySelectorAll(
    'input[name*="cnpj"], input[name*="_cnpj"], .cnpj-mask, [data-mask="cnpj"]'
  );
  cnpjFields.forEach(field => {
    if (!field._maskApplied) {
      field.addEventListener('input', mascaraCNPJ);
      field._maskApplied = true;
    }
  });

  // Máscara para CEP
  const cepFields = scope.querySelectorAll(
    'input[name*="cep"], input[name*="_cep"], .cep-mask, [data-mask="cep"]'
  );
  cepFields.forEach(field => {
    if (!field._maskApplied) {
      field.addEventListener('input', mascaraCEP);
      field._maskApplied = true;
    }
  });

  // Máscara para telefone
  const telefoneFields = scope.querySelectorAll(
    'input[name*="telefone"], input[name*="celular"], .phone-mask, [data-mask="telefone"]'
  );
  telefoneFields.forEach(field => {
    if (!field._maskApplied) {
      field.addEventListener('input', mascaraTelefone);
      field._maskApplied = true;
    }
  });
}

function mascaraCPF(e) {
  // Verificar se as máscaras estão desabilitadas para este campo
  if (e.target._maskDisabled) {return;}

  let valor = e.target.value.replace(/\D/g, '');
  valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
  valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
  valor = valor.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  e.target.value = valor;
}

function mascaraCNPJ(e) {
  // Verificar se as máscaras estão desabilitadas para este campo
  if (e.target._maskDisabled) {return;}

  let valor = e.target.value.replace(/\D/g, '');
  valor = valor.replace(/(\d{2})(\d)/, '$1.$2');
  valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
  valor = valor.replace(/(\d{3})(\d)/, '$1/$2');
  valor = valor.replace(/(\d{4})(\d{1,2})$/, '$1-$2');
  e.target.value = valor;
}

function mascaraCEP(e) {
  // Verificar se as máscaras estão desabilitadas para este campo
  if (e.target._maskDisabled) {return;}

  let valor = e.target.value.replace(/\D/g, '');
  valor = valor.replace(/(\d{5})(\d)/, '$1-$2');
  e.target.value = valor;
}

function mascaraTelefone(e) {
  // Verificar se as máscaras estão desabilitadas para este campo
  if (e.target._maskDisabled) {return;}

  let valor = e.target.value.replace(/\D/g, '');
  if (valor.length <= 10) {
    // Telefone fixo
    valor = valor.replace(/(\d{2})(\d)/, '($1) $2');
    valor = valor.replace(/(\d{4})(\d)/, '$1-$2');
  } else {
    // Celular
    valor = valor.replace(/(\d{2})(\d)/, '($1) $2');
    valor = valor.replace(/(\d{5})(\d)/, '$1-$2');
  }
  e.target.value = valor;
}

// Exportar para uso global
window.aplicarMascarasFormulario = aplicarMascarasFormulario;
