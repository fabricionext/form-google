<template>
  <div class="cliente-search-card card mb-3">
    <div class="card-header">
      <h6 class="mb-0">
        <i class="fas fa-users"></i>
        Buscar Clientes
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
            placeholder="Nome, CPF ou email..."
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
            {{ resultados.length }} cliente(s) encontrado(s)
          </small>
        </div>

        <div class="results-list">
          <div
            v-for="cliente in resultados"
            :key="cliente.id"
            class="cliente-item"
            :class="{ dragging: cliente.isDragging }"
            draggable="true"
            :data-type="'cliente'"
            :data-cliente="JSON.stringify(cliente)"
            @dragstart="handleDragStart(cliente, $event)"
            @dragend="handleDragEnd(cliente, $event)"
            @click="selecionarCliente(cliente)"
          >
            <div class="cliente-info">
              <div class="cliente-nome">
                <strong>{{
                  cliente.nome_completo ||
                  `${cliente.primeiro_nome} ${cliente.sobrenome}`
                }}</strong>
              </div>
              <div class="cliente-detalhes">
                <small class="text-muted">
                  {{ cliente.cpf || cliente.cnpj }} • {{ cliente.email }}
                </small>
              </div>
              <div v-if="cliente.endereco_cidade" class="cliente-endereco">
                <small class="text-muted">
                  <i class="fas fa-map-marker-alt"></i>
                  {{ cliente.endereco_cidade }}/{{ cliente.endereco_estado }}
                </small>
              </div>
            </div>
            <div class="cliente-actions">
              <button
                @click.stop="selecionarCliente(cliente)"
                class="btn btn-sm btn-outline-primary"
                title="Preencher dados do cliente"
              >
                <i class="fas fa-arrow-right"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Estado vazio -->
      <div
        v-else-if="searchQuery && !carregando"
        class="empty-state text-center py-3"
      >
        <i class="fas fa-search text-muted"></i>
        <p class="text-muted mb-0">Nenhum cliente encontrado</p>
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
          Digite para buscar clientes existentes
        </small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useFormularioStore } from '../stores/formulario.js';

const emit = defineEmits(['cliente-selecionado', 'cliente-drop-autor']);

const formularioStore = useFormularioStore();

// Estado local
const searchQuery = ref('');
const carregando = ref(false);

// Computed
const resultados = computed(() => {
  if (!searchQuery.value.trim()) return [];
  return formularioStore.buscarClientes(searchQuery.value);
});

// Métodos
const handleSearch = () => {
  // A busca é reativa através do computed
  // Aqui podemos adicionar debounce se necessário
};

const limparBusca = () => {
  searchQuery.value = '';
};

const selecionarCliente = cliente => {
  emit('cliente-selecionado', cliente);
  searchQuery.value = ''; // Limpar busca após seleção
};

// Drag and Drop
const handleDragStart = (cliente, event) => {
  cliente.isDragging = true;

  // Configurar dados do drag
  event.dataTransfer.setData('application/json', JSON.stringify(cliente));
  event.dataTransfer.setData('text/plain', cliente.nome_completo);
  event.dataTransfer.effectAllowed = 'copy';

  // Adicionar classe visual
  event.target.classList.add('dragging');
};

const handleDragEnd = (cliente, event) => {
  cliente.isDragging = false;
  event.target.classList.remove('dragging');
};
</script>

<style scoped>
.cliente-search-card {
  border: 1px solid #e3e6f0;
  box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
}

.search-container {
  position: relative;
}

.results-list {
  max-height: 400px;
  overflow-y: auto;
}

.cliente-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  border: 1px solid #e3e6f0;
  border-radius: 0.35rem;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cliente-item:hover {
  border-color: #4e73df;
  background-color: #f8f9fc;
  transform: translateY(-1px);
  box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.1);
}

.cliente-item.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.cliente-info {
  flex: 1;
}

.cliente-nome {
  margin-bottom: 0.25rem;
}

.cliente-detalhes,
.cliente-endereco {
  margin-bottom: 0.25rem;
}

.cliente-actions {
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
  border: 2px dashed #dee2e6;
  border-radius: 0.35rem;
  background-color: #f8f9fa;
}

.loading {
  padding: 1rem;
}

/* Responsividade */
@media (max-width: 768px) {
  .cliente-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .cliente-actions {
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
