<template>
  <div class="document-generation-monitor">
    <!-- Generation Status Card -->
    <div
      v-if="documentGeneration.status"
      class="bg-white rounded-lg border shadow-sm p-6 mb-6"
    >
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">
          Geração de Documento
        </h3>
        <button
          v-if="canClose"
          @click="closeMonitor"
          class="text-gray-400 hover:text-gray-600"
        >
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- Status Content -->
      <div class="space-y-4">
        <!-- Status Badge -->
        <div class="flex items-center space-x-3">
          <div :class="statusBadgeClasses">
            <component :is="statusIcon" class="w-4 h-4 mr-2" />
            {{ statusText }}
          </div>

          <div v-if="documentGeneration.taskId" class="text-sm text-gray-500">
            ID: {{ documentGeneration.taskId }}
          </div>
        </div>

        <!-- Progress Bar -->
        <div v-if="showProgressBar" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600">Progresso</span>
            <span class="font-medium">{{ documentGeneration.progress }}%</span>
          </div>

          <div class="w-full bg-gray-200 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
              :style="{ width: `${documentGeneration.progress}%` }"
            ></div>
          </div>
        </div>

        <!-- Error Message -->
        <div
          v-if="
            documentGeneration.status === 'FAILURE' && documentGeneration.error
          "
          class="bg-red-50 border border-red-200 rounded-md p-4"
        >
          <div class="flex">
            <ExclamationTriangleIcon class="h-5 w-5 text-red-400 mt-0.5" />
            <div class="ml-3">
              <h4 class="text-sm font-medium text-red-800">Erro na Geração</h4>
              <div class="mt-1 text-sm text-red-700">
                {{ documentGeneration.error }}
              </div>
            </div>
          </div>
        </div>

        <!-- Success Message -->
        <div
          v-if="documentGeneration.status === 'SUCCESS'"
          class="bg-green-50 border border-green-200 rounded-md p-4"
        >
          <div class="flex">
            <CheckCircleIcon class="h-5 w-5 text-green-400 mt-0.5" />
            <div class="ml-3">
              <h4 class="text-sm font-medium text-green-800">
                Documento Gerado com Sucesso!
              </h4>
              <div class="mt-1 text-sm text-green-700">
                O documento foi criado e está pronto para download.
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center space-x-3 pt-4">
          <!-- Download Button -->
          <button
            v-if="
              documentGeneration.status === 'SUCCESS' &&
              documentGeneration.downloadUrl
            "
            @click="downloadDocument"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <ArrowDownTrayIcon class="w-4 h-4 mr-2" />
            Download
          </button>

          <!-- View in Drive Button -->
          <button
            v-if="
              documentGeneration.status === 'SUCCESS' &&
              documentGeneration.driveUrl
            "
            @click="openInDrive"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <CloudIcon class="w-4 h-4 mr-2" />
            Ver no Drive
          </button>

          <!-- Retry Button -->
          <button
            v-if="documentGeneration.status === 'FAILURE'"
            @click="retryGeneration"
            :disabled="isRetrying"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <ArrowPathIcon
              class="w-4 h-4 mr-2"
              :class="{ 'animate-spin': isRetrying }"
            />
            {{ isRetrying ? 'Tentando...' : 'Tentar Novamente' }}
          </button>

          <!-- Cancel Button -->
          <button
            v-if="documentGeneration.status === 'PENDING'"
            @click="cancelGeneration"
            class="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <XMarkIcon class="w-4 h-4 mr-2" />
            Cancelar
          </button>
        </div>

        <!-- Generation Details (Expandable) -->
        <div v-if="showDetails" class="pt-4 border-t">
          <button
            @click="toggleDetails"
            class="flex items-center text-sm text-gray-600 hover:text-gray-900"
          >
            <ChevronDownIcon
              class="w-4 h-4 mr-1 transition-transform"
              :class="{ 'rotate-180': detailsExpanded }"
            />
            Detalhes Técnicos
          </button>

          <div v-if="detailsExpanded" class="mt-3 bg-gray-50 rounded-md p-3">
            <dl class="space-y-2 text-sm">
              <div v-if="documentGeneration.taskId">
                <dt class="font-medium text-gray-700">Task ID:</dt>
                <dd class="text-gray-600 font-mono">
                  {{ documentGeneration.taskId }}
                </dd>
              </div>

              <div v-if="documentGeneration.documentId">
                <dt class="font-medium text-gray-700">Document ID:</dt>
                <dd class="text-gray-600 font-mono">
                  {{ documentGeneration.documentId }}
                </dd>
              </div>

              <div v-if="generationStartTime">
                <dt class="font-medium text-gray-700">Iniciado em:</dt>
                <dd class="text-gray-600">
                  {{ formatTime(generationStartTime) }}
                </dd>
              </div>

              <div v-if="generationEndTime">
                <dt class="font-medium text-gray-700">Concluído em:</dt>
                <dd class="text-gray-600">
                  {{ formatTime(generationEndTime) }}
                </dd>
              </div>

              <div v-if="generationDuration">
                <dt class="font-medium text-gray-700">Duração:</dt>
                <dd class="text-gray-600">{{ generationDuration }}s</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>

    <!-- Generation History -->
    <div
      v-if="showHistory && generationHistory.length > 0"
      class="bg-white rounded-lg border shadow-sm p-6"
    >
      <h3 class="text-lg font-semibold text-gray-900 mb-4">
        Histórico de Gerações
      </h3>

      <div class="space-y-3">
        <div
          v-for="(generation, index) in generationHistory"
          :key="generation.taskId || index"
          class="flex items-center justify-between p-3 bg-gray-50 rounded-md"
        >
          <div class="flex items-center space-x-3">
            <div :class="getHistoryStatusClasses(generation.status)">
              <component
                :is="getHistoryStatusIcon(generation.status)"
                class="w-4 h-4"
              />
            </div>

            <div>
              <div class="text-sm font-medium text-gray-900">
                {{ generation.templateName || 'Documento' }}
              </div>
              <div class="text-xs text-gray-500">
                {{ formatTime(generation.timestamp) }}
              </div>
            </div>
          </div>

          <div class="flex items-center space-x-2">
            <button
              v-if="generation.status === 'SUCCESS' && generation.downloadUrl"
              @click="downloadHistoryDocument(generation)"
              class="text-blue-600 hover:text-blue-800 text-sm"
            >
              Download
            </button>

            <button
              v-if="generation.status === 'FAILURE'"
              @click="retryHistoryGeneration(generation)"
              class="text-gray-600 hover:text-gray-800 text-sm"
            >
              Tentar Novamente
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import {
  CheckCircleIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon,
  CloudIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ClockIcon,
  XCircleIcon,
} from '@heroicons/vue/24/outline';
import { useFormularioStore } from '../stores/formulario.js';
import { documentsAPI } from '../services/api.js';

// Props
const props = defineProps({
  autoClose: {
    type: Boolean,
    default: false,
  },
  showHistory: {
    type: Boolean,
    default: true,
  },
  refreshInterval: {
    type: Number,
    default: 2000, // 2 seconds
  },
});

// Emits
const emit = defineEmits([
  'document-downloaded',
  'generation-cancelled',
  'monitor-closed',
]);

// Store
const store = useFormularioStore();

// Local state
const isRetrying = ref(false);
const detailsExpanded = ref(false);
const generationStartTime = ref(null);
const generationEndTime = ref(null);
const generationHistory = ref([]);
const refreshTimer = ref(null);

// Computed properties
const documentGeneration = computed(() => store.documentGeneration);

const statusText = computed(() => {
  switch (documentGeneration.value.status) {
    case 'PENDING':
      return 'Gerando documento...';
    case 'SUCCESS':
      return 'Documento gerado com sucesso';
    case 'FAILURE':
      return 'Falha na geração';
    default:
      return 'Aguardando...';
  }
});

const statusIcon = computed(() => {
  switch (documentGeneration.value.status) {
    case 'PENDING':
      return ClockIcon;
    case 'SUCCESS':
      return CheckCircleIcon;
    case 'FAILURE':
      return XCircleIcon;
    default:
      return ClockIcon;
  }
});

const statusBadgeClasses = computed(() => {
  const baseClasses =
    'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium';

  switch (documentGeneration.value.status) {
    case 'PENDING':
      return `${baseClasses} bg-yellow-100 text-yellow-800`;
    case 'SUCCESS':
      return `${baseClasses} bg-green-100 text-green-800`;
    case 'FAILURE':
      return `${baseClasses} bg-red-100 text-red-800`;
    default:
      return `${baseClasses} bg-gray-100 text-gray-800`;
  }
});

const showProgressBar = computed(() => {
  return documentGeneration.value.status === 'PENDING';
});

const canClose = computed(() => {
  return (
    documentGeneration.value.status === 'SUCCESS' ||
    documentGeneration.value.status === 'FAILURE' ||
    props.autoClose
  );
});

const showDetails = computed(() => {
  return (
    documentGeneration.value.taskId ||
    documentGeneration.value.documentId ||
    generationStartTime.value
  );
});

const generationDuration = computed(() => {
  if (!generationStartTime.value || !generationEndTime.value) return null;

  const duration = (generationEndTime.value - generationStartTime.value) / 1000;
  return duration.toFixed(1);
});

// Methods
const downloadDocument = async () => {
  if (
    !documentGeneration.value.documentId &&
    !documentGeneration.value.downloadUrl
  )
    return;

  try {
    let downloadUrl = documentGeneration.value.downloadUrl;

    if (!downloadUrl && documentGeneration.value.documentId) {
      const response = await documentsAPI.download(
        documentGeneration.value.documentId
      );
      downloadUrl = URL.createObjectURL(response);
    }

    // Create temporary link and trigger download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `documento_${documentGeneration.value.documentId || Date.now()}.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up object URL if we created one
    if (!documentGeneration.value.downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
    }

    emit('document-downloaded', documentGeneration.value);
  } catch (error) {
    console.error('Erro no download:', error);
    // Could show a toast notification here
  }
};

const openInDrive = () => {
  if (documentGeneration.value.driveUrl) {
    window.open(documentGeneration.value.driveUrl, '_blank');
  }
};

const retryGeneration = async () => {
  if (!documentGeneration.value.documentId) return;

  try {
    isRetrying.value = true;

    await documentsAPI.retry(documentGeneration.value.documentId);

    // Reset status to pending
    store.documentGeneration.status = 'PENDING';
    store.documentGeneration.progress = 0;
    store.documentGeneration.error = null;

    startPolling();
  } catch (error) {
    console.error('Erro ao tentar novamente:', error);
  } finally {
    isRetrying.value = false;
  }
};

const cancelGeneration = () => {
  store.resetDocumentGeneration();
  stopPolling();
  emit('generation-cancelled');
};

const closeMonitor = () => {
  stopPolling();
  emit('monitor-closed');
};

const toggleDetails = () => {
  detailsExpanded.value = !detailsExpanded.value;
};

const formatTime = timestamp => {
  if (!timestamp) return '';

  const date = new Date(timestamp);
  return date.toLocaleString('pt-BR');
};

const getHistoryStatusClasses = status => {
  const baseClasses = 'w-8 h-8 rounded-full flex items-center justify-center';

  switch (status) {
    case 'SUCCESS':
      return `${baseClasses} bg-green-100 text-green-600`;
    case 'FAILURE':
      return `${baseClasses} bg-red-100 text-red-600`;
    default:
      return `${baseClasses} bg-gray-100 text-gray-600`;
  }
};

const getHistoryStatusIcon = status => {
  switch (status) {
    case 'SUCCESS':
      return CheckCircleIcon;
    case 'FAILURE':
      return XCircleIcon;
    default:
      return ClockIcon;
  }
};

const downloadHistoryDocument = async generation => {
  try {
    const response = await documentsAPI.download(generation.documentId);
    const downloadUrl = URL.createObjectURL(response);

    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `documento_${generation.documentId}.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('Erro no download do histórico:', error);
  }
};

const retryHistoryGeneration = async generation => {
  try {
    await documentsAPI.retry(generation.documentId);
    // Could update the history item status here
  } catch (error) {
    console.error('Erro ao tentar novamente:', error);
  }
};

const loadHistory = async () => {
  try {
    const response = await documentsAPI.list({ limit: 10 });
    generationHistory.value = response.documents || [];
  } catch (error) {
    console.error('Erro ao carregar histórico:', error);
  }
};

const startPolling = () => {
  if (refreshTimer.value) return;

  refreshTimer.value = setInterval(async () => {
    if (
      documentGeneration.value.status === 'PENDING' &&
      documentGeneration.value.taskId
    ) {
      try {
        const status = await documentsAPI.getStatus(
          documentGeneration.value.taskId
        );

        // Update progress
        if (status.progress !== undefined) {
          store.documentGeneration.progress = status.progress;
        }

        // Check if completed
        if (status.state === 'SUCCESS') {
          store.documentGeneration.status = 'SUCCESS';
          store.documentGeneration.progress = 100;
          store.documentGeneration.documentId = status.document_id;
          store.documentGeneration.downloadUrl = status.download_url;
          store.documentGeneration.driveUrl = status.drive_url;

          generationEndTime.value = new Date();
          stopPolling();

          // Auto-close if configured
          if (props.autoClose) {
            setTimeout(closeMonitor, 3000);
          }
        } else if (status.state === 'FAILURE') {
          store.documentGeneration.status = 'FAILURE';
          store.documentGeneration.error = status.error || 'Erro desconhecido';

          generationEndTime.value = new Date();
          stopPolling();
        }
      } catch (error) {
        console.error('Erro no polling:', error);
      }
    }
  }, props.refreshInterval);
};

const stopPolling = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
    refreshTimer.value = null;
  }
};

// Watchers
watch(
  () => documentGeneration.value.status,
  (newStatus, oldStatus) => {
    if (newStatus === 'PENDING' && oldStatus !== 'PENDING') {
      generationStartTime.value = new Date();
      generationEndTime.value = null;
      startPolling();
    }
  }
);

// Lifecycle
onMounted(() => {
  if (props.showHistory) {
    loadHistory();
  }

  if (documentGeneration.value.status === 'PENDING') {
    startPolling();
  }
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.document-generation-monitor {
  @apply space-y-6;
}

/* Progress bar animation */
.bg-blue-600 {
  transition: width 0.5s ease-out;
}

/* Rotating animation for retry button */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
