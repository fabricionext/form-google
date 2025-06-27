<template>
  <div class="autoridade-search-card card mb-3">
    <div class="card-header">
      <h6 class="mb-0">
        <i class="fas fa-landmark"></i>
        Autoridades de Trânsito
      </h6>
    </div>
    <div class="card-body">
      <!-- Campo de busca -->
      <div class="search-container mb-3">
        <div class="input-group">
          <input
            v-model="searchQuery"
            @input="handleSearch"
            type="text"
            class="form-control"
            placeholder="Nome da autoridade ou cidade..."
            autocomplete="off"
          />
          <button
            v-if="searchQuery"
            @click="limparBusca"
            class="btn btn-outline-secondary"
            type="button"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

      <!-- Resultados da busca -->
      <div v-if="resultados.length > 0" class="search-results">
        <div class="results-header mb-2">
          <small class="text-muted">
            {{ resultados.length }} autoridade(s) encontrada(s)
          </small>
        </div>
        
        <div class="results-list">
          <div
            v-for="autoridade in resultados"
            :key="autoridade.id"
            class="autoridade-item"
            :class="{ 'dragging': autoridade.isDragging }"
            draggable="true"
            :data-type="'autoridade'"
            :data-autoridade="JSON.stringify(autoridade)"
            @dragstart="handleDragStart(autoridade, $event)"
            @dragend="handleDragEnd(autoridade, $event)"
            @click="selecionarAutoridade(autoridade)"
          >
            <div class="autoridade-info">
              <div class="autoridade-nome">
                <strong>{{ autoridade.nome }}</strong>
              </div>
              <div v-if="autoridade.cnpj" class="autoridade-cnpj">
                <small class="text-muted">
                  CNPJ: {{ autoridade.cnpj }}
                </small>
              </div>
              <div v-if="autoridade.cidade" class="autoridade-endereco">
                <small class="text-muted">
                  <i class="fas fa-map-marker-alt"></i>
                  {{ autoridade.cidade }}{{ autoridade.estado ? `/${autoridade.estado}` : '' }}
                </small>
              </div>
            </div>
            <div class="autoridade-actions">
              <button
                @click.stop="selecionarAutoridade(autoridade)"
                class="btn btn-sm btn-outline-warning"
                title="Preencher dados da autoridade"
              >
                <i class="fas fa-arrow-right"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Estado vazio -->
      <div v-else-if="searchQuery && !carregando" class="empty-state text-center py-3">
        <i class="fas fa-search text-muted"></i>
        <p class="text-muted mb-0">Nenhuma autoridade encontrada</p>
      </div>

      <!-- Loading -->
      <div v-if="carregando" class="loading text-center py-3">
        <div class="spinner-border spinner-border-sm" role="status">
          <span class="visually-hidden">Carregando...</span>
        </div>
      </div>

      <!-- Instruções -->
      <div v-if="!searchQuery" class="instructions">
        <small class="text-muted">
          <i class="fas fa-info-circle"></i>
          Digite para buscar autoridades de trânsito
        </small>
      </div>

      <!-- Botão para adicionar nova autoridade -->
      <div class="mt-3">
        <button
          @click="abrirModalNovaAutoridade"
          class="btn btn-sm btn-outline-secondary w-100"
        >
          <i class="fas fa-plus"></i>
          Nova Autoridade
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFormularioStore } from '../stores/formulario.js'

const emit = defineEmits(['autoridade-selecionada'])

const formularioStore = useFormularioStore()

// Estado local
const searchQuery = ref('')
const carregando = ref(false)

// Computed
const resultados = computed(() => {
  if (!searchQuery.value.trim()) return []
  return formularioStore.buscarAutoridades(searchQuery.value)
})

// Métodos
const handleSearch = () => {
  // A busca é reativa através do computed
}

const limparBusca = () => {
  searchQuery.value = ''
}

const selecionarAutoridade = (autoridade) => {
  // Por padrão, usar índice 1 para a primeira autoridade
  emit('autoridade-selecionada', { autoridadeData: autoridade, index: 1 })
  searchQuery.value = '' // Limpar busca após seleção
}

const abrirModalNovaAutoridade = () => {
  // TODO: Implementar modal para cadastrar nova autoridade
  alert('Funcionalidade de cadastro de nova autoridade será implementada')
}

// Drag and Drop
const handleDragStart = (autoridade, event) => {
  autoridade.isDragging = true
  
  // Configurar dados do drag
  event.dataTransfer.setData('application/json', JSON.stringify(autoridade))
  event.dataTransfer.setData('text/plain', autoridade.nome)
  event.dataTransfer.effectAllowed = 'copy'
  
  // Adicionar classe visual
  event.target.classList.add('dragging')
}

const handleDragEnd = (autoridade, event) => {
  autoridade.isDragging = false
  event.target.classList.remove('dragging')
}
</script>

<style scoped>
.autoridade-search-card {
  border: 1px solid #f6c23e;
  box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
}

.autoridade-search-card .card-header {
  background-color: #f6c23e;
  border-bottom: 1px solid #f6c23e;
}

.autoridade-search-card .card-header h6 {
  color: #fff;
}

.search-container {
  position: relative;
}

.results-list {
  max-height: 300px;
  overflow-y: auto;
}

.autoridade-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  border: 1px solid #f6c23e;
  border-radius: 0.35rem;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.autoridade-item:hover {
  border-color: #e6b800;
  background-color: #fffbf0;
  transform: translateY(-1px);
  box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.1);
}

.autoridade-item.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.autoridade-info {
  flex: 1;
}

.autoridade-nome {
  margin-bottom: 0.25rem;
}

.autoridade-cnpj,
.autoridade-endereco {
  margin-bottom: 0.25rem;
}

.autoridade-actions {
  flex-shrink: 0;
  margin-left: 0.5rem;
}

.empty-state {
  color: #6c757d;
}

.empty-state i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  display: block;
}

.instructions {
  text-align: center;
  padding: 1rem;
  border: 2px dashed #f6c23e;
  border-radius: 0.35rem;
  background-color: #fffbf0;
}

.loading {
  padding: 1rem;
}

/* Responsividade */
@media (max-width: 768px) {
  .autoridade-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .autoridade-actions {
    margin-left: 0;
    margin-top: 0.5rem;
    align-self: flex-end;
  }
}

/* Animações */
.results-list {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>