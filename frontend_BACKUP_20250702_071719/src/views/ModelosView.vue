<template>
  <div>
    <!-- Header Section -->
    <div class="d-flex align-center justify-space-between mb-8">
      <div>
        <h1 class="text-h4 font-weight-bold text-primary mb-2">
          Modelos de Petição
        </h1>
        <p class="text-subtitle-1 text-medium-emphasis mb-0">
          Gerencie e organize seus templates de documentos jurídicos
        </p>
      </div>
      
      <v-btn
        color="primary"
        size="large"
        :to="'/modelos/novo'"
        elevation="2"
        rounded="lg"
        class="px-6"
      >
        <v-icon start>mdi-plus</v-icon>
        Novo Modelo
      </v-btn>
    </div>

    <!-- Statistics Cards -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" lg="3">
        <v-card color="primary" variant="elevated" rounded="lg">
          <v-card-text class="text-center text-white">
            <v-icon size="40" class="mb-2">mdi-file-document-multiple</v-icon>
            <div class="text-h4 font-weight-bold">{{ modelos.length }}</div>
            <div class="text-body-2">Total de Modelos</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" lg="3">
        <v-card color="success" variant="elevated" rounded="lg">
          <v-card-text class="text-center text-white">
            <v-icon size="40" class="mb-2">mdi-check-circle</v-icon>
            <div class="text-h4 font-weight-bold">{{ modelosAtivos }}</div>
            <div class="text-body-2">Modelos Ativos</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" lg="3">
        <v-card color="info" variant="elevated" rounded="lg">
          <v-card-text class="text-center text-white">
            <v-icon size="40" class="mb-2">mdi-clock-outline</v-icon>
            <div class="text-h4 font-weight-bold">{{ modelosRecentes }}</div>
            <div class="text-body-2">Criados este Mês</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" lg="3">
        <v-card color="warning" variant="elevated" rounded="lg">
          <v-card-text class="text-center text-white">
            <v-icon size="40" class="mb-2">mdi-trending-up</v-icon>
            <div class="text-h4 font-weight-bold">{{ documentosGerados }}</div>
            <div class="text-body-2">Docs Gerados</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filters and Search -->
    <v-card class="mb-6" elevation="2" rounded="lg">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="4">
            <v-text-field
              v-model="searchQuery"
              label="Buscar modelos..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            ></v-text-field>
          </v-col>
          
          <v-col cols="12" md="3">
            <v-select
              v-model="statusFilter"
              :items="statusOptions"
              label="Status"
              variant="outlined"
              density="compact"
              hide-details
            ></v-select>
          </v-col>
          
          <v-col cols="12" md="3">
            <v-select
              v-model="sortBy"
              :items="sortOptions"
              label="Ordenar por"
              variant="outlined"
              density="compact"
              hide-details
            ></v-select>
          </v-col>
          
          <v-col cols="12" md="2">
            <v-btn-toggle
              v-model="viewMode"
              variant="outlined"
              mandatory
              divided
            >
              <v-btn value="table" icon="mdi-table"></v-btn>
              <v-btn value="grid" icon="mdi-view-grid"></v-btn>
            </v-btn-toggle>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Data Table View -->
    <v-card v-if="viewMode === 'table'" elevation="2" rounded="lg">
      <v-data-table
        :headers="headers"
        :items="filteredModelos"
        :loading="loading"
        :search="searchQuery"
        class="elevation-0"
        density="comfortable"
        show-expand
        hover
      >
        <template v-slot:item.actions="{ item }">
          <div class="d-flex gap-1">
            <v-tooltip text="Editar Modelo">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  size="small"
                  variant="tonal"
                  color="info"
                  :to="`/modelos/${item.id}/editar`"
                  icon
                >
                  <v-icon size="16">mdi-pencil</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
            
            <v-tooltip text="Gerenciar Placeholders">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  size="small"
                  variant="tonal"
                  color="warning"
                  :to="`/modelos/${item.id}/placeholders`"
                  icon
                >
                  <v-icon size="16">mdi-format-list-bulleted</v-icon>
                </v-btn>
              </template>
            </v-tooltip>

            <v-tooltip text="Gerar Documento">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  size="small"
                  variant="tonal"
                  color="success"
                  @click="abrirFormulario(item.slug)"
                  icon
                >
                  <v-icon size="16">mdi-file-document</v-icon>
                </v-btn>
              </template>
            </v-tooltip>

            <v-tooltip text="Mais opções">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  size="small"
                  variant="text"
                  icon
                >
                  <v-icon size="16">mdi-dots-vertical</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
          </div>
        </template>

        <template v-slot:item.ativo="{ item }">
          <v-chip
            :color="item.ativo ? 'success' : 'error'"
            size="small"
            variant="tonal"
          >
            <v-icon start size="16">
              {{ item.ativo ? 'mdi-check-circle' : 'mdi-close-circle' }}
            </v-icon>
            {{ item.ativo ? 'Ativo' : 'Inativo' }}
          </v-chip>
        </template>

        <template v-slot:item.data_criacao="{ item }">
          <div class="text-body-2">
            {{ formatDate(item.data_criacao) }}
          </div>
        </template>

        <template v-slot:expanded-row="{ item }">
          <div class="pa-4 bg-surface-variant">
            <v-row>
              <v-col cols="12" md="6">
                <div class="text-subtitle-2 mb-2">Descrição:</div>
                <p class="text-body-2">{{ item.descricao || 'Sem descrição' }}</p>
              </v-col>
              <v-col cols="12" md="6">
                <div class="text-subtitle-2 mb-2">Estatísticas:</div>
                <v-chip-group>
                  <v-chip size="small" color="primary">
                    <v-icon start size="14">mdi-puzzle</v-icon>
                    {{ item.total_placeholders || 0 }} placeholders
                  </v-chip>
                  <v-chip size="small" color="secondary">
                    <v-icon start size="14">mdi-file-document</v-icon>
                    {{ item.documentos_gerados || 0 }} documentos
                  </v-chip>
                </v-chip-group>
              </v-col>
            </v-row>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Grid View -->
    <v-row v-else>
      <v-col
        v-for="modelo in filteredModelos"
        :key="modelo.id"
        cols="12"
        sm="6"
        lg="4"
        xl="3"
      >
        <v-card
          elevation="2"
          rounded="lg"
          hover
          class="modelo-card"
          @click="abrirFormulario(modelo.slug)"
        >
          <v-card-text>
            <div class="d-flex align-center justify-space-between mb-3">
              <v-avatar color="primary" size="48">
                <v-icon color="white" size="24">mdi-file-document</v-icon>
              </v-avatar>
              
              <v-chip
                :color="modelo.ativo ? 'success' : 'error'"
                size="small"
                variant="tonal"
              >
                {{ modelo.ativo ? 'Ativo' : 'Inativo' }}
              </v-chip>
            </div>
            
            <h3 class="text-h6 font-weight-bold mb-2">{{ modelo.nome }}</h3>
            <p class="text-body-2 text-medium-emphasis mb-3">
              {{ modelo.descricao || 'Sem descrição' }}
            </p>
            
            <div class="d-flex justify-space-between align-center">
              <div class="text-caption">
                {{ formatDate(modelo.data_criacao) }}
              </div>
              
              <v-btn-group variant="tonal" size="small">
                <v-btn
                  :to="`/modelos/${modelo.id}/editar`"
                  icon
                  @click.stop
                >
                  <v-icon size="16">mdi-pencil</v-icon>
                </v-btn>
                <v-btn
                  :to="`/modelos/${modelo.id}/placeholders`"
                  icon
                  @click.stop
                >
                  <v-icon size="16">mdi-format-list-bulleted</v-icon>
                </v-btn>
              </v-btn-group>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-card
      v-if="modelos.length === 0 && !loading"
      elevation="0"
      rounded="lg"
      class="text-center pa-12"
    >
      <v-icon size="120" color="medium-emphasis" class="mb-4">
        mdi-file-document-plus-outline
      </v-icon>
      <h2 class="text-h5 font-weight-bold mb-4">Nenhum modelo encontrado</h2>
      <p class="text-body-1 text-medium-emphasis mb-6">
        Comece criando seu primeiro modelo de petição para automatizar a geração de documentos.
      </p>
      <v-btn
        color="primary"
        size="large"
        :to="'/modelos/novo'"
        rounded="lg"
      >
        <v-icon start>mdi-plus</v-icon>
        Criar Primeiro Modelo
      </v-btn>
    </v-card>

    <!-- Enhanced Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="4000"
      elevation="6"
      rounded="lg"
    >
      <div class="d-flex align-center">
        <v-icon class="me-2">{{ snackbar.icon }}</v-icon>
        {{ snackbar.message }}
      </div>
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">
          Fechar
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import { modeloService } from '@/services/api'

export default {
  name: 'ModelosView',
  data() {
    return {
      modelos: [],
      loading: true,
      searchQuery: '',
      statusFilter: 'todos',
      sortBy: 'nome',
      viewMode: 'table',
      headers: [
        { title: 'Nome', key: 'nome', sortable: true },
        { title: 'Descrição', key: 'descricao', sortable: false },
        { title: 'Status', key: 'ativo', sortable: true },
        { title: 'Criado em', key: 'data_criacao', sortable: true },
        { title: 'Ações', key: 'actions', sortable: false, width: '140px' }
      ],
      statusOptions: [
        { title: 'Todos', value: 'todos' },
        { title: 'Ativos', value: 'ativo' },
        { title: 'Inativos', value: 'inativo' }
      ],
      sortOptions: [
        { title: 'Nome', value: 'nome' },
        { title: 'Data de Criação', value: 'data_criacao' },
        { title: 'Status', value: 'ativo' }
      ],
      snackbar: {
        show: false,
        message: '',
        color: 'success',
        icon: 'mdi-check-circle'
      }
    }
  },
  computed: {
    filteredModelos() {
      let filtered = [...this.modelos]
      
      // Filter by status
      if (this.statusFilter !== 'todos') {
        filtered = filtered.filter(modelo => {
          if (this.statusFilter === 'ativo') return modelo.ativo
          if (this.statusFilter === 'inativo') return !modelo.ativo
          return true
        })
      }
      
      // Sort
      filtered.sort((a, b) => {
        if (this.sortBy === 'nome') {
          return a.nome.localeCompare(b.nome)
        }
        if (this.sortBy === 'data_criacao') {
          return new Date(b.data_criacao) - new Date(a.data_criacao)
        }
        if (this.sortBy === 'ativo') {
          return b.ativo - a.ativo
        }
        return 0
      })
      
      return filtered
    },
    
    modelosAtivos() {
      return this.modelos.filter(m => m.ativo).length
    },
    
    modelosRecentes() {
      const umMesAtras = new Date()
      umMesAtras.setMonth(umMesAtras.getMonth() - 1)
      return this.modelos.filter(m => new Date(m.data_criacao) > umMesAtras).length
    },
    
    documentosGerados() {
      return this.modelos.reduce((total, m) => total + (m.documentos_gerados || 0), 0)
    }
  },
  async mounted() {
    await this.carregarModelos()
  },
  methods: {
    async carregarModelos() {
      try {
        this.loading = true
        const response = await modeloService.listar()
        if (response.success) {
          this.modelos = response.modelos || []
        } else {
          this.mostrarMensagem('Erro ao carregar modelos', 'error', 'mdi-alert-circle')
        }
      } catch (error) {
        console.error('Erro ao carregar modelos:', error)
        this.mostrarMensagem('Erro ao conectar com o servidor', 'error', 'mdi-wifi-off')
      } finally {
        this.loading = false
      }
    },
    
    abrirFormulario(slug) {
      this.$router.push(`/formularios/${slug}/gerar`)
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    },
    
    mostrarMensagem(message, color = 'success', icon = 'mdi-check-circle') {
      this.snackbar = {
        show: true,
        message,
        color,
        icon
      }
    }
  }
}
</script>

<style scoped>
.modelo-card {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modelo-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

/* Custom data table styling */
:deep(.v-data-table) {
  border-radius: 12px;
}

:deep(.v-data-table__td) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

:deep(.v-data-table__tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.04);
}

/* Statistics cards animation */
@keyframes slideInUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.v-card {
  animation: slideInUp 0.6s ease-out;
}

.v-card:nth-child(2) {
  animation-delay: 0.1s;
}

.v-card:nth-child(3) {
  animation-delay: 0.2s;
}

.v-card:nth-child(4) {
  animation-delay: 0.3s;
}
</style>