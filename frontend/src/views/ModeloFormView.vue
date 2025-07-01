<template>
  <div>
    <v-row>
      <v-col>
        <h1 class="text-h4 mb-4">
          {{ isEdit ? 'Editar Modelo' : 'Novo Modelo' }}
        </h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <v-card>
          <v-card-text>
            <v-form ref="form" v-model="formularioValido">
              <v-text-field
                v-model="modelo.nome"
                label="Nome do Modelo"
                :rules="[v => !!v || 'Nome é obrigatório']"
                required
              ></v-text-field>

              <v-textarea
                v-model="modelo.descricao"
                label="Descrição"
                rows="3"
              ></v-textarea>

              <v-text-field
                v-model="modelo.doc_template_id"
                label="ID do Template no Google Docs"
                :rules="[v => !!v || 'ID do template é obrigatório']"
                required
              ></v-text-field>

              <v-text-field
                v-model="modelo.pasta_destino_id"
                label="ID da Pasta de Destino no Google Drive"
                :rules="[v => !!v || 'ID da pasta é obrigatório']"
                required
              ></v-text-field>

              <v-switch
                v-model="modelo.ativo"
                label="Ativo"
                color="primary"
              ></v-switch>
            </v-form>
          </v-card-text>

          <v-card-actions>
            <v-btn
              @click="$router.back()"
              variant="outlined"
            >
              Cancelar
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn
              @click="salvar"
              :loading="salvando"
              :disabled="!formularioValido"
              color="primary"
            >
              {{ isEdit ? 'Atualizar' : 'Criar' }}
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
import { modeloService } from '@/services/api'

export default {
  name: 'ModeloFormView',
  props: {
    id: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      modelo: {
        nome: '',
        descricao: '',
        doc_template_id: '',
        pasta_destino_id: '',
        ativo: true
      },
      formularioValido: false,
      salvando: false,
      snackbar: {
        show: false,
        message: '',
        color: 'success'
      }
    }
  },
  computed: {
    isEdit() {
      return !!this.id
    }
  },
  async mounted() {
    if (this.isEdit) {
      await this.carregarModelo()
    }
  },
  methods: {
    async carregarModelo() {
      try {
        const response = await modeloService.buscarPorId(this.id)
        if (response.success) {
          this.modelo = response.modelo
        } else {
          this.mostrarMensagem('Erro ao carregar modelo', 'error')
        }
      } catch (error) {
        console.error('Erro ao carregar modelo:', error)
        this.mostrarMensagem('Erro ao conectar com o servidor', 'error')
      }
    },

    async salvar() {
      try {
        this.salvando = true
        
        let response
        if (this.isEdit) {
          response = await modeloService.atualizar(this.id, this.modelo)
        } else {
          response = await modeloService.criar(this.modelo)
        }
        
        if (response.success) {
          this.mostrarMensagem(
            this.isEdit ? 'Modelo atualizado com sucesso!' : 'Modelo criado com sucesso!',
            'success'
          )
          setTimeout(() => {
            this.$router.push('/modelos')
          }, 1500)
        } else {
          this.mostrarMensagem(response.error || 'Erro ao salvar modelo', 'error')
        }
      } catch (error) {
        console.error('Erro ao salvar modelo:', error)
        this.mostrarMensagem('Erro ao salvar modelo', 'error')
      } finally {
        this.salvando = false
      }
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