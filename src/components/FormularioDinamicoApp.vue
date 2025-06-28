<template>
  <div class="formulario-dinamico-app">
    <!-- Barra de progresso e status -->
    <div v-if="dataChanged" class="alert alert-info mb-3">
      <i class="fas fa-edit"></i>
      Dados alterados - não esqueça de salvar!
      <button
        @click="salvarRascunho"
        class="btn btn-sm btn-outline-primary ms-2"
      >
        <i class="fas fa-save"></i> Salvar Rascunho
      </button>
    </div>

    <div class="row">
      <!-- Sidebar com buscas -->
      <div class="col-md-3">
        <!-- Busca de Clientes -->
        <ClienteSearch
          @cliente-selecionado="handleClienteDrop"
          @cliente-drop-autor="handleClienteDropAutor"
        />

        <!-- Busca de Autoridades -->
        <AutoridadeSearch @autoridade-selecionada="handleAutoridadeDrop" />
      </div>

      <!-- Formulário Principal -->
      <div class="col-md-9">
        <form id="peticao_form" @submit="handleSubmit" novalidate>
          <!-- Token CSRF -->
          <input type="hidden" name="csrf_token" :value="csrfToken" />

          <!-- Seções do Formulário -->
          <FormularioSecao
            v-for="(campos, secao) in camposOrganizados"
            :key="secao"
            :secao="secao"
            :campos="campos"
            :form-data="formData"
            @campo-atualizado="atualizarCampo"
          />

          <!-- Botões de Ação -->
          <div class="form-actions mt-4">
            <button
              type="submit"
              class="btn btn-primary btn-lg"
              :disabled="submitting"
            >
              <i class="fas fa-file-alt"></i>
              {{ submitting ? 'Gerando...' : 'Gerar Documento' }}
            </button>

            <button
              type="button"
              class="btn btn-secondary ms-2"
              @click="limparFormulario"
            >
              <i class="fas fa-eraser"></i>
              Limpar
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useFormularioStore } from '../stores/formulario.js';
import ClienteSearch from './ClienteSearch.vue';
import AutoridadeSearch from './AutoridadeSearch.vue';
import FormularioSecao from './FormularioSecao.vue';

const formularioStore = useFormularioStore();

// Estado local
const csrfToken = ref('');

// Computed do store
const { formData, dataChanged, submitting, camposOrganizados } =
  formularioStore;

// Inicialização
onMounted(async () => {
  // Obter token CSRF do meta tag
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  if (csrfMeta) {
    csrfToken.value = csrfMeta.content;
  }

  // Carregar dados iniciais
  await carregarDadosIniciais();

  // Inicializar buscas fuzzy
  formularioStore.inicializarBuscas();

  // Carregar rascunho se existir
  const rascunhoCarregado = formularioStore.carregarRascunho();
  if (rascunhoCarregado) {
    console.log('✅ Rascunho carregado automaticamente');
  }

  // Auto-save a cada 30 segundos
  setInterval(() => {
    if (dataChanged.value) {
      formularioStore.salvarRascunho();
    }
  }, 30000);
});

// Carregar dados do backend
const carregarDadosIniciais = async () => {
  try {
    // Carregar clientes
    const clientesResponse = await fetch('/peticionador/api/clientes');
    if (clientesResponse.ok) {
      formularioStore.clientes = await clientesResponse.json();
    }

    // Carregar autoridades
    const autoridadesResponse = await fetch('/peticionador/api/autoridades');
    if (autoridadesResponse.ok) {
      formularioStore.autoridades = await autoridadesResponse.json();
    }

    // Carregar campos do formulário atual
    const formElement = document.getElementById('peticao_form');
    if (formElement) {
      const campos = Array.from(formElement.querySelectorAll('[name]'))
        .filter(field => field.name && field.name !== 'csrf_token')
        .map(field => ({
          chave: field.name,
          tipo: field.type || 'text',
          label: field.getAttribute('data-label') || field.name,
          obrigatorio: field.required || false,
          elemento: field,
        }));

      formularioStore.campos = campos;
    }
  } catch (error) {
    console.error('Erro ao carregar dados iniciais:', error);
  }
};

// Event handlers
const handleClienteDrop = clienteData => {
  formularioStore.preencherCampoCliente(clienteData);
  mostrarToast(`Cliente ${clienteData.nome_completo} carregado!`, 'success');
};

const handleClienteDropAutor = ({ clienteData, autorIndex }) => {
  formularioStore.preencherCampoCliente(clienteData, autorIndex);
  mostrarToast(
    `Autor ${autorIndex} preenchido com ${clienteData.nome_completo}!`,
    'success'
  );
};

const handleAutoridadeDrop = ({ autoridadeData, index }) => {
  formularioStore.preencherCampoAutoridade(autoridadeData, index);
  mostrarToast(`Autoridade ${autoridadeData.nome} carregada!`, 'success');
};

const atualizarCampo = ({ chave, valor }) => {
  formularioStore.atualizarCampo(chave, valor);
};

const salvarRascunho = () => {
  formularioStore.salvarRascunho();
  mostrarToast('Rascunho salvo!', 'success');
};

const handleSubmit = async event => {
  event.preventDefault();

  if (submitting.value) return;

  formularioStore.submitting = true;

  try {
    // Submeter formulário usando FormData
    const formElement = event.target;
    const formData = new FormData(formElement);

    // Adicionar dados do store ao FormData
    Object.keys(formularioStore.formData).forEach(key => {
      if (
        formularioStore.formData[key] !== undefined &&
        formularioStore.formData[key] !== null
      ) {
        formData.set(key, formularioStore.formData[key]);
      }
    });

    const response = await fetch(
      formElement.action || window.location.pathname,
      {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
      }
    );

    if (response.ok) {
      const result = await response.json();
      if (result.success) {
        mostrarToast('Documento gerado com sucesso!', 'success');

        // Limpar rascunho após sucesso
        localStorage.removeItem(`draft_${window.location.pathname}`);

        // Redirecionar se necessário
        if (result.redirect) {
          window.location.href = result.redirect;
        }
      } else {
        mostrarToast(result.message || 'Erro ao gerar documento', 'error');
      }
    } else {
      mostrarToast('Erro na comunicação com o servidor', 'error');
    }
  } catch (error) {
    console.error('Erro ao submeter formulário:', error);
    mostrarToast('Erro inesperado ao gerar documento', 'error');
  } finally {
    formularioStore.submitting = false;
  }
};

const limparFormulario = () => {
  if (confirm('Tem certeza que deseja limpar todos os dados?')) {
    formularioStore.formData = {};
    formularioStore.dataChanged = false;

    // Limpar campos do DOM
    const form = document.getElementById('peticao_form');
    if (form) {
      form.reset();
    }

    // Remover rascunho
    localStorage.removeItem(`draft_${window.location.pathname}`);

    mostrarToast('Formulário limpo!', 'info');
  }
};

// Utilitário para mostrar toasts
const mostrarToast = (mensagem, tipo = 'info') => {
  // Usar Bootstrap toast se disponível, senão alert
  if (window.bootstrap && window.bootstrap.Toast) {
    // Implementar toast Bootstrap aqui
    console.log(`${tipo.toUpperCase()}: ${mensagem}`);
  } else {
    alert(mensagem);
  }
};
</script>

<style scoped>
.formulario-dinamico-app {
  padding: 1rem 0;
}

.form-actions {
  border-top: 1px solid #dee2e6;
  padding-top: 1rem;
}

.alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

@media (max-width: 768px) {
  .col-md-3,
  .col-md-9 {
    margin-bottom: 1rem;
  }
}
</style>
