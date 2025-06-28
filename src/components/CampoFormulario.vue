<template>
  <div
    class="campo-formulario"
    :class="{ 'campo-obrigatorio': campo.obrigatorio }"
  >
    <!-- Label -->
    <label
      :for="campo.chave"
      class="form-label"
      :class="{ required: campo.obrigatorio }"
    >
      {{ campo.label }}
      <span v-if="campo.obrigatorio" class="text-danger">*</span>
    </label>

    <!-- Campo de Input baseado no tipo -->
    <component
      :is="componenteInput"
      :id="campo.chave"
      :name="campo.chave"
      v-model="valorInterno"
      :class="classesInput"
      :placeholder="campo.placeholder_text || campo.label"
      :required="campo.obrigatorio"
      :type="tipoInput"
      :rows="campo.tipo === 'textarea' ? 3 : undefined"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
    />

    <!-- Feedback de validação -->
    <div v-if="erro" class="invalid-feedback d-block">
      {{ erro }}
    </div>

    <!-- Texto de ajuda -->
    <div v-if="textoAjuda" class="form-text">
      {{ textoAjuda }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  campo: {
    type: Object,
    required: true,
  },
  valor: {
    type: [String, Number],
    default: '',
  },
});

const emit = defineEmits(['atualizado']);

// Estado local
const valorInterno = ref(props.valor);
const erro = ref('');
const focado = ref(false);

// Watchers
watch(
  () => props.valor,
  novoValor => {
    valorInterno.value = novoValor;
  }
);

// Computed
const componenteInput = computed(() => {
  return props.campo.tipo === 'textarea' ? 'textarea' : 'input';
});

const tipoInput = computed(() => {
  const tipos = {
    text: 'text',
    email: 'email',
    tel: 'tel',
    date: 'date',
    number: 'number',
    password: 'password',
    url: 'url',
  };
  return tipos[props.campo.tipo] || 'text';
});

const classesInput = computed(() => {
  const classes = ['form-control'];

  if (erro.value) {
    classes.push('is-invalid');
  } else if (valorInterno.value && !focado.value) {
    classes.push('is-valid');
  }

  // Classes especiais baseadas no tipo de campo
  if (props.campo.chave.includes('cpf') || props.campo.chave.includes('cnpj')) {
    classes.push('mask-documento');
  } else if (
    props.campo.chave.includes('telefone') ||
    props.campo.chave.includes('celular')
  ) {
    classes.push('mask-telefone');
  } else if (props.campo.chave.includes('cep')) {
    classes.push('mask-cep');
  }

  return classes;
});

const textoAjuda = computed(() => {
  const ajudas = {
    cpf: 'Digite apenas números (ex: 12345678901)',
    cnpj: 'Digite apenas números (ex: 12345678000123)',
    telefone: 'Digite com DDD (ex: 11987654321)',
    celular: 'Digite com DDD (ex: 11987654321)',
    cep: 'Digite apenas números (ex: 01234567)',
    email: 'Digite um email válido (ex: exemplo@email.com)',
    data: 'Formato: DD/MM/AAAA',
  };

  for (const [tipo, texto] of Object.entries(ajudas)) {
    if (props.campo.chave.includes(tipo)) {
      return texto;
    }
  }

  return null;
});

// Métodos
const handleInput = event => {
  let valor = event.target.value;

  // Aplicar máscaras
  valor = aplicarMascara(valor);

  // Atualizar valor interno
  valorInterno.value = valor;

  // Validar
  validarCampo(valor);

  // Emitir evento
  emit('atualizado', { chave: props.campo.chave, valor });
};

const handleBlur = () => {
  focado.value = false;
  validarCampo(valorInterno.value);
};

const handleFocus = () => {
  focado.value = true;
  erro.value = ''; // Limpar erro ao focar
};

const aplicarMascara = valor => {
  if (!valor) return valor;

  // Remover caracteres não numéricos para máscaras
  const apenasNumeros = valor.replace(/\D/g, '');

  if (props.campo.chave.includes('cpf')) {
    return mascaraCPF(apenasNumeros);
  } else if (props.campo.chave.includes('cnpj')) {
    return mascaraCNPJ(apenasNumeros);
  } else if (
    props.campo.chave.includes('telefone') ||
    props.campo.chave.includes('celular')
  ) {
    return mascaraTelefone(apenasNumeros);
  } else if (props.campo.chave.includes('cep')) {
    return mascaraCEP(apenasNumeros);
  }

  return valor;
};

const mascaraCPF = valor => {
  return valor
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
};

const mascaraCNPJ = valor => {
  return valor
    .slice(0, 14)
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2');
};

const mascaraTelefone = valor => {
  if (valor.length <= 10) {
    return valor
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2');
  } else {
    return valor
      .slice(0, 11)
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{5})(\d)/, '$1-$2');
  }
};

const mascaraCEP = valor => {
  return valor.slice(0, 8).replace(/(\d{5})(\d)/, '$1-$2');
};

const validarCampo = valor => {
  erro.value = '';

  // Validação de campo obrigatório
  if (props.campo.obrigatorio && !valor.trim()) {
    erro.value = `${props.campo.label} é obrigatório`;
    return false;
  }

  // Validações específicas por tipo
  if (valor) {
    if (props.campo.tipo === 'email' && !validarEmail(valor)) {
      erro.value = 'Email inválido';
      return false;
    }

    if (props.campo.chave.includes('cpf') && !validarCPF(valor)) {
      erro.value = 'CPF inválido';
      return false;
    }

    if (props.campo.chave.includes('cnpj') && !validarCNPJ(valor)) {
      erro.value = 'CNPJ inválido';
      return false;
    }
  }

  return true;
};

const validarEmail = email => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
};

const validarCPF = cpf => {
  const numeros = cpf.replace(/\D/g, '');
  if (numeros.length !== 11) return false;

  // Verificar se todos os dígitos são iguais
  if (/^(\d)\1{10}$/.test(numeros)) return false;

  // Validar dígitos verificadores
  let soma = 0;
  for (let i = 0; i < 9; i++) {
    soma += parseInt(numeros[i]) * (10 - i);
  }

  let resto = soma % 11;
  const digito1 = resto < 2 ? 0 : 11 - resto;

  if (parseInt(numeros[9]) !== digito1) return false;

  soma = 0;
  for (let i = 0; i < 10; i++) {
    soma += parseInt(numeros[i]) * (11 - i);
  }

  resto = soma % 11;
  const digito2 = resto < 2 ? 0 : 11 - resto;

  return parseInt(numeros[10]) === digito2;
};

const validarCNPJ = cnpj => {
  const numeros = cnpj.replace(/\D/g, '');
  if (numeros.length !== 14) return false;

  // Verificar se todos os dígitos são iguais
  if (/^(\d)\1{13}$/.test(numeros)) return false;

  // Validar primeiro dígito verificador
  const pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  let soma = 0;

  for (let i = 0; i < 12; i++) {
    soma += parseInt(numeros[i]) * pesos1[i];
  }

  let resto = soma % 11;
  const digito1 = resto < 2 ? 0 : 11 - resto;

  if (parseInt(numeros[12]) !== digito1) return false;

  // Validar segundo dígito verificador
  const pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  soma = 0;

  for (let i = 0; i < 13; i++) {
    soma += parseInt(numeros[i]) * pesos2[i];
  }

  resto = soma % 11;
  const digito2 = resto < 2 ? 0 : 11 - resto;

  return parseInt(numeros[13]) === digito2;
};
</script>

<style scoped>
.campo-formulario {
  margin-bottom: 1rem;
}

.campo-obrigatorio .form-label::after {
  content: ' *';
  color: #dc3545;
}

.form-label.required {
  font-weight: 600;
}

.form-control {
  transition: all 0.3s ease;
}

.form-control:focus {
  border-color: #4e73df;
  box-shadow: 0 0 0 0.2rem rgba(78, 115, 223, 0.25);
}

.is-valid {
  border-color: #28a745;
}

.is-invalid {
  border-color: #dc3545;
}

.invalid-feedback {
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.form-text {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

/* Animações para feedback */
.invalid-feedback {
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-5px);
  }
  75% {
    transform: translateX(5px);
  }
}

/* Estilos responsivos */
@media (max-width: 576px) {
  .form-control {
    font-size: 16px; /* Evitar zoom no iOS */
  }
}
</style>
