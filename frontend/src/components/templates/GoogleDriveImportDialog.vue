<template>
  <v-dialog v-model="dialog" max-width="600" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon left color="success">mdi-google-drive</v-icon>
        Importar Templates do Google Drive
        <v-spacer></v-spacer>
        <v-btn icon @click="closeDialog" :disabled="importing">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-form ref="form" v-model="formValid">
          <v-text-field
            v-model="folderId"
            label="ID da Pasta no Google Drive"
            placeholder="1ABC123xyz..."
            :rules="folderIdRules"
            outlined
            required
            hint="Cole aqui o ID da pasta que contém os templates"
            persistent-hint
          >
            <template v-slot:prepend-inner>
              <v-icon>mdi-folder-google-drive</v-icon>
            </template>
          </v-text-field>

          <v-checkbox
            v-model="autoDetectFields"
            label="Detectar campos automaticamente"
            hint="Analisar documentos e identificar placeholders"
            persistent-hint
          ></v-checkbox>

          <div v-if="scanning" class="text-center py-4">
            <v-progress-circular
              indeterminate
              color="primary"
              size="64"
            ></v-progress-circular>
            <div class="mt-3">
              <strong>Escaneando pasta...</strong>
            </div>
            <div class="text-caption">Isso pode levar alguns segundos</div>
          </div>

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
        <v-btn
          @click="scanFolder"
          :loading="scanning"
          :disabled="!folderId || importing"
          color="info"
          outlined
        >
          <v-icon left>mdi-magnify</v-icon>
          Escanear Pasta
        </v-btn>

        <v-spacer></v-spacer>

        <v-btn @click="closeDialog" :disabled="importing" text>
          Cancelar
        </v-btn>

        <v-btn
          @click="importSelected"
          :loading="importing"
          :disabled="!formValid"
          color="success"
        >
          <v-icon left>mdi-download</v-icon>
          Importar
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';

export default {
  name: 'GoogleDriveImportDialog',
  props: {
    value: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      dialog: false,
      folderId: '',
      autoDetectFields: true,
      formValid: false,
      scanning: false,
      importing: false,
      error: null,
      folderIdRules: [
        v => !!v || 'ID da pasta é obrigatório',
        v => (v && v.length >= 10) || 'ID deve ter pelo menos 10 caracteres',
      ],
    };
  },
  watch: {
    value(newVal) {
      this.dialog = newVal;
      if (newVal) {
        this.resetDialog();
      }
    },
    dialog(newVal) {
      this.$emit('input', newVal);
    },
  },
  methods: {
    async scanFolder() {
      if (!this.folderId) return;
      this.scanning = true;
      this.error = null;
      setTimeout(() => {
        this.scanning = false;
      }, 2000);
    },
    async importSelected() {
      this.importing = true;
      this.error = null;
      try {
        const token = localStorage.getItem('token');
        const response = await axios.post(
          '/admin/templates/import-drive',
          {
            folder_id: this.folderId,
            auto_detect_fields: this.autoDetectFields,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        this.$emit('imported', response.data.imported_templates);
        this.closeDialog();
      } catch (error) {
        console.error('Erro ao importar templates:', error);
        this.error =
          error.response?.data?.message || 'Erro ao importar templates';
      } finally {
        this.importing = false;
      }
    },
    closeDialog() {
      if (!this.importing) {
        this.dialog = false;
        this.resetDialog();
      }
    },
    resetDialog() {
      this.folderId = '';
      this.autoDetectFields = true;
      this.error = null;
      this.scanning = false;
      this.importing = false;
      if (this.$refs.form) {
        this.$refs.form.resetValidation();
      }
    },
  },
};
</script>
