<template>
  <div class="dynamic-schema-renderer">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center p-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <span class="ml-3 text-gray-600">Carregando schema...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
      <div class="flex">
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Erro ao carregar schema</h3>
          <div class="mt-2 text-sm text-red-700">{{ error }}</div>
        </div>
      </div>
    </div>

    <!-- Schema Rendered Form -->
    <div v-else-if="schema" class="space-y-6">
      <!-- Form Header -->
      <div v-if="schema.title || schema.description" class="border-b pb-4">
        <h2 v-if="schema.title" class="text-2xl font-bold text-gray-900">{{ schema.title }}</h2>
        <p v-if="schema.description" class="mt-2 text-gray-600">{{ schema.description }}</p>
      </div>

      <!-- Dynamic Sections -->
      <div v-for="section in organizedSections" :key="section.name" class="space-y-4">
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <component :is="section.icon" v-if="section.icon" class="w-5 h-5 mr-2 text-blue-600" />
            {{ section.title }}
          </h3>
          
          <!-- Fields Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="field in section.fields"
              :key="field.name"
              :class="getFieldClasses(field)"
            >
              <DynamicField
                :field="field"
                :value="formData[field.name]"
                :errors="validationErrors[field.name]"
                @update:value="updateField(field.name, $event)"
                @blur="validateField(field.name)"
                @focus="clearFieldError(field.name)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Conditional Fields -->
      <div v-if="conditionalFields.length > 0" class="bg-blue-50 rounded-lg p-6">
        <h3 class="text-lg font-semibold text-blue-900 mb-4">Campos Condicionais</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="field in conditionalFields" :key="field.name">
            <DynamicField
              :field="field"
              :value="formData[field.name]"
              :errors="validationErrors[field.name]"
              @update:value="updateField(field.name, $event)"
              @blur="validateField(field.name)"
            />
          </div>
        </div>
      </div>

      <!-- Multi-Author Sections -->
      <div v-if="multiAuthorFields.length > 0" class="space-y-4">
        <div
          v-for="(authorGroup, index) in authorGroups"
          :key="`author_${index + 1}`"
          class="bg-green-50 rounded-lg border border-green-200 p-6"
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-green-900">
              Autor {{ index + 1 }}
            </h3>
            <button
              v-if="index > 0"
              @click="removeAuthor(index)"
              class="text-red-600 hover:text-red-800"
              type="button"
            >
              Remover
            </button>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="field in authorGroup" :key="field.name">
              <DynamicField
                :field="field"
                :value="formData[field.name]"
                :errors="validationErrors[field.name]"
                @update:value="updateField(field.name, $event)"
                @blur="validateField(field.name)"
              />
            </div>
          </div>
        </div>
        
        <button
          v-if="authorGroups.length < maxAuthors"
          @click="addAuthor"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
          type="button"
        >
          + Adicionar Autor
        </button>
      </div>

      <!-- Form Actions -->
      <div class="flex items-center justify-between pt-6 border-t">
        <div class="flex items-center space-x-2">
          <button
            @click="validateAllFields"
            :disabled="loading || submitting"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            type="button"
          >
            Validar Formulário
          </button>
          
          <button
            @click="saveAsDraft"
            :disabled="loading"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            type="button"
          >
            Salvar Rascunho
          </button>
        </div>
        
        <button
          @click="generateDocument"
          :disabled="!isFormValid || submitting"
          class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          type="button"
        >
          <span v-if="submitting" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white">
            <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </span>
          {{ submitting ? 'Gerando...' : 'Gerar Documento' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useFormularioStore } from '../stores/formulario.js'
import DynamicField from './DynamicField.vue'

// Props
const props = defineProps({
  templateId: {
    type: [Number, String],
    required: true
  },
  initialData: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['document-generated', 'validation-error', 'form-updated'])

// Store
const store = useFormularioStore()

// Local reactive state
const loading = ref(false)
const error = ref(null)
const maxAuthors = ref(3)

// Computed properties
const schema = computed(() => store.formSchema)
const formData = computed(() => store.formData)
const validationErrors = computed(() => store.validationErrors)
const submitting = computed(() => store.submitting)

const organizedSections = computed(() => {
  if (!schema.value?.fields) return []
  
  const sections = {
    cliente: { name: 'cliente', title: 'Dados do Cliente', icon: 'UserIcon', fields: [] },
    endereco: { name: 'endereco', title: 'Endereço', icon: 'MapPinIcon', fields: [] },
    processo: { name: 'processo', title: 'Dados do Processo', icon: 'DocumentTextIcon', fields: [] },
    autoridades: { name: 'autoridades', title: 'Autoridades', icon: 'BuildingOfficeIcon', fields: [] },
    outros: { name: 'outros', title: 'Outros Campos', icon: null, fields: [] }
  }
  
  schema.value.fields.forEach(field => {
    if (field.name.startsWith('autor_')) return // Handled separately
    if (field.conditional) return // Handled separately
    
    const category = field.category || categorizarCampo(field.name)
    const section = sections[category] || sections.outros
    section.fields.push(field)
  })
  
  return Object.values(sections).filter(section => section.fields.length > 0)
})

const conditionalFields = computed(() => {
  if (!schema.value?.fields) return []
  
  return schema.value.fields.filter(field => {
    if (!field.conditional) return false
    
    // Check if condition is met
    const condition = field.conditional
    if (condition.field && condition.value) {
      return formData.value[condition.field] === condition.value
    }
    
    return false
  })
})

const multiAuthorFields = computed(() => {
  if (!schema.value?.fields) return []
  
  return schema.value.fields.filter(field => field.name.startsWith('autor_'))
})

const authorGroups = computed(() => {
  const groups = {}
  
  multiAuthorFields.value.forEach(field => {
    const match = field.name.match(/autor_(\d+)_(.+)/)
    if (match) {
      const authorNum = parseInt(match[1])
      if (!groups[authorNum]) {
        groups[authorNum] = []
      }
      groups[authorNum].push(field)
    }
  })
  
  return Object.values(groups).sort((a, b) => {
    const aNum = parseInt(a[0]?.name.match(/autor_(\d+)_/)?.[1] || 0)
    const bNum = parseInt(b[0]?.name.match(/autor_(\d+)_/)?.[1] || 0)
    return aNum - bNum
  })
})

const isFormValid = computed(() => {
  return Object.keys(validationErrors.value).length === 0
})

// Methods
const loadSchema = async () => {
  try {
    loading.value = true
    error.value = null
    
    await store.loadTemplate(props.templateId)
    
    // Initialize form data with defaults
    if (props.initialData && Object.keys(props.initialData).length > 0) {
      Object.assign(store.formData, props.initialData)
    }
    
  } catch (err) {
    error.value = err.message || 'Erro ao carregar schema do formulário'
    console.error('Erro ao carregar schema:', err)
  } finally {
    loading.value = false
  }
}

const getFieldClasses = (field) => {
  const baseClasses = ''
  
  if (field.type === 'textarea' || field.type === 'longtext') {
    return `${baseClasses} md:col-span-2 lg:col-span-3`
  }
  
  if (field.type === 'section_header') {
    return `${baseClasses} md:col-span-2 lg:col-span-3`
  }
  
  return baseClasses
}

const updateField = (fieldName, value) => {
  store.atualizarCampo(fieldName, value)
  emit('form-updated', { field: fieldName, value })
  
  // Clear validation error when field is updated
  if (validationErrors.value[fieldName]) {
    clearFieldError(fieldName)
  }
}

const validateField = async (fieldName) => {
  // Individual field validation will be handled by the store
  // This is called on field blur
}

const validateAllFields = async () => {
  try {
    const isValid = await store.validateForm()
    if (!isValid) {
      emit('validation-error', validationErrors.value)
    }
    return isValid
  } catch (err) {
    error.value = 'Erro na validação do formulário'
    return false
  }
}

const clearFieldError = (fieldName) => {
  if (validationErrors.value[fieldName]) {
    const errors = { ...validationErrors.value }
    delete errors[fieldName]
    store.validationErrors = errors
  }
}

const generateDocument = async () => {
  try {
    const isValid = await validateAllFields()
    if (!isValid) return
    
    const result = await store.generateDocument()
    emit('document-generated', result)
  } catch (err) {
    error.value = err.message || 'Erro na geração do documento'
    emit('validation-error', { general: [error.value] })
  }
}

const saveAsDraft = () => {
  store.salvarRascunho()
}

const addAuthor = () => {
  // Logic to add a new author section
  const currentAuthors = authorGroups.value.length
  if (currentAuthors < maxAuthors.value) {
    // Add empty fields for the new author
    const newAuthorNum = currentAuthors + 1
    const authorTemplate = multiAuthorFields.value.filter(f => f.name.startsWith('autor_1_'))
    
    authorTemplate.forEach(templateField => {
      const newFieldName = templateField.name.replace('autor_1_', `autor_${newAuthorNum}_`)
      store.atualizarCampo(newFieldName, '')
    })
  }
}

const removeAuthor = (authorIndex) => {
  const authorNum = authorIndex + 1
  const fieldsToRemove = Object.keys(formData.value).filter(key => 
    key.startsWith(`autor_${authorNum}_`)
  )
  
  fieldsToRemove.forEach(field => {
    delete store.formData[field]
  })
  
  store.dataChanged = true
}

// Helper function for field categorization (imported from store)
const categorizarCampo = (chave) => {
  const chaveLower = chave.toLowerCase()
  
  if (chaveLower.includes('orgao_transito') || chaveLower.includes('autoridade')) {
    return 'autoridades'
  }
  
  if (chaveLower.includes('endereco') || chaveLower.includes('logradouro') || 
      chaveLower.includes('numero') || chaveLower.includes('bairro') ||
      chaveLower.includes('cidade') || chaveLower.includes('cep')) {
    return 'endereco'
  }
  
  if (chaveLower.includes('processo') || chaveLower.includes('infracao') || 
      chaveLower.includes('multa') || chaveLower.includes('artigo')) {
    return 'processo'
  }
  
  if (chaveLower.includes('nome') || chaveLower.includes('cpf') || 
      chaveLower.includes('rg') || chaveLower.includes('profissao')) {
    return 'cliente'
  }
  
  return 'outros'
}

// Watchers
watch(() => props.templateId, (newId) => {
  if (newId) {
    loadSchema()
  }
}, { immediate: true })

// Lifecycle
onMounted(() => {
  if (props.templateId) {
    loadSchema()
  }
})
</script>

<style scoped>
.dynamic-schema-renderer {
  max-width: none;
}

/* Custom styles for field groups */
.field-group {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  background-color: #f9fafb;
}

.field-group h4 {
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.75rem;
}

/* Responsive grid adjustments */
@media (max-width: 768px) {
  .grid-cols-1.md\:grid-cols-2.lg\:grid-cols-3 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
}
</style>