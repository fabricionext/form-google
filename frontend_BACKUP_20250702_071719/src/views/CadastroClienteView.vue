<template>
  <v-container fluid class="pa-2 pa-md-4">
    <!-- Header Responsivo -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="text-center text-md-left">
          <h1 class="text-h4 text-md-h3 font-weight-bold text-primary mb-2">
            <v-icon color="primary" size="large" class="me-2"
              >mdi-account-plus</v-icon
            >
            Cadastro de Cliente
          </h1>
          <p class="text-body-1 text-medium-emphasis">
            Preencha os dados para criar pasta no Google Drive e gerar
            documentos
          </p>
        </div>
      </v-col>
    </v-row>

    <!-- Barra de Progresso -->
    <v-row v-if="processando">
      <v-col cols="12">
        <v-card class="mb-4" elevation="2">
          <v-card-text>
            <div class="d-flex align-center mb-2">
              <v-icon color="primary" class="me-2">{{ statusIcon }}</v-icon>
              <span class="font-weight-medium">{{ statusMessage }}</span>
            </div>
            <v-progress-linear
              :value="progressValue"
              color="primary"
              height="8"
              rounded
              striped
            ></v-progress-linear>
            <div class="text-caption mt-1 text-center">
              {{ progressValue }}% concluído
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Formulário Principal -->
    <v-form
      ref="form"
      v-model="formularioValido"
      @submit.prevent="salvarCliente"
    >
      <!-- Tipo de Pessoa -->
      <v-card class="mb-4" elevation="3">
        <v-card-title class="bg-primary text-white">
          <v-icon class="me-2">mdi-account-group</v-icon>
          Tipo de Pessoa
        </v-card-title>
        <v-card-text class="pa-4">
          <v-radio-group
            v-model="cliente.tipo_pessoa"
            row
            :rules="[v => !!v || 'Selecione o tipo de pessoa']"
          >
            <v-radio
              label="Pessoa Física"
              value="fisica"
              color="primary"
              class="me-4"
            ></v-radio>
            <v-radio
              label="Pessoa Jurídica"
              value="juridica"
              color="primary"
            ></v-radio>
          </v-radio-group>
        </v-card-text>
      </v-card>

      <!-- Dados Pessoais/Empresariais -->
      <v-card class="mb-4" elevation="3">
        <v-card-title class="bg-green text-white">
          <v-icon class="me-2">mdi-account-details</v-icon>
          {{
            cliente.tipo_pessoa === 'fisica'
              ? 'Dados Pessoais'
              : 'Dados da Empresa'
          }}
        </v-card-title>
        <v-card-text class="pa-4">
          <!-- Pessoa Física -->
          <div v-if="cliente.tipo_pessoa === 'fisica'">
            <!-- Nome e Sobrenome -->
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="cliente.primeiro_nome"
                  label="Nome *"
                  variant="outlined"
                  density="comfortable"
                  :rules="nomeRules"
                  prepend-inner-icon="mdi-account"
                  hint="Digite apenas o primeiro nome"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="cliente.sobrenome"
                  label="Sobrenome *"
                  variant="outlined"
                  density="comfortable"
                  :rules="sobrenomeRules"
                  prepend-inner-icon="mdi-account-outline"
                  hint="Digite o sobrenome completo"
                  persistent-hint
                ></v-text-field>
              </v-col>
            </v-row>

            <!-- Nacionalidade e Estado Civil -->
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="cliente.nacionalidade"
                  :items="nacionalidades"
                  label="Nacionalidade"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-earth"
                ></v-select>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="cliente.estado_civil"
                  :items="estadosCivis"
                  label="Estado Civil"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-heart"
                ></v-select>
              </v-col>
            </v-row>

            <!-- Profissão -->
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="cliente.profissao"
                  label="Profissão"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-briefcase"
                  hint="Ex: Advogado, Engenheiro, Estudante, etc."
                  persistent-hint
                ></v-text-field>
              </v-col>
            </v-row>
          </div>

          <!-- Pessoa Jurídica -->
          <div v-if="cliente.tipo_pessoa === 'juridica'">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="cliente.razao_social"
                  label="Razão Social *"
                  variant="outlined"
                  density="comfortable"
                  :rules="razaoSocialRules"
                  prepend-inner-icon="mdi-domain"
                  hint="Nome completo da empresa conforme CNPJ"
                  persistent-hint
                ></v-text-field>
              </v-col>
            </v-row>
          </div>
        </v-card-text>
      </v-card>

      <!-- Endereço -->
      <v-card class="mb-4" elevation="3">
        <v-card-title class="bg-blue text-white">
          <v-icon class="me-2">mdi-map-marker</v-icon>
          Endereço
        </v-card-title>
        <v-card-text class="pa-4">
          <!-- CEP -->
          <v-row>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="cliente.endereco_cep"
                label="CEP *"
                variant="outlined"
                density="comfortable"
                :rules="cepRules"
                :loading="buscandoCep"
                @input="formatarCep"
                @blur="buscarCep"
                prepend-inner-icon="mdi-mailbox"
                hint="Digite o CEP para buscar automaticamente"
                persistent-hint
              >
                <template v-slot:append-inner>
                  <v-icon v-if="enderecoEncontrado" color="success"
                    >mdi-check-circle</v-icon
                  >
                </template>
              </v-text-field>
            </v-col>
            <v-col cols="12" md="8">
              <v-text-field
                v-model="cliente.endereco_logradouro"
                label="Logradouro *"
                variant="outlined"
                density="comfortable"
                :rules="logradouroRules"
                prepend-inner-icon="mdi-road"
                hint="Rua, avenida, etc."
                persistent-hint
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- Número, Complemento e Bairro -->
          <v-row>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="cliente.endereco_numero"
                label="Número *"
                variant="outlined"
                density="comfortable"
                :rules="numeroRules"
                prepend-inner-icon="mdi-numeric"
                hint="Número da residência"
                persistent-hint
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="5">
              <v-text-field
                v-model="cliente.endereco_complemento"
                label="Complemento"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-home-plus"
                hint="Apto, bloco, etc. (opcional)"
                persistent-hint
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="cliente.endereco_bairro"
                label="Bairro *"
                variant="outlined"
                density="comfortable"
                :rules="bairroRules"
                prepend-inner-icon="mdi-map"
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- Cidade e Estado -->
          <v-row>
            <v-col cols="12" md="8">
              <v-text-field
                v-model="cliente.endereco_cidade"
                label="Cidade *"
                variant="outlined"
                density="comfortable"
                :rules="cidadeRules"
                prepend-inner-icon="mdi-city"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="4">
              <v-select
                v-model="cliente.endereco_estado"
                :items="estados"
                label="Estado *"
                variant="outlined"
                density="comfortable"
                :rules="estadoRules"
                prepend-inner-icon="mdi-map-outline"
              ></v-select>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Documentos e Contato -->
      <v-card class="mb-4" elevation="3">
        <v-card-title class="bg-orange text-white">
          <v-icon class="me-2">mdi-card-account-details</v-icon>
          Documentos e Contato
        </v-card-title>
        <v-card-text class="pa-4">
          <!-- Pessoa Física -->
          <div v-if="cliente.tipo_pessoa === 'fisica'">
            <!-- Data de Nascimento e CPF -->
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="cliente.data_nascimento"
                  label="Data de Nascimento *"
                  variant="outlined"
                  density="comfortable"
                  :rules="dataNascimentoRules"
                  @input="formatarDataNascimento"
                  prepend-inner-icon="mdi-calendar"
                  hint="DD/MM/AAAA"
                  persistent-hint
                  placeholder="DD/MM/AAAA"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="cliente.cpf"
                  label="CPF *"
                  variant="outlined"
                  density="comfortable"
                  :rules="cpfRules"
                  @input="formatarCpf"
                  prepend-inner-icon="mdi-card-account-details-outline"
                  hint="XXX.XXX.XXX-XX"
                  persistent-hint
                  placeholder="000.000.000-00"
                ></v-text-field>
              </v-col>
            </v-row>

            <!-- RG e Estado Emissor -->
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="cliente.rg_numero"
                  label="RG"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-card-text"
                  hint="Número do RG (opcional)"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="cliente.rg_uf_emissor"
                  :items="estados"
                  label="Estado Emissor do RG"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-map-marker-outline"
                  hint="Estado que emitiu o RG"
                  persistent-hint
                ></v-select>
              </v-col>
            </v-row>

            <!-- CNH -->
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="cliente.cnh_numero"
                  label="CNH"
                  variant="outlined"
                  density="comfortable"
                  @input="formatarCnh"
                  prepend-inner-icon="mdi-car"
                  hint="Número da CNH - 11 dígitos (opcional)"
                  persistent-hint
                  placeholder="00000000000"
                ></v-text-field>
              </v-col>
            </v-row>
          </div>

          <!-- Pessoa Jurídica -->
          <div v-if="cliente.tipo_pessoa === 'juridica'">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="cliente.cnpj"
                  label="CNPJ *"
                  variant="outlined"
                  density="comfortable"
                  :rules="cnpjRules"
                  @input="formatarCnpj"
                  prepend-inner-icon="mdi-domain"
                  hint="XX.XXX.XXX/XXXX-XX"
                  persistent-hint
                  placeholder="00.000.000/0000-00"
                ></v-text-field>
              </v-col>
            </v-row>
          </div>

          <!-- Email e Telefones (comum para ambos) -->
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="cliente.email"
                label="Email *"
                type="email"
                variant="outlined"
                density="comfortable"
                :rules="emailRules"
                prepend-inner-icon="mdi-email"
                hint="Email principal para contato"
                persistent-hint
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="cliente.telefone_celular"
                label="Telefone Celular *"
                variant="outlined"
                density="comfortable"
                :rules="celularRules"
                @input="formatarTelefoneCelular"
                prepend-inner-icon="mdi-cellphone"
                hint="(XX) XXXXX-XXXX"
                persistent-hint
                placeholder="(00) 00000-0000"
              ></v-text-field>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="cliente.telefone_outro"
                label="Telefone Adicional"
                variant="outlined"
                density="comfortable"
                @input="formatarTelefoneOutro"
                prepend-inner-icon="mdi-phone"
                hint="Telefone fixo ou adicional (opcional)"
                persistent-hint
                placeholder="(00) 0000-0000 ou (00) 00000-0000"
              ></v-text-field>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Botões de Ação -->
      <v-card elevation="2">
        <v-card-actions class="pa-4">
          <v-btn
            variant="outlined"
            size="large"
            @click="limparFormulario"
            :disabled="processando"
            prepend-icon="mdi-refresh"
            class="me-2"
          >
            Limpar
          </v-btn>

          <v-spacer></v-spacer>

          <v-btn
            color="primary"
            size="large"
            type="submit"
            :loading="processando"
            :disabled="!formularioValido"
            prepend-icon="mdi-content-save"
            class="px-8"
          >
            {{ processando ? 'Processando...' : 'Salvar Cliente' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-form>

    <!-- Snackbar de Mensagens -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="top"
      multi-line
    >
      <div class="d-flex align-center">
        <v-icon class="me-2">{{ snackbar.icon }}</v-icon>
        <div>
          <div class="font-weight-bold">{{ snackbar.title }}</div>
          <div class="text-caption">{{ snackbar.message }}</div>
        </div>
      </div>
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="snackbar.show = false"
          icon="mdi-close"
        ></v-btn>
      </template>
    </v-snackbar>

    <!-- Dialog de Sucesso -->
    <v-dialog v-model="sucessoDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="text-h5 text-center py-6">
          <v-icon color="success" size="64" class="mb-4"
            >mdi-check-circle</v-icon
          >
          <br />
          Cliente Cadastrado!
        </v-card-title>
        <v-card-text class="text-center">
          <p class="text-h6 mb-2">
            {{ nomeCompleto }} foi cadastrado com sucesso!
          </p>
          <p class="text-body-2 mb-4">
            <v-icon color="success" size="16" class="me-1"
              >mdi-folder-google-drive</v-icon
            >
            Pasta criada no Google Drive: <strong>{{ nomePastaDrive }}</strong>
          </p>
          <p class="text-caption text-medium-emphasis">
            Agora você pode gerar documentos para este cliente.
          </p>
        </v-card-text>
        <v-card-actions class="justify-center pb-6">
          <v-btn
            color="primary"
            variant="flat"
            size="large"
            @click="fecharSucesso"
            prepend-icon="mdi-check"
          >
            Continuar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { clienteService, googleDriveService } from '@/services/api';

export default {
  name: 'CadastroClienteView',
  data() {
    return {
      formularioValido: false,
      processando: false,
      buscandoCep: false,
      enderecoEncontrado: false,
      progressValue: 0,
      statusMessage: '',
      statusIcon: 'mdi-cloud-upload',
      sucessoDialog: false,
      nomeCompleto: '',
      nomePastaDrive: '',

      cliente: {
        tipo_pessoa: 'fisica',
        primeiro_nome: '',
        sobrenome: '',
        nacionalidade: 'Brasileiro(a)',
        estado_civil: '',
        profissao: '',
        razao_social: '',
        endereco_cep: '',
        endereco_logradouro: '',
        endereco_numero: '',
        endereco_complemento: '',
        endereco_bairro: '',
        endereco_cidade: '',
        endereco_estado: '',
        data_nascimento: '',
        cpf: '',
        rg_numero: '',
        rg_uf_emissor: '',
        cnh_numero: '',
        cnpj: '',
        email: '',
        telefone_celular: '',
        telefone_outro: '',
      },

      snackbar: {
        show: false,
        message: '',
        title: '',
        color: 'success',
        timeout: 5000,
        icon: 'mdi-check-circle',
      },

      nacionalidades: [
        'Brasileiro(a)',
        'Argentino(a)',
        'Boliviano(a)',
        'Chileno(a)',
        'Colombiano(a)',
        'Equatoriano(a)',
        'Paraguaio(a)',
        'Peruano(a)',
        'Uruguaio(a)',
        'Venezuelano(a)',
        'Americano(a)',
        'Canadense',
        'Mexicano(a)',
        'Alemão/Alemã',
        'Espanhol(a)',
        'Francês/Francesa',
        'Inglês/Inglesa',
        'Italiano(a)',
        'Português/Portuguesa',
        'Chinês/Chinesa',
        'Japonês/Japonesa',
        'Coreano(a)',
        'Outro',
      ],

      estadosCivis: [
        'Solteiro(a)',
        'Casado(a)',
        'Divorciado(a)',
        'Viúvo(a)',
        'União Estável',
        'Separado(a)',
      ],

      estados: [
        'AC',
        'AL',
        'AP',
        'AM',
        'BA',
        'CE',
        'DF',
        'ES',
        'GO',
        'MA',
        'MT',
        'MS',
        'MG',
        'PA',
        'PB',
        'PR',
        'PE',
        'PI',
        'RJ',
        'RN',
        'RS',
        'RO',
        'RR',
        'SC',
        'SP',
        'SE',
        'TO',
      ],
    };
  },

  computed: {
    // Regras de validação
    nomeRules() {
      return [
        v => !!v || 'Nome é obrigatório',
        v => (v && v.length >= 2) || 'Nome deve ter pelo menos 2 caracteres',
      ];
    },
    sobrenomeRules() {
      return [
        v => !!v || 'Sobrenome é obrigatório',
        v =>
          (v && v.length >= 2) || 'Sobrenome deve ter pelo menos 2 caracteres',
      ];
    },
    razaoSocialRules() {
      return [
        v => !!v || 'Razão Social é obrigatória',
        v =>
          (v && v.length >= 3) ||
          'Razão Social deve ter pelo menos 3 caracteres',
      ];
    },
    cepRules() {
      return [
        v => !!v || 'CEP é obrigatório',
        v =>
          (v && v.replace(/\D/g, '').length === 8) || 'CEP deve ter 8 dígitos',
      ];
    },
    logradouroRules() {
      return [v => !!v || 'Logradouro é obrigatório'];
    },
    numeroRules() {
      return [v => !!v || 'Número é obrigatório'];
    },
    bairroRules() {
      return [v => !!v || 'Bairro é obrigatório'];
    },
    cidadeRules() {
      return [v => !!v || 'Cidade é obrigatória'];
    },
    estadoRules() {
      return [v => !!v || 'Estado é obrigatório'];
    },
    dataNascimentoRules() {
      return [
        v => !!v || 'Data de nascimento é obrigatória',
        v => this.validarDataNascimento(v) || 'Data inválida (DD/MM/AAAA)',
      ];
    },
    cpfRules() {
      return [
        v => !!v || 'CPF é obrigatório',
        v => this.validarCpf(v) || 'CPF inválido',
      ];
    },
    cnpjRules() {
      return [
        v => !!v || 'CNPJ é obrigatório',
        v =>
          (v && v.replace(/\D/g, '').length === 14) ||
          'CNPJ deve ter 14 dígitos',
      ];
    },
    emailRules() {
      return [
        v => !!v || 'Email é obrigatório',
        v => /.+@.+\..+/.test(v) || 'Email deve ser válido',
      ];
    },
    celularRules() {
      return [
        v => !!v || 'Telefone celular é obrigatório',
        v =>
          (v && v.replace(/\D/g, '').length >= 10) ||
          'Telefone deve ter pelo menos 10 dígitos',
      ];
    },
  },

  mounted() {
    this.carregarCache();
  },

  watch: {
    'cliente.email'() {
      this.salvarCache(this.cliente);
    },
    'cliente.cpf'() {
      this.salvarCache(this.cliente);
    },
    'cliente.cnpj'() {
      this.salvarCache(this.cliente);
    },
    'cliente.primeiro_nome'() {
      this.salvarCache(this.cliente);
    },
    'cliente.sobrenome'() {
      this.salvarCache(this.cliente);
    },
    'cliente.razao_social'() {
      this.salvarCache(this.cliente);
    },
    'cliente.telefone_celular'() {
      this.salvarCache(this.cliente);
    },
  },

  methods: {
    async salvarCliente() {
      const { valid } = await this.$refs.form.validate();
      if (!valid) {
        this.mostrarMensagem(
          'Erro',
          'Corrija os campos destacados',
          'error',
          'mdi-alert-circle'
        );
        return;
      }

      try {
        this.processando = true;

        // Etapa 1: Validação
        this.progressValue = 20;
        this.statusMessage = 'Validando dados...';
        this.statusIcon = 'mdi-check-circle';
        await this.sleep(800);

        // Etapa 2: Preparar dados
        this.progressValue = 40;
        this.statusMessage = 'Preparando dados...';
        this.statusIcon = 'mdi-cog';
        const dadosCliente = this.prepararDadosCliente();
        await this.sleep(800);

        // Etapa 3: Salvar
        this.progressValue = 70;
        this.statusMessage = 'Salvando no banco...';
        this.statusIcon = 'mdi-database';
        const response = await this.salvarNoBanco(dadosCliente);
        await this.sleep(800);

        // Etapa 4: Google Drive
        this.progressValue = 90;
        this.statusMessage = 'Criando pasta Google Drive...';
        this.statusIcon = 'mdi-google-drive';
        await this.criarPastaGoogleDrive(response.cliente);
        await this.sleep(500);

        // Finalizar
        this.progressValue = 100;
        this.statusMessage = 'Concluído!';
        this.statusIcon = 'mdi-check-circle';
        await this.sleep(500);

        this.nomeCompleto =
          this.cliente.tipo_pessoa === 'fisica'
            ? `${this.cliente.primeiro_nome} ${this.cliente.sobrenome}`
            : this.cliente.razao_social;

        this.sucessoDialog = true;
        this.limparCache();
      } catch (error) {
        console.error('Erro:', error);
        this.mostrarMensagem(
          'Erro',
          error.message || 'Erro ao cadastrar cliente',
          'error',
          'mdi-alert-circle'
        );
      } finally {
        this.processando = false;
        this.progressValue = 0;
      }
    },

    prepararDadosCliente() {
      const dados = { ...this.cliente };
      if (dados.cpf) dados.cpf = dados.cpf.replace(/\D/g, '');
      if (dados.cnpj) dados.cnpj = dados.cnpj.replace(/\D/g, '');
      if (dados.endereco_cep)
        dados.endereco_cep = dados.endereco_cep.replace(/\D/g, '');
      if (dados.telefone_celular)
        dados.telefone_celular = dados.telefone_celular.replace(/\D/g, '');
      if (dados.telefone_outro)
        dados.telefone_outro = dados.telefone_outro.replace(/\D/g, '');
      if (dados.cnh_numero)
        dados.cnh_numero = dados.cnh_numero.replace(/\D/g, '');
      return dados;
    },

    async salvarNoBanco(dadosCliente) {
      return await clienteService.criar(dadosCliente);
    },

    async criarPastaGoogleDrive(cliente) {
      const anoAtual = new Date().getFullYear();
      const nomePasta =
        cliente.tipo_pessoa === 'fisica'
          ? `[${anoAtual}]-${cliente.primeiro_nome} ${cliente.sobrenome}`
          : `[${anoAtual}]-${cliente.razao_social}`;

      this.nomePastaDrive = nomePasta;

      try {
        await googleDriveService.criarPasta(nomePasta, cliente.id);
      } catch (error) {
        console.warn('Erro ao criar pasta:', error);
        throw error;
      }
    },

    async buscarCep() {
      const cep = this.cliente.endereco_cep.replace(/\D/g, '');
      if (cep.length !== 8) {
        this.enderecoEncontrado = false;
        return;
      }

      try {
        this.buscandoCep = true;
        this.enderecoEncontrado = false;

        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();

        if (data.erro) {
          this.mostrarMensagem(
            'Aviso',
            'CEP não encontrado',
            'warning',
            'mdi-alert'
          );
          return;
        }

        if (data.logradouro) {
          this.cliente.endereco_logradouro = data.logradouro;
          this.cliente.endereco_bairro = data.bairro;
          this.cliente.endereco_cidade = data.localidade;
          this.cliente.endereco_estado = data.uf;
          this.enderecoEncontrado = true;
          this.mostrarMensagem(
            'Sucesso',
            'Endereço preenchido!',
            'success',
            'mdi-check-circle'
          );
        }
      } catch (error) {
        console.error('Erro CEP:', error);
        this.mostrarMensagem(
          'Erro',
          'Erro ao buscar CEP',
          'error',
          'mdi-wifi-off'
        );
      } finally {
        this.buscandoCep = false;
      }
    },

    // Formatadores
    formatarCpf() {
      let cpf = this.cliente.cpf.replace(/\D/g, '');
      if (cpf.length <= 11) {
        cpf = cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
        this.cliente.cpf = cpf;
      }
    },

    formatarCnpj() {
      let cnpj = this.cliente.cnpj.replace(/\D/g, '');
      if (cnpj.length <= 14) {
        cnpj = cnpj.replace(
          /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
          '$1.$2.$3/$4-$5'
        );
        this.cliente.cnpj = cnpj;
      }
    },

    formatarCep() {
      let cep = this.cliente.endereco_cep.replace(/\D/g, '');
      if (cep.length <= 8) {
        cep = cep.replace(/(\d{5})(\d{3})/, '$1-$2');
        this.cliente.endereco_cep = cep;
      }
    },

    formatarTelefoneCelular() {
      let telefone = this.cliente.telefone_celular.replace(/\D/g, '');
      if (telefone.length <= 11) {
        if (telefone.length === 11) {
          telefone = telefone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
        } else if (telefone.length === 10) {
          telefone = telefone.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
        }
        this.cliente.telefone_celular = telefone;
      }
    },

    formatarTelefoneOutro() {
      let telefone = this.cliente.telefone_outro.replace(/\D/g, '');
      if (telefone.length <= 11) {
        if (telefone.length === 11) {
          telefone = telefone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
        } else if (telefone.length === 10) {
          telefone = telefone.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
        }
        this.cliente.telefone_outro = telefone;
      }
    },

    formatarDataNascimento() {
      let data = this.cliente.data_nascimento.replace(/\D/g, '');
      if (data.length <= 8) {
        data = data.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3');
        this.cliente.data_nascimento = data;
      }
    },

    formatarCnh() {
      let cnh = this.cliente.cnh_numero.replace(/\D/g, '');
      if (cnh.length <= 11) {
        this.cliente.cnh_numero = cnh;
      }
    },

    // Validadores
    validarCpf(cpf) {
      if (!cpf) return false;
      cpf = cpf.replace(/\D/g, '');
      
      if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
      
      // Validação dos dígitos verificadores
      let soma = 0;
      for (let i = 0; i < 9; i++) {
        soma += parseInt(cpf.charAt(i)) * (10 - i);
      }
      let resto = 11 - (soma % 11);
      let dv1 = resto < 2 ? 0 : resto;
      
      soma = 0;
      for (let i = 0; i < 10; i++) {
        soma += parseInt(cpf.charAt(i)) * (11 - i);
      }
      resto = 11 - (soma % 11);
      let dv2 = resto < 2 ? 0 : resto;
      
      return parseInt(cpf.charAt(9)) === dv1 && parseInt(cpf.charAt(10)) === dv2;
    },

    validarDataNascimento(data) {
      if (!data) return false;
      const regex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
      const match = data.match(regex);
      if (!match) return false;
      const dia = parseInt(match[1]);
      const mes = parseInt(match[2]);
      const ano = parseInt(match[3]);
      return (
        dia >= 1 &&
        dia <= 31 &&
        mes >= 1 &&
        mes <= 12 &&
        ano >= 1900 &&
        ano <= new Date().getFullYear()
      );
    },

    // Cache
    salvarCache(dados) {
      try {
        sessionStorage.setItem('cadastro_cliente_cache', JSON.stringify(dados));
      } catch (error) {
        console.warn('Erro ao salvar cache:', error);
      }
    },

    carregarCache() {
      try {
        const cache = sessionStorage.getItem('cadastro_cliente_cache');
        if (cache) {
          const dados = JSON.parse(cache);
          if (dados.primeiro_nome || dados.razao_social || dados.email) {
            this.cliente = { ...this.cliente, ...dados };
            this.mostrarMensagem(
              'Info',
              'Dados anteriores carregados',
              'info',
              'mdi-information'
            );
          }
        }
      } catch (error) {
        console.warn('Erro ao carregar cache:', error);
      }
    },

    limparCache() {
      try {
        sessionStorage.removeItem('cadastro_cliente_cache');
      } catch (error) {
        console.warn('Erro ao limpar cache:', error);
      }
    },

    limparFormulario() {
      this.$refs.form.reset();
      this.cliente = {
        tipo_pessoa: 'fisica',
        primeiro_nome: '',
        sobrenome: '',
        nacionalidade: 'Brasileiro(a)',
        estado_civil: '',
        profissao: '',
        razao_social: '',
        endereco_cep: '',
        endereco_logradouro: '',
        endereco_numero: '',
        endereco_complemento: '',
        endereco_bairro: '',
        endereco_cidade: '',
        endereco_estado: '',
        data_nascimento: '',
        cpf: '',
        rg_numero: '',
        rg_uf_emissor: '',
        cnh_numero: '',
        cnpj: '',
        email: '',
        telefone_celular: '',
        telefone_outro: '',
      };
      this.enderecoEncontrado = false;
      this.limparCache();
    },

    fecharSucesso() {
      this.sucessoDialog = false;
      this.limparFormulario();
      this.$emit('cliente-cadastrado');
    },

    mostrarMensagem(
      title,
      message,
      color = 'success',
      icon = 'mdi-check-circle'
    ) {
      this.snackbar = {
        show: true,
        title,
        message,
        color,
        icon,
      };
    },

    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },
  },
};
</script>

<style scoped>
.v-container {
  max-width: 1200px;
}

.v-card {
  transition: all 0.3s ease;
}

.v-progress-linear {
  border-radius: 4px;
}

@media (max-width: 600px) {
  .v-container {
    padding: 8px !important;
  }

  .v-card-actions {
    flex-direction: column;
    gap: 12px;
  }

  .v-btn {
    width: 100%;
  }

  .v-spacer {
    display: none;
  }
}
</style>
