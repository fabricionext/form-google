<template>
  <div class="autor-secao">
    <div class="autor-header">
      <h6 class="autor-titulo">
        <i class="fas fa-user"></i>
        Autor {{ autorIndex }}
        <span v-if="totalCampos > 0" class="badge bg-primary ms-2">
          {{ camposPreenchidos }}/{{ totalCampos }}
        </span>
      </h6>
      
      <!-- Drop Zone para Autor -->
      <div
        class="autor-drop-zone"
        :class="{ 'drop-active': dropActive }"
        :data-autor-index="autorIndex"
        @drop="handleDrop"
        @dragover.prevent="dropActive = true"
        @dragenter.prevent="dropActive = true"
        @dragleave.prevent="dropActive = false"
      >
        <i class="fas fa-user-plus"></i>
        <span class="drop-text">Arraste um cliente aqui</span>
      </div>
    </div>

    <div class="autor-content">
      <!-- Abas: Dados Pessoais e Endereço -->
      <ul class="nav nav-tabs nav-justified mb-3" role="tablist">
        <li class="nav-item" role="presentation">
          <button
            :class="['nav-link', { active: abaAtiva === 'dados' }]"
            @click="abaAtiva = 'dados'"
            type="button"
          >
            <i class="fas fa-user"></i>
            Dados Pessoais
            <span v-if="autorData.dados?.length > 0" class="badge bg-info ms-1">
              {{ autorData.dados.length }}
            </span>
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button
            :class="['nav-link', { active: abaAtiva === 'endereco' }]"
            @click="abaAtiva = 'endereco'"
            type="button"
          >
            <i class="fas fa-map-marker-alt"></i>
            Endereço
            <span v-if="autorData.endereco?.length > 0" class="badge bg-success ms-1">
              {{ autorData.endereco.length }}
            </span>
          </button>
        </li>
      </ul>

      <!-- Conteúdo das Abas -->
      <div class="tab-content">
        <!-- Aba Dados Pessoais -->
        <div
          v-show="abaAtiva === 'dados'"
          class="tab-pane fade show active"
        >
          <div class="row">
            <div
              v-for="campo in autorData.dados || []"
              :key="campo.chave"
              class="col-md-6 mb-3"
            >
              <CampoFormulario
                :campo="campo"
                :valor="formData[campo.chave] || ''"
                @atualizado="$emit('campo-atualizado', $event)"
              />
            </div>
          </div>
          
          <!-- Estado vazio para dados -->
          <div v-if="!autorData.dados || autorData.dados.length === 0" class="empty-state">
            <i class="fas fa-user-slash text-muted fa-2x"></i>
            <p class="text-muted mt-2">Nenhum campo de dados pessoais encontrado para este autor</p>
          </div>
        </div>

        <!-- Aba Endereço -->
        <div
          v-show="abaAtiva === 'endereco'"
          class="tab-pane fade"
          :class="{ 'show active': abaAtiva === 'endereco' }"
        >
          <div class="row">
            <div
              v-for="campo in autorData.endereco || []"
              :key="campo.chave"
              class="col-md-6 mb-3"
            >
              <CampoFormulario
                :campo="campo"
                :valor="formData[campo.chave] || ''"
                @atualizado="$emit('campo-atualizado', $event)"
              />
            </div>
          </div>
          
          <!-- Estado vazio para endereço -->
          <div v-if="!autorData.endereco || autorData.endereco.length === 0" class="empty-state">
            <i class="fas fa-map-marker-slash text-muted fa-2x"></i>
            <p class="text-muted mt-2">Nenhum campo de endereço encontrado para este autor</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import CampoFormulario from './CampoFormulario.vue'

const props = defineProps({
  autorIndex: {
    type: [String, Number],
    required: true
  },
  autorData: {
    type: Object,
    required: true
  },
  formData: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['campo-atualizado', 'cliente-drop-autor'])

// Estado local
const abaAtiva = ref('dados')
const dropActive = ref(false)

// Computed
const totalCampos = computed(() => {
  const dados = props.autorData.dados?.length || 0
  const endereco = props.autorData.endereco?.length || 0
  return dados + endereco
})

const camposPreenchidos = computed(() => {
  let preenchidos = 0
  
  // Contar campos de dados preenchidos
  if (props.autorData.dados) {
    preenchidos += props.autorData.dados.filter(campo => 
      props.formData[campo.chave] && props.formData[campo.chave].toString().trim()
    ).length
  }
  
  // Contar campos de endereço preenchidos
  if (props.autorData.endereco) {
    preenchidos += props.autorData.endereco.filter(campo => 
      props.formData[campo.chave] && props.formData[campo.chave].toString().trim()
    ).length
  }
  
  return preenchidos
})

// Métodos
const handleDrop = (event) => {
  event.preventDefault()
  dropActive.value = false
  
  try {
    const clienteData = JSON.parse(event.dataTransfer.getData('application/json'))
    
    // Emitir evento para o componente pai tratar o drop
    emit('cliente-drop-autor', {
      clienteData,
      autorIndex: props.autorIndex
    })
    
    // Feedback visual
    mostrarFeedbackDrop()
    
  } catch (error) {
    console.error('Erro ao processar drop do cliente:', error)
  }
}

const mostrarFeedbackDrop = () => {
  // Adicionar efeito visual de sucesso
  const dropZone = document.querySelector(`[data-autor-index="${props.autorIndex}"]`)
  if (dropZone) {
    dropZone.classList.add('drop-success')
    setTimeout(() => {
      dropZone.classList.remove('drop-success')
    }, 1000)
  }
}
</script>

<style scoped>
.autor-secao {
  border: 1px solid #dee2e6;
  border-radius: 0.5rem;
  background-color: #fff;
  overflow: hidden;
}

.autor-header {
  background: linear-gradient(135deg, #4e73df 0%, #224abe 100%);
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.autor-titulo {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.autor-drop-zone {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 2px dashed rgba(255, 255, 255, 0.5);
  border-radius: 0.375rem;
  background-color: rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  min-width: 150px;
  justify-content: center;
}

.autor-drop-zone:hover,
.autor-drop-zone.drop-active {
  border-color: #fff;
  background-color: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.autor-drop-zone.drop-success {
  background-color: #28a745;
  border-color: #28a745;
  animation: pulse 1s ease;
}

.drop-text {
  font-size: 0.875rem;
  font-weight: 500;
}

.autor-content {
  padding: 1rem;
}

.nav-tabs {
  border-bottom: 2px solid #e9ecef;
}

.nav-tabs .nav-link {
  border: none;
  border-bottom: 3px solid transparent;
  background: none;
  color: #6c757d;
  font-weight: 500;
  padding: 0.75rem 1rem;
}

.nav-tabs .nav-link:hover {
  border-bottom-color: #dee2e6;
  color: #495057;
}

.nav-tabs .nav-link.active {
  color: #4e73df;
  border-bottom-color: #4e73df;
  background: none;
}

.tab-content {
  padding-top: 1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
}

.badge {
  font-size: 0.75rem;
}

/* Responsividade */
@media (max-width: 768px) {
  .autor-header {
    flex-direction: column;
    gap: 0.75rem;
    text-align: center;
  }
  
  .autor-drop-zone {
    min-width: auto;
    width: 100%;
  }
  
  .drop-text {
    font-size: 0.8rem;
  }
  
  .nav-tabs .nav-link {
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
  }
}

/* Animações */
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.tab-pane {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>