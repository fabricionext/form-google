<template>
  <v-container fluid>
    <!-- Header com Ações Rápidas -->
    <v-row class="mb-4">
      <v-col cols="12" md="8">
        <h2 class="text-h4 font-weight-bold">
          <v-icon left color="primary">mdi-google-drive</v-icon>
          Gerenciador de Templates
        </h2>
      </v-col>
      <v-col cols="12" md="4" class="text-right">
        <v-btn
          v-if="isEditor"
          color="success"
          @click="importDialog = true"
          class="mr-2"
        >
          <v-icon left>mdi-cloud-download</v-icon>
          Importar do Drive
        </v-btn>
        <v-btn v-if="isEditor" color="primary" @click="createNewTemplate">
          <v-icon left>mdi-plus</v-icon>
          Novo Template
        </v-btn>
      </v-col>
    </v-row>

    <!-- Filtros e Busca -->
    <v-card class="elevation-2 mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Buscar templates..."
              dense
              clearable
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="categoryFilter"
              :items="categories"
              label="Categoria"
              dense
              clearable
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="statusFilter"
              :items="statusOptions"
              label="Status"
              dense
              clearable
            ></v-select>
          </v-col>
          <v-col cols="12" md="2">
            <v-btn outlined block @click="loadTemplates" :loading="loading">
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Grid de Templates -->
    <v-row v-if="loading">
      <v-col v-for="n in 6" :key="n" cols="12" sm="6" lg="4" xl="3">
        <v-skeleton-loader
          type="card-avatar, article, actions"
        ></v-skeleton-loader>
      </v-col>
    </v-row>
    <v-row v-else-if="templates.length > 0">
      <v-col
        v-for="template in templates"
        :key="template.id"
        cols="12"
        sm="6"
        lg="4"
        xl="3"
      >
        <TemplateCard
          :template="template"
          @preview="handlePreview(template)"
          @generate="handleGenerate(template)"
          @edit="handleEdit(template)"
          @sync="handleSync(template)"
          @duplicate="handleDuplicate(template)"
          @delete="handleDelete(template)"
        />
      </v-col>
    </v-row>
    <v-row v-else>
      <v-col cols="12" class="text-center mt-8">
        <v-icon size="64" color="grey lighten-1"
          >mdi-text-box-search-outline</v-icon
        >
        <p class="text-h6 mt-4 grey--text">Nenhum template encontrado.</p>
        <p class="text-body-1 grey--text">
          Tente ajustar seus filtros ou crie um novo template.
        </p>
      </v-col>
    </v-row>

    <!-- Dialogs -->
    <TemplateEditDialog
      v-if="currentTemplate"
      v-model="editDialog"
      :template="currentTemplate"
      @saved="handleTemplateSaved"
    />
    <GoogleDriveImportDialog v-model="importDialog" @import="handleImport" />

    <!-- Snackbar para feedback -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="4000"
      bottom
      right
    >
      {{ snackbar.text }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar.show = false">Fechar</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import * as driveService from '@/services/driveService';
import { api } from '@/plugins/axiosInterceptor';
import TemplateCard from '@/components/templates/TemplateCard.vue';
import GoogleDriveImportDialog from '@/components/templates/GoogleDriveImportDialog.vue';
import TemplateEditDialog from '@/components/templates/TemplateEditDialog.vue';

// Tipos
interface Template {
  id: number;
  nome: string;
  categoria: string;
  status: string;
  thumbnail: string;
  usage_count: number;
  avg_generation_time: number;
  detected_fields: string[];
  syncing: boolean; // Controlado localmente
  last_sync: string | null;
}

// State
const router = useRouter();
const auth = useAuthStore();

const templates = ref<Template[]>([]);
const loading = ref(true);
const search = ref('');
const categoryFilter = ref(null);
const statusFilter = ref(null);

const categories = ref(['Contestações', 'Recursos', 'Embargos', 'Outros']);
const statusOptions = ref(['Ativo', 'Inativo', 'Arquivado']);

const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
});

const editDialog = ref(false);
const importDialog = ref(false);
const currentTemplate = ref<Template | null>(null);

// Computed
const isEditor = computed(() => auth.isEditor || auth.isAdmin);

// Methods
async function loadTemplates() {
  loading.value = true;
  try {
    const params = {
      search: search.value,
      category: categoryFilter.value,
      status: statusFilter.value,
    };
    const response = await api.get('/admin/templates', { params });
    templates.value = response.data.templates.map((t: Template) => ({
      ...t,
      syncing: false,
    }));
  } catch (error) {
    showSnackbar('Erro ao carregar templates.', 'error');
    console.error(error);
  } finally {
    loading.value = false;
  }
}

function showSnackbar(text: string, color = 'success') {
  snackbar.value = { show: true, text, color };
}

// --- Funções de Ação do TemplateCard ---

function handlePreview(template: Template) {
  currentTemplate.value = template;
  console.log('Previewing:', template.nome);
}

function handleGenerate(template: Template) {
  router.push(`/formularios/${template.id}/gerar`);
}

function handleEdit(template: Template) {
  currentTemplate.value = { ...template };
  editDialog.value = true;
}

async function handleSync(template: Template) {
  const t = templates.value.find(t => t.id === template.id);
  if (t) t.syncing = true;

  try {
    await driveService.syncTemplate(template.id);
    showSnackbar(`'${template.nome}' sincronizado com sucesso.`);
    await loadTemplates();
  } catch (error) {
    showSnackbar(`Erro ao sincronizar '${template.nome}'.`, 'error');
    console.error(error);
  } finally {
    if (t) t.syncing = false;
  }
}

async function handleDuplicate(template: Template) {
  try {
    await driveService.duplicateTemplate(template.id);
    showSnackbar(`'${template.nome}' duplicado com sucesso.`);
    await loadTemplates();
  } catch (error) {
    showSnackbar(`Erro ao duplicar '${template.nome}'.`, 'error');
  }
}

async function handleDelete(template: Template) {
  if (
    confirm(`Tem certeza que deseja excluir o template '${template.nome}'?`)
  ) {
    try {
      await driveService.deleteTemplate(template.id);
      showSnackbar(`'${template.nome}' excluído com sucesso.`);
      templates.value = templates.value.filter(t => t.id !== template.id);
    } catch (error) {
      showSnackbar(`Erro ao excluir '${template.nome}'.`, 'error');
    }
  }
}

// --- Funções de Ação da Página ---

function createNewTemplate() {
  currentTemplate.value = {
    id: 0,
    nome: '',
    categoria: 'Outros',
    status: 'Inativo',
    thumbnail: '',
    usage_count: 0,
    avg_generation_time: 0,
    detected_fields: [],
    syncing: false,
    last_sync: null,
  };
  editDialog.value = true;
}

async function handleTemplateSaved() {
  editDialog.value = false;
  showSnackbar('Template salvo com sucesso!');
  await loadTemplates();
}

async function handleImport(fileIds: string[]) {
  importDialog.value = false;
  showSnackbar(`${fileIds.length} template(s) importado(s) com sucesso.`);
  await loadTemplates();
}

// Lifecycle and Watchers
onMounted(loadTemplates);

let debounceTimer: number;
watch([search, categoryFilter, statusFilter], () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    loadTemplates();
  }, 500);
});
</script>

<style scoped>
.template-card {
  transition: all 0.2s ease-in-out;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.template-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
}
.template-thumbnail {
  height: 120px;
  background-size: cover;
  background-position: center;
  position: relative;
  background-color: #f5f5f5;
}
.v-card__text {
  flex-grow: 1;
}
</style>
