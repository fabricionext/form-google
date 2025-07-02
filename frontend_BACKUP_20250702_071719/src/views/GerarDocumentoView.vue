<template>
  <div>
    <v-row>
      <v-col>
        <h1 class="text-h4 mb-4">{{ modelo.nome || 'Carregando...' }}</h1>
        <p v-if="modelo.descricao" class="text-subtitle-1 mb-4">{{ modelo.descricao }}</p>
      </v-col>
    </v-row>

    <!-- Busca de Cliente -->
    <v-card class="mb-6" elevation="2" rounded="lg">
      <v-card-title class="text-h6 font-weight-bold d-flex align-center">
        <v-avatar color="info" size="32" class="me-3">
          <v-icon color="white" size="16">mdi-account-search</v-icon>
        </v-avatar>
        Buscar Cliente
      </v-card-title>
      
      <v-card-text>
        <v-row>
          <v-col cols="12" md="8">
            <v-text-field
              v-model="cpfBusca"
              label="CPF do Cliente"
              placeholder="000.000.000-00"
              prepend-inner-icon="mdi-card-account-details"
              :loading="buscandoCliente"
              variant="outlined"
              density="comfortable"
              @keyup.enter="buscarCliente"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="4">
            <v-btn
              @click="buscarCliente"
              :loading="buscandoCliente"
              color="primary"
              size="large"
              block
              rounded="lg"
            >
              <v-icon start>mdi-magnify</v-icon>
              Buscar Cliente
            </v-btn>
          </v-col>
        </v-row>

        <!-- Cliente Encontrado -->
        <v-expand-transition>
          <v-card
            v-if="cliente.nome_completo"
            class="mt-6"
            color="success"
            variant="tonal"
            rounded="lg"
          >
            <v-card-title class="text-h6 d-flex align-center">
              <v-icon class="me-2" color="success">mdi-account-check</v-icon>
              Cliente Encontrado
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <div class="mb-2">
                    <span class="text-subtitle-2">Nome:</span>
                    <div class="text-body-1 font-weight-medium">{{ cliente.nome_completo }}</div>
                  </div>
                  <div class="mb-2">
                    <span class="text-subtitle-2">CPF:</span>
                    <div class="text-body-1">{{ cliente.cpf }}</div>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div v-if="cliente.email" class="mb-2">
                    <span class="text-subtitle-2">Email:</span>
                    <div class="text-body-1">{{ cliente.email }}</div>
                  </div>
                  <div v-if="cliente.telefone" class="mb-2">
                    <span class="text-subtitle-2">Telefone:</span>
                    <div class="text-body-1">{{ cliente.telefone }}</div>
                  </div>
                </v-col>
              </v-row>
              
              <v-btn
                @click="preencherFormularioComCliente"
                color="success"
                size="large"
                class="mt-4"
                rounded="lg"
              >
                <v-icon start>mdi-auto-fix</v-icon>
                Preencher Formulário Automaticamente
              </v-btn>
            </v-card-text>
          </v-card>
        </v-expand-transition>
      </v-card-text>
    </v-card>

    <!-- Formulário Dinâmico -->
    <v-row>
      <v-col>
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-form-select</v-icon>
            Dados do Formulário
          </v-card-title>
          <v-card-text>
            <v-form ref="form" v-model="formularioValido">
              <v-row>
                <v-col
                  v-for="placeholder in placeholders"
                  :key="placeholder.id"
                  cols="12"
                  :md="getColWidth(placeholder.tipo_campo)"
                >
                  <!-- Campo de Texto -->
                  <v-text-field
                    v-if="placeholder.tipo_campo === 'string'"
                    v-model="formData[placeholder.chave]"
                    :label="placeholder.label_form"
                    :rules="getValidationRules(placeholder)"
                    :required="placeholder.obrigatorio"
                  ></v-text-field>

                  <!-- Campo de Texto Longo -->
                  <v-textarea
                    v-else-if="placeholder.tipo_campo === 'text'"
                    v-model="formData[placeholder.chave]"
                    :label="placeholder.label_form"
                    :rules="getValidationRules(placeholder)"
                    :required="placeholder.obrigatorio"
                    rows="3"
                  ></v-textarea>

                  <!-- Campo de Data -->
                  <v-text-field
                    v-else-if="placeholder.tipo_campo === 'date'"
                    v-model="formData[placeholder.chave]"
                    :label="placeholder.label_form"
                    :rules="getValidationRules(placeholder)"
                    :required="placeholder.obrigatorio"
                    type="date"
                  ></v-text-field>

                  <!-- Campo Numérico -->
                  <v-text-field
                    v-else-if="placeholder.tipo_campo === 'number'"
                    v-model="formData[placeholder.chave]"
                    :label="placeholder.label_form"
                    :rules="getValidationRules(placeholder)"
                    :required="placeholder.obrigatorio"
                    type="number"
                  ></v-text-field>

                  <!-- Campo Padrão -->
                  <v-text-field
                    v-else
                    v-model="formData[placeholder.chave]"
                    :label="placeholder.label_form"
                    :rules="getValidationRules(placeholder)"
                    :required="placeholder.obrigatorio"
                  ></v-text-field>
                </v-col>
              </v-row>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              @click="gerarDocumento"
              :loading="gerandoDocumento"
              :disabled="!formularioValido || placeholders.length === 0"
              color="primary"
              size="large"
            >
              <v-icon class="mr-2">mdi-file-document-outline</v-icon>
              Gerar Documento
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Snackbar para mensagens -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="5000"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="snackbar.show = false"
        >
          Fechar
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import { formularioService, clienteService } from '@/services/api'

export default {
  name: 'GerarDocumentoView',
  props: {
    slug: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      modelo: {},
      placeholders: [],
      formData: {},
      cliente: {},
      cpfBusca: '',
      buscandoCliente: false,
      gerandoDocumento: false,
      formularioValido: false,
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
        const response = await formularioService.buscarPorSlug(this.slug)
        
        if (response.success) {
          this.modelo = response.data.modelo
          this.placeholders = response.data.placeholders || []
          this.inicializarFormData()
        } else {
          this.mostrarMensagem('Erro ao carregar formulário', 'error')
        }
      } catch (error) {
        console.error('Erro ao carregar dados:', error)
        this.mostrarMensagem('Erro ao conectar com o servidor', 'error')
      }
    },

    inicializarFormData() {
      const data = {}
      this.placeholders.forEach(placeholder => {
        data[placeholder.chave] = ''
      })
      this.formData = data
    },

    async buscarCliente() {
      if (!this.cpfBusca.trim()) {
        this.mostrarMensagem('Digite um CPF para buscar', 'warning')
        return
      }

      try {
        this.buscandoCliente = true
        const response = await clienteService.buscarPorCpf(this.cpfBusca)
        
        if (response.success) {
          this.cliente = response.cliente
          this.mostrarMensagem('Cliente encontrado com sucesso!', 'success')
        } else {
          this.cliente = {}
          this.mostrarMensagem('Cliente não encontrado', 'warning')
        }
      } catch (error) {
        console.error('Erro ao buscar cliente:', error)
        this.mostrarMensagem('Erro ao buscar cliente', 'error')
      } finally {
        this.buscandoCliente = false
      }
    },

    preencherFormularioComCliente() {
      if (!this.cliente.nome_completo) return

      // Mapeia os dados do cliente para o formulário
      const mapeamento = {
        'primeiro_nome': this.cliente.primeiro_nome,
        'sobrenome': this.cliente.sobrenome,
        'nome_completo': this.cliente.nome_completo,
        'cpf': this.cliente.cpf,
        'email': this.cliente.email,
        'telefone': this.cliente.telefone,
        'endereco': this.cliente.endereco,
        'cidade': this.cliente.cidade,
        'estado': this.cliente.estado,
        'cep': this.cliente.cep
      }

      for (const [chave, valor] of Object.entries(mapeamento)) {
        if (this.formData.hasOwnProperty(chave) && valor) {
          this.formData[chave] = valor
        }
      }

      this.mostrarMensagem('Formulário preenchido com dados do cliente!', 'success')
    },

    async gerarDocumento() {
      try {
        this.gerandoDocumento = true
        
        const response = await formularioService.gerarDocumento(this.slug, this.formData)
        
        if (response.success) {
          this.mostrarMensagem('Documento gerado com sucesso!', 'success')
          // Abre o documento em nova aba
          if (response.link) {
            window.open(response.link, '_blank')
          }
        } else {
          this.mostrarMensagem(response.error || 'Erro ao gerar documento', 'error')
        }
      } catch (error) {
        console.error('Erro ao gerar documento:', error)
        this.mostrarMensagem('Erro ao gerar documento', 'error')
      } finally {
        this.gerandoDocumento = false
      }
    },

    getColWidth(tipoCampo) {
      // Define o tamanho da coluna baseado no tipo de campo
      switch (tipoCampo) {
        case 'text':
          return 12 // Texto longo ocupa linha inteira
        case 'date':
          return 6  // Data ocupa metade da linha
        default:
          return 6  // Outros campos ocupam metade da linha
      }
    },

    getValidationRules(placeholder) {
      const rules = []
      
      if (placeholder.obrigatorio) {
        rules.push(v => !!v || `${placeholder.label_form} é obrigatório`)
      }
      
      if (placeholder.tipo_campo === 'email') {
        rules.push(v => !v || /.+@.+\..+/.test(v) || 'Email deve ser válido')
      }
      
      return rules
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