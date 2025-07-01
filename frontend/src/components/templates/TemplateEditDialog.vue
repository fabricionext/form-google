<template>
  <v-dialog v-model="dialog" max-width="800" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon left color="primary">mdi-pencil</v-icon>
        {{ template ? 'Editar Template' : 'Novo Template' }}
        <v-spacer></v-spacer>
        <v-btn icon @click="closeDialog" :disabled="saving">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-form ref="form" v-model="formValid">
          <v-text-field
            v-model="templateData.nome"
            label="Nome do Template"
            :rules="nameRules"
            outlined
            required
          ></v-text-field>

          <v-textarea
            v-model="templateData.descricao"
            label="Descrição"
            rows="3"
            outlined
          ></v-textarea>

          <v-select
            v-model="templateData.categoria"
            :items="categories"
            label="Categoria"
            outlined
            required
          ></v-select>

          <v-text-field
            v-model="templateData.google_doc_id"
            label="ID do Google Docs"
            :rules="docIdRules"
            outlined
            required
          ></v-text-field>

          <v-text-field
            v-model="templateData.pasta_destino_id"
            label="ID da Pasta de Destino"
            outlined
          ></v-text-field>

          <v-select
            v-model="templateData.status"
            :items="statusOptions"
            label="Status"
            outlined
            required
          ></v-select>

          <v-alert
            v-if="error"
            type="error"
            dense
            dismissible
            @input="error = null"
          >
            {{ error }}
          </v-alert>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-btn @click="closeDialog" :disabled="saving" text> Cancelar </v-btn>

        <v-spacer></v-spacer>

        <v-btn
          @click="saveTemplate"
          :loading="saving"
          :disabled="!formValid"
          color="primary"
        >
          <v-icon left>mdi-content-save</v-icon>
          {{ template ? 'Atualizar' : 'Criar' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';

export default {
  name: 'TemplateEditDialog',
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    template: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      dialog: false,
      formValid: false,
      saving: false,
      error: null,
      templateData: {
        nome: '',
        descricao: '',
        categoria: '',
        google_doc_id: '',
        pasta_destino_id: '',
        status: 'ativo',
      },
      categories: [
        { text: 'Petições Iniciais', value: 'peticoes_iniciais' },
        { text: 'Recursos', value: 'recursos' },
        { text: 'Contestações', value: 'contestacoes' },
        { text: 'Embargos', value: 'embargos' },
        { text: 'Administrativo', value: 'administrativo' },
      ],
      statusOptions: [
        { text: 'Ativo', value: 'ativo' },
        { text: 'Inativo', value: 'inativo' },
        { text: 'Rascunho', value: 'rascunho' },
      ],
      nameRules: [
        v => !!v || 'Nome é obrigatório',
        v => (v && v.length >= 3) || 'Nome deve ter pelo menos 3 caracteres',
      ],
      docIdRules: [
        v => !!v || 'ID do Google Docs é obrigatório',
        v => (v && v.length >= 10) || 'ID deve ter pelo menos 10 caracteres',
      ],
    };
  },
  watch: {
    value(newVal) {
      this.dialog = newVal;
      if (newVal) {
        this.loadTemplateData();
      }
    },
    dialog(newVal) {
      this.$emit('input', newVal);
    },
    template() {
      if (this.dialog) {
        this.loadTemplateData();
      }
    },
  },
  methods: {
    loadTemplateData() {
      if (this.template) {
        this.templateData = {
          nome: this.template.nome || '',
          descricao: this.template.descricao || '',
          categoria: this.template.categoria || '',
          google_doc_id: this.template.google_doc_id || '',
          pasta_destino_id: this.template.pasta_destino_id || '',
          status: this.template.status || 'ativo',
        };
      } else {
        this.resetForm();
      }
    },
    async saveTemplate() {
      this.saving = true;
      this.error = null;
      try {
        const token = localStorage.getItem('token');
        let response;
        if (this.template) {
          response = await axios.put(
            `/admin/templates/${this.template.id}`,
            this.templateData,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );
        } else {
          response = await axios.post('/admin/templates', this.templateData, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
        }
        this.$emit('updated', response.data.template);
        this.closeDialog();
      } catch (error) {
        console.error('Erro ao salvar template:', error);
        this.error = error.response?.data?.message || 'Erro ao salvar template';
      } finally {
        this.saving = false;
      }
    },
    closeDialog() {
      if (!this.saving) {
        this.dialog = false;
        this.resetForm();
      }
    },
    resetForm() {
      this.templateData = {
        nome: '',
        descricao: '',
        categoria: '',
        google_doc_id: '',
        pasta_destino_id: '',
        status: 'ativo',
      };
      this.error = null;
      if (this.$refs.form) {
        this.$refs.form.resetValidation();
      }
    },
  },
};
</script>
