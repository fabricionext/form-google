<template>
  <div>
    <v-row>
      <v-col>
        <h1 class="text-h4 mb-4">
          Placeholders: {{ modelo.nome || 'Carregando...' }}
        </h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <v-card>
          <v-card-title>
            Gerenciar Placeholders
            <v-spacer></v-spacer>
            <v-btn
              @click="sincronizarPlaceholders"
              :loading="sincronizando"
              color="primary"
              class="mr-2"
            >
              <v-icon class="mr-2">mdi-sync</v-icon>
              Sincronizar
            </v-btn>
          </v-card-title>

          <v-card-text>
            <p class="text-subtitle-1 mb-4">
              Arraste e solte os itens para reordenar os placeholders:
            </p>

            <div v-if="placeholders.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey">mdi-format-list-bulleted</v-icon>
              <p class="text-h6 mt-4">Nenhum placeholder encontrado</p>
              <p class="text-body-2">Clique em "Sincronizar" para detectar placeholders no documento.</p>
            </div>

            <draggable
              v-else
              v-model="placeholders"
              item-key="id"
              @end="onDragEnd"
              class="placeholder-list"
            >
              <template #item="{ element, index }">
                <v-card
                  class="placeholder-item mb-2"
                  outlined
                  :class="{ 'dragging': element.dragging }"
                >
                  <v-card-text class="py-3">
                    <v-row align="center">
                      <v-col cols="1">
                        <v-icon class="drag-handle" color="grey">
                          mdi-drag-vertical
                        </v-icon>
                      </v-col>
                      <v-col cols="2">
                        <strong>{{ element.chave }}</strong>
                      </v-col>
                      <v-col cols="3">
                        {{ element.label_form }}
                      </v-col>
                      <v-col cols="2">
                        <v-chip
                          :color="getTipoColor(element.tipo_campo)"
                          small
                        >
                          {{ element.tipo_campo }}
                        </v-chip>
                      </v-col>
                      <v-col cols="2">
                        <v-switch
                          v-model="element.obrigatorio"
                          label="Obrigatório"
                          @change="atualizarPlaceholder(element)"
                          density="compact"
                        ></v-switch>
                      </v-col>
                      <v-col cols="2">
                        <span class="text-caption">Ordem: {{ element.ordem || index + 1 }}</span>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </template>
            </draggable>
          </v-card-text>

          <v-card-actions v-if="placeholders.length > 0">
            <v-spacer></v-spacer>
            <v-btn
              @click="salvarOrdem"
              :loading="salvandoOrdem"
              color="success"
            >
              <v-icon class="mr-2">mdi-content-save</v-icon>
              Salvar Ordem
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Snackbar para mensagens -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
    >
      {{ snackbar.message }}
    </v-snackbar>
  </div>
</template>

<script>
import draggable from 'vuedraggable'
import { modeloService } from '@/services/api'

export default {
  name: 'PlaceholdersView',
  components: {
    draggable
  },
  props: {
    id: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      modelo: {},
      placeholders: [],
      sincronizando: false,
      salvandoOrdem: false,
      snackbar: {
        show: false,
        message: '',
        color: 'success'
      }
    }
  },
  async mounted() {
    await this.carregarDados()
  },
  methods: {
    async carregarDados() {
      try {
        const response = await modeloService.buscarPorId(this.id)
        if (response.success) {
          this.modelo = response.modelo
          this.placeholders = response.placeholders || []
        } else {
          this.mostrarMensagem('Erro ao carregar dados', 'error')
        }
      } catch (error) {
        console.error('Erro ao carregar dados:', error)
        this.mostrarMensagem('Erro ao conectar com o servidor', 'error')
      }
    },

    async sincronizarPlaceholders() {
      try {
        this.sincronizando = true
        const response = await modeloService.sincronizarPlaceholders(this.id)
        
        if (response.success) {
          this.mostrarMensagem('Placeholders sincronizados com sucesso!', 'success')
          await this.carregarDados() // Recarrega os dados
        } else {
          this.mostrarMensagem(response.error || 'Erro ao sincronizar placeholders', 'error')
        }
      } catch (error) {
        console.error('Erro ao sincronizar placeholders:', error)
        this.mostrarMensagem('Erro ao sincronizar placeholders', 'error')
      } finally {
        this.sincronizando = false
      }
    },

    async salvarOrdem() {
      try {
        this.salvandoOrdem = true
        
        // Cria array com a nova ordem baseada na posição atual
        const novaOrdem = this.placeholders.map((placeholder, index) => ({
          id: placeholder.id,
          ordem: index + 1
        }))
        
        const response = await modeloService.reordenarPlaceholders(this.id, novaOrdem)
        
        if (response.success) {
          this.mostrarMensagem('Ordem salva com sucesso!', 'success')
        } else {
          this.mostrarMensagem(response.error || 'Erro ao salvar ordem', 'error')
        }
      } catch (error) {
        console.error('Erro ao salvar ordem:', error)
        this.mostrarMensagem('Erro ao salvar ordem', 'error')
      } finally {
        this.salvandoOrdem = false
      }
    },

    onDragEnd() {
      // Este método é chamado quando o usuário termina de arrastar um item
      console.log('Ordem alterada')
    },

    async atualizarPlaceholder(placeholder) {
      // TODO: Implementar atualização individual de placeholder
      console.log('Atualizar placeholder:', placeholder)
    },

    getTipoColor(tipo) {
      const cores = {
        'string': 'blue',
        'text': 'green',
        'date': 'orange',
        'number': 'purple',
        'email': 'teal'
      }
      return cores[tipo] || 'grey'
    },

    mostrarMensagem(message, color = 'success') {
      this.snackbar = {
        show: true,
        message,
        color
      }
    }
  }
}
</script>

<style scoped>
.placeholder-list {
  min-height: 100px;
}

.placeholder-item {
  cursor: move;
  transition: all 0.3s ease;
}

.placeholder-item:hover {
  background-color: #f5f5f5;
}

.placeholder-item.dragging {
  opacity: 0.5;
  transform: rotate(5deg);
}

.drag-handle {
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}
</style>