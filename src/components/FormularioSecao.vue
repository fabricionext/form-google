<template>
  <div class="formulario-secao mb-4">
    <!-- Cabeçalho da Seção -->
    <div class="secao-header">
      <h5 class="secao-titulo" :class="secaoClasses">
        <i :class="secaoIcon"></i>
        {{ secaoTitulo }}
        <span v-if="totalCampos > 0" class="badge badge-light ms-2">
          {{ totalCampos }}
        </span>
      </h5>
      <button
        v-if="totalCampos > 0"
        @click="toggleSecao"
        class="btn btn-sm btn-outline-secondary"
        type="button"
      >
        <i
          :class="[
            secaoExpandida ? 'fas fa-chevron-up' : 'fas fa-chevron-down',
          ]"
        ></i>
      </button>
    </div>

    <!-- Conteúdo da Seção -->
    <div v-show="secaoExpandida" class="secao-content">
      <div class="card">
        <div class="card-body">
          <!-- Seção de Autores (tratamento especial) -->
          <div v-if="secao === 'autores'" class="autores-container">
            <div
              v-for="(autorData, autorIndex) in campos"
              :key="autorIndex"
              class="autor-group mb-4"
            >
              <AutorSecao
                :autor-index="autorIndex"
                :autor-data="autorData"
                :form-data="formData"
                @campo-atualizado="$emit('campo-atualizado', $event)"
              />
            </div>
          </div>

          <!-- Seções Regulares -->
          <div v-else class="campos-grid">
            <div
              v-for="campo in campos"
              :key="campo.chave"
              class="campo-container"
              :class="getFieldContainerClass(campo)"
            >
              <CampoFormulario
                :campo="campo"
                :valor="formData[campo.chave] || ''"
                @atualizado="handleCampoUpdate"
              />
            </div>
          </div>

          <!-- Drop Zone para Autoridades -->
          <div
            v-if="secao === 'autoridades'"
            class="authority-drop-zone"
            :data-authority-index="1"
            @drop="handleAuthorityDrop"
            @dragover.prevent
            @dragenter.prevent
          >
            <div class="drop-zone-content">
              <i class="fas fa-landmark fa-2x text-muted"></i>
              <p class="text-muted mt-2 mb-0">
                Arraste uma autoridade aqui para preencher automaticamente
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import CampoFormulario from './CampoFormulario.vue';
import AutorSecao from './AutorSecao.vue';

const props = defineProps({
  secao: {
    type: String,
    required: true,
  },
  campos: {
    type: [Array, Object],
    required: true,
  },
  formData: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['campo-atualizado']);

// Estado local
const secaoExpandida = ref(true);

// Computed
const totalCampos = computed(() => {
  if (props.secao === 'autores') {
    return Object.keys(props.campos).length;
  }
  return Array.isArray(props.campos) ? props.campos.length : 0;
});

const secaoTitulo = computed(() => {
  const titulos = {
    autores: 'Autores/Requerentes',
    cliente: 'Dados do Cliente',
    endereco: 'Endereço',
    processo: 'Dados do Processo',
    autoridades: 'Autoridades de Trânsito',
    polo_ativo: 'Polo Ativo',
    polo_passivo: 'Polo Passivo',
    terceiros: 'Terceiros',
    outros: 'Outros Campos',
  };
  return titulos[props.secao] || props.secao;
});

const secaoIcon = computed(() => {
  const icones = {
    autores: 'fas fa-user-friends',
    cliente: 'fas fa-user',
    endereco: 'fas fa-map-marker-alt',
    processo: 'fas fa-gavel',
    autoridades: 'fas fa-landmark',
    polo_ativo: 'fas fa-arrow-right',
    polo_passivo: 'fas fa-arrow-left',
    terceiros: 'fas fa-users',
    outros: 'fas fa-ellipsis-h',
  };
  return icones[props.secao] || 'fas fa-folder';
});

const secaoClasses = computed(() => {
  const classes = {
    autores: 'text-primary',
    cliente: 'text-info',
    endereco: 'text-success',
    processo: 'text-warning',
    autoridades: 'text-danger',
    polo_ativo: 'text-primary',
    polo_passivo: 'text-secondary',
    terceiros: 'text-info',
    outros: 'text-muted',
  };
  return classes[props.secao] || 'text-dark';
});

// Métodos
const toggleSecao = () => {
  secaoExpandida.value = !secaoExpandida.value;
};

const handleCampoUpdate = ({ chave, valor }) => {
  emit('campo-atualizado', { chave, valor });
};

const getFieldContainerClass = campo => {
  // Determinar classes baseadas no tipo de campo
  const classes = ['col-md-6'];

  if (campo.tipo === 'textarea') {
    classes.push('col-md-12');
  }

  if (campo.chave.includes('endereco')) {
    classes.push('endereco-field');
  }

  return classes.join(' ');
};

const handleAuthorityDrop = event => {
  event.preventDefault();

  try {
    const autoridadeData = JSON.parse(
      event.dataTransfer.getData('application/json')
    );
    const authorityIndex = event.currentTarget.dataset.authorityIndex;

    emit('autoridade-selecionada', { autoridadeData, index: authorityIndex });
  } catch (error) {
    console.error('Erro ao processar drop de autoridade:', error);
  }
};
</script>

<style scoped>
.formulario-secao {
  border: 1px solid #e3e6f0;
  border-radius: 0.5rem;
  overflow: hidden;
}

.secao-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, #f8f9fc 0%, #e3e6f0 100%);
  border-bottom: 1px solid #e3e6f0;
}

.secao-titulo {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.secao-content {
  animation: slideDown 0.3s ease;
}

.campos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.campo-container {
  margin-bottom: 1rem;
}

.autor-group {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 1rem;
  background-color: #f8f9fa;
}

.autores-container {
  space-y: 1rem;
}

.authority-drop-zone {
  min-height: 100px;
  border: 2px dashed #dee2e6;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1rem;
  transition: all 0.3s ease;
}

.authority-drop-zone:hover,
.authority-drop-zone.drop-target {
  border-color: #f6c23e;
  background-color: #fffbf0;
}

.drop-zone-content {
  text-align: center;
  padding: 1rem;
}

/* Responsividade */
@media (max-width: 768px) {
  .campos-grid {
    grid-template-columns: 1fr;
  }

  .secao-header {
    padding: 0.75rem 1rem;
  }

  .secao-titulo {
    font-size: 1rem;
  }
}

/* Animações */
@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
  }
}

/* Estados especiais */
.endereco-field {
  border-left: 3px solid #28a745;
}

.campo-obrigatorio {
  border-left: 3px solid #dc3545;
}

/* Badge customizado */
.badge {
  background-color: rgba(255, 255, 255, 0.8) !important;
  color: #333 !important;
}
</style>
