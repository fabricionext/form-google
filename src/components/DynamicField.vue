<template>
  <div class="dynamic-field">
    <!-- Field Label -->
    <label 
      v-if="field.label && field.type !== 'checkbox'"
      :for="fieldId"
      class="block text-sm font-medium text-gray-700 mb-1"
    >
      {{ field.label }}
      <span v-if="field.required" class="text-red-500 ml-1">*</span>
    </label>

    <!-- Field Description -->
    <p v-if="field.description" class="text-xs text-gray-500 mb-2">
      {{ field.description }}
    </p>

    <!-- Input Fields -->
    <div class="relative">
      <!-- Text Input -->
      <input
        v-if="['text', 'email', 'tel', 'number'].includes(field.type)"
        :id="fieldId"
        :type="field.type"
        :value="modelValue"
        :placeholder="field.placeholder"
        :required="field.required"
        :readonly="field.readonly"
        :disabled="field.disabled"
        :class="inputClasses"
        @input="updateValue($event.target.value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
      />

      <!-- CPF Input with Mask -->
      <input
        v-else-if="field.type === 'cpf'"
        :id="fieldId"
        type="text"
        :value="modelValue"
        :placeholder="field.placeholder || '000.000.000-00'"
        :required="field.required"
        :class="inputClasses"
        @input="updateCpfValue($event.target.value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
        maxlength="14"
      />

      <!-- CNPJ Input with Mask -->
      <input
        v-else-if="field.type === 'cnpj'"
        :id="fieldId"
        type="text"
        :value="modelValue"
        :placeholder="field.placeholder || '00.000.000/0000-00'"
        :required="field.required"
        :class="inputClasses"
        @input="updateCnpjValue($event.target.value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
        maxlength="18"
      />

      <!-- Phone Input with Mask -->
      <input
        v-else-if="field.type === 'phone'"
        :id="fieldId"
        type="tel"
        :value="modelValue"
        :placeholder="field.placeholder || '(00) 00000-0000'"
        :required="field.required"
        :class="inputClasses"
        @input="updatePhoneValue($event.target.value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
        maxlength="15"
      />

      <!-- CEP Input with Mask -->
      <input
        v-else-if="field.type === 'cep'"
        :id="fieldId"
        type="text"
        :value="modelValue"
        :placeholder="field.placeholder || '00000-000'"
        :required="field.required"
        :class="inputClasses"
        @input="updateCepValue($event.target.value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
        maxlength="9"
      />

      <!-- Date Input -->
      <input
        v-else-if="field.type === 'date'"
        :id="fieldId"
        type="date"
        :value="modelValue"
        :required="field.required"
        :class="inputClasses"
        @input="updateValue($event.target.value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
      />

      <!-- Textarea -->
      <textarea
        v-else-if="['textarea', 'longtext'].includes(field.type)"
        :id="fieldId"
        :value="modelValue"
        :placeholder="field.placeholder"
        :required="field.required"
        :rows="field.rows || 3"
        :class="textareaClasses"
        @input="updateValue($event.target.value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
      ></textarea>

      <!-- Select Dropdown -->
      <select
        v-else-if="field.type === 'select'"
        :id="fieldId"
        :value="modelValue"
        :required="field.required"
        :class="selectClasses"
        @change="updateValue($event.target.value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
      >
        <option value="">{{ field.placeholder || 'Selecione...' }}</option>
        <option
          v-for="option in field.options"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>

      <!-- Radio Group -->
      <div v-else-if="field.type === 'radio'" class="space-y-2">
        <div
          v-for="option in field.options"
          :key="option.value"
          class="flex items-center"
        >
          <input
            :id="`${fieldId}_${option.value}`"
            :name="fieldId"
            type="radio"
            :value="option.value"
            :checked="modelValue === option.value"
            :required="field.required"
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
            @change="updateValue(option.value)"
          />
          <label
            :for="`${fieldId}_${option.value}`"
            class="ml-3 block text-sm font-medium text-gray-700"
          >
            {{ option.label }}
          </label>
        </div>
      </div>

      <!-- Checkbox -->
      <div v-else-if="field.type === 'checkbox'" class="flex items-center">
        <input
          :id="fieldId"
          type="checkbox"
          :checked="Boolean(modelValue)"
          :required="field.required"
          class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          @change="updateValue($event.target.checked)"
        />
        <label
          :for="fieldId"
          class="ml-3 block text-sm font-medium text-gray-700"
        >
          {{ field.label }}
          <span v-if="field.required" class="text-red-500 ml-1">*</span>
        </label>
      </div>

      <!-- Client Search -->
      <div v-else-if="field.type === 'client_search'" class="relative">
        <input
          :id="fieldId"
          type="text"
          :value="searchQuery"
          :placeholder="field.placeholder || 'Digite o nome ou CPF do cliente'"
          :class="inputClasses"
          @input="handleClientSearch($event.target.value)"
          @blur="hideClientSuggestions"
          @focus="$emit('focus')"
        />
        
        <!-- Client Suggestions -->
        <div
          v-if="showClientSuggestions && clientSuggestions.length > 0"
          class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
        >
          <div
            v-for="client in clientSuggestions"
            :key="client.id"
            class="px-4 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
            @mousedown="selectClient(client)"
          >
            <div class="font-medium text-gray-900">{{ client.nome_completo }}</div>
            <div class="text-sm text-gray-500">{{ formatCpf(client.cpf) }}</div>
          </div>
        </div>
      </div>

      <!-- Authority Search -->
      <div v-else-if="field.type === 'authority_search'" class="relative">
        <input
          :id="fieldId"
          type="text"
          :value="searchQuery"
          :placeholder="field.placeholder || 'Digite o nome da autoridade'"
          :class="inputClasses"
          @input="handleAuthoritySearch($event.target.value)"
          @blur="hideAuthoritySuggestions"
          @focus="$emit('focus')"
        />
        
        <!-- Authority Suggestions -->
        <div
          v-if="showAuthoritySuggestions && authoritySuggestions.length > 0"
          class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
        >
          <div
            v-for="authority in authoritySuggestions"
            :key="authority.id"
            class="px-4 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
            @mousedown="selectAuthority(authority)"
          >
            <div class="font-medium text-gray-900">{{ authority.nome }}</div>
            <div class="text-sm text-gray-500">{{ authority.cidade }}, {{ authority.estado }}</div>
          </div>
        </div>
      </div>

      <!-- File Upload -->
      <input
        v-else-if="field.type === 'file'"
        :id="fieldId"
        type="file"
        :accept="field.accept"
        :required="field.required"
        :class="inputClasses"
        @change="handleFileUpload($event)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
      />

      <!-- Section Header (not an input) -->
      <div
        v-else-if="field.type === 'section_header'"
        class="border-b border-gray-200 pb-2 mb-4"
      >
        <h3 class="text-lg font-semibold text-gray-900">{{ field.label }}</h3>
        <p v-if="field.description" class="text-sm text-gray-600 mt-1">
          {{ field.description }}
        </p>
      </div>

      <!-- Fallback for unknown field types -->
      <input
        v-else
        :id="fieldId"
        type="text"
        :value="modelValue"
        :placeholder="field.placeholder"
        :required="field.required"
        :class="inputClasses"
        @input="updateValue($event.target.value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
      />
    </div>

    <!-- Error Messages -->
    <div v-if="errors && errors.length > 0" class="mt-1">
      <p
        v-for="error in errors"
        :key="error"
        class="text-sm text-red-600"
      >
        {{ error }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useFormularioStore } from '../stores/formulario.js'

// Props
const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  value: {
    type: [String, Number, Boolean, File],
    default: ''
  },
  errors: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['update:value', 'blur', 'focus'])

// Store
const store = useFormularioStore()

// Local state
const searchQuery = ref('')
const clientSuggestions = ref([])
const authoritySuggestions = ref([])
const showClientSuggestions = ref(false)
const showAuthoritySuggestions = ref(false)

// Computed
const modelValue = computed(() => props.value)

const fieldId = computed(() => `field_${props.field.name}`)

const hasErrors = computed(() => props.errors && props.errors.length > 0)

const baseInputClasses = 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'

const inputClasses = computed(() => {
  return [
    baseInputClasses,
    hasErrors.value 
      ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500'
      : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
    props.field.disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'
  ].join(' ')
})

const textareaClasses = computed(() => {
  return [
    'block w-full rounded-md shadow-sm sm:text-sm resize-vertical',
    hasErrors.value 
      ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500'
      : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
  ].join(' ')
})

const selectClasses = computed(() => {
  return [
    'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
    hasErrors.value 
      ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500'
      : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
  ].join(' ')
})

// Methods
const updateValue = (newValue) => {
  emit('update:value', newValue)
}

const updateCpfValue = (value) => {
  const formatted = formatCpfInput(value)
  emit('update:value', formatted)
}

const updateCnpjValue = (value) => {
  const formatted = formatCnpjInput(value)
  emit('update:value', formatted)
}

const updatePhoneValue = (value) => {
  const formatted = formatPhoneInput(value)
  emit('update:value', formatted)
}

const updateCepValue = (value) => {
  const formatted = formatCepInput(value)
  emit('update:value', formatted)
}

const handleClientSearch = async (query) => {
  searchQuery.value = query
  
  if (query.length >= 3) {
    try {
      clientSuggestions.value = await store.searchClients(query)
      showClientSuggestions.value = true
    } catch (error) {
      console.error('Erro na busca de clientes:', error)
      clientSuggestions.value = []
    }
  } else {
    clientSuggestions.value = []
    showClientSuggestions.value = false
  }
}

const handleAuthoritySearch = async (query) => {
  searchQuery.value = query
  
  if (query.length >= 3) {
    try {
      authoritySuggestions.value = await store.searchAuthorities(query)
      showAuthoritySuggestions.value = true
    } catch (error) {
      console.error('Erro na busca de autoridades:', error)
      authoritySuggestions.value = []
    }
  } else {
    authoritySuggestions.value = []
    showAuthoritySuggestions.value = false
  }
}

const selectClient = (client) => {
  searchQuery.value = client.nome_completo
  showClientSuggestions.value = false
  emit('update:value', client.id)
  
  // Auto-fill related fields if this is part of an author section
  const authorMatch = props.field.name.match(/autor_(\d+)_/)
  if (authorMatch) {
    const authorIndex = parseInt(authorMatch[1])
    store.preencherCampoCliente(client, authorIndex)
  } else {
    store.preencherCampoCliente(client)
  }
}

const selectAuthority = (authority) => {
  searchQuery.value = authority.nome
  showAuthoritySuggestions.value = false
  emit('update:value', authority.id)
  
  // Auto-fill authority fields
  const authorityMatch = props.field.name.match(/orgao_transito_(\d+)_/)
  if (authorityMatch) {
    const authorityIndex = parseInt(authorityMatch[1])
    store.preencherCampoAutoridade(authority, authorityIndex)
  }
}

const hideClientSuggestions = () => {
  setTimeout(() => {
    showClientSuggestions.value = false
  }, 200)
}

const hideAuthoritySuggestions = () => {
  setTimeout(() => {
    showAuthoritySuggestions.value = false
  }, 200)
}

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  emit('update:value', file)
}

// Formatting utilities
const formatCpfInput = (value) => {
  const numbers = value.replace(/\D/g, '')
  if (numbers.length <= 11) {
    return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
      .replace(/(\d{3})(\d{3})(\d{3})(\d{1})$/, '$1.$2.$3-$4')
      .replace(/(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3')
      .replace(/(\d{3})(\d{2})$/, '$1.$2')
      .replace(/(\d{3})$/, '$1')
  }
  return value
}

const formatCnpjInput = (value) => {
  const numbers = value.replace(/\D/g, '')
  if (numbers.length <= 14) {
    return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
      .replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{1})$/, '$1.$2.$3/$4-$5')
      .replace(/(\d{2})(\d{3})(\d{3})(\d{3})$/, '$1.$2.$3/$4')
      .replace(/(\d{2})(\d{3})(\d{2})$/, '$1.$2.$3')
      .replace(/(\d{2})(\d{2})$/, '$1.$2')
  }
  return value
}

const formatPhoneInput = (value) => {
  const numbers = value.replace(/\D/g, '')
  if (numbers.length <= 11) {
    return numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3')
      .replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3')
      .replace(/(\d{2})(\d{4})(\d{3})$/, '($1) $2-$3')
      .replace(/(\d{2})(\d{4})(\d{2})$/, '($1) $2-$3')
      .replace(/(\d{2})(\d{4})(\d{1})$/, '($1) $2-$3')
      .replace(/(\d{2})(\d{3})$/, '($1) $2')
      .replace(/(\d{2})(\d{2})$/, '($1) $2')
  }
  return value
}

const formatCepInput = (value) => {
  const numbers = value.replace(/\D/g, '')
  if (numbers.length <= 8) {
    return numbers.replace(/(\d{5})(\d{3})/, '$1-$2')
      .replace(/(\d{5})(\d{2})$/, '$1-$2')
      .replace(/(\d{5})(\d{1})$/, '$1-$2')
  }
  return value
}

const formatCpf = (cpf) => {
  if (!cpf) return ''
  return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
}

// Initialize search query with current value for search fields
watch(() => props.value, (newValue) => {
  if (['client_search', 'authority_search'].includes(props.field.type)) {
    if (typeof newValue === 'string') {
      searchQuery.value = newValue
    }
  }
}, { immediate: true })
</script>

<style scoped>
/* Custom styles for specific field types */
.dynamic-field {
  @apply relative;
}

/* Ensure suggestions dropdown appears above other elements */
.dynamic-field .absolute {
  z-index: 50;
}

/* File input styling */
input[type="file"] {
  @apply file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100;
}
</style>