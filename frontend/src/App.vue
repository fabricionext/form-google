<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useTheme } from 'vuetify';
import { useAuthStore } from '@/stores/auth';
import { api } from '@/plugins/axiosInterceptor';
import { useRoute } from 'vue-router';
import emitter from '@/plugins/eventBus';

const theme = useTheme();
const authStore = useAuthStore();
const route = useRoute();

// Estado do UI
const drawer = ref(true);
const loading = ref(false);

// Estado do Snackbar de Erro
const snackbar = ref(false);
const snackbarMessage = ref('');

const menuItems = [
  {
    title: 'Gerenciador de Templates',
    icon: 'mdi-google-drive',
    route: '/templates',
  },
  { title: 'Dashboard', icon: 'mdi-view-dashboard', route: '/modelos' },
  {
    title: 'Modelos de Petição',
    icon: 'mdi-file-document-multiple',
    route: '/modelos',
  },
  {
    title: 'Criar Modelo',
    icon: 'mdi-plus-circle-outline',
    route: '/modelos/novo',
  },
  {
    title: 'Formulários Ativos',
    icon: 'mdi-form-select',
    route: '/formularios',
  },
  { title: 'Relatórios', icon: 'mdi-chart-line', route: '/relatorios' },
];

// Lógica de Autenticação e Tema
const isDark = computed(() => theme.global.name.value === 'modernDark');

function toggleTheme() {
  theme.global.name.value = isDark.value ? 'modernLight' : 'modernDark';
  localStorage.setItem('theme', theme.global.name.value);
}

async function checkAuthStatus() {
  loading.value = true;
  try {
    const { data } = await api.get('/auth/status');
    if (data.logged_in) {
      authStore.user = data.user;
      authStore.access = 'cookie_session_active';
    } else {
      authStore.logout();
    }
  } catch (error) {
    console.error('Erro ao verificar status de autenticação:', error);
    authStore.logout();
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) theme.global.name.value = savedTheme;
  checkAuthStatus();

  // Listener para erros da API
  emitter.on('api-error', message => {
    snackbarMessage.value = message;
    snackbar.value = true;
  });
});

onUnmounted(() => {
  emitter.off('api-error');
});

// Título da página dinâmico
const currentPageTitle = computed(() => {
  // Lógica para determinar o título da página com base na rota
  return route.meta.title || 'Sistema Peticionador';
});
</script>

<template>
  <v-app>
    <!-- O Navigation Drawer e a App Bar só são renderizados se o usuário estiver autenticado -->
    <template v-if="authStore.user">
      <v-navigation-drawer
        v-model="drawer"
        app
        permanent
        width="300"
        color="surface"
        border="0"
        elevation="1"
      >
        <div class="pa-6 d-flex align-center">
          <v-avatar color="primary" size="48" class="me-3"
            ><v-icon color="white" size="24">mdi-gavel</v-icon></v-avatar
          >
          <div>
            <h3 class="text-h6 font-weight-bold text-primary">Peticionador</h3>
            <p class="text-caption text-medium-emphasis mb-0">
              Sistema Legal Inteligente
            </p>
          </div>
        </div>
        <v-divider class="mx-4 mb-2"></v-divider>
        <v-list nav density="comfortable" class="px-2">
          <v-list-item
            v-for="item in menuItems"
            :key="item.title"
            :to="item.route"
            rounded="lg"
            class="mb-1"
            color="primary"
          >
            <template v-slot:prepend
              ><v-icon :icon="item.icon" size="20"></v-icon
            ></template>
            <v-list-item-title class="font-weight-medium">{{
              item.title
            }}</v-list-item-title>
          </v-list-item>
        </v-list>
        <template v-slot:append>
          <div class="pa-4">
            <v-list-item rounded="lg" @click="toggleTheme">
              <template v-slot:prepend
                ><v-icon
                  :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
                  size="20"
                ></v-icon
              ></template>
              <v-list-item-title class="font-weight-medium">{{
                isDark ? 'Modo Claro' : 'Modo Escuro'
              }}</v-list-item-title>
            </v-list-item>
          </div>
        </template>
      </v-navigation-drawer>
      <v-app-bar app color="surface" elevation="1" height="72" border="0">
        <v-app-bar-nav-icon
          @click="drawer = !drawer"
          variant="text"
          color="on-surface"
        ></v-app-bar-nav-icon>
        <v-toolbar-title class="font-weight-bold text-h6">{{
          currentPageTitle
        }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn v-bind="props" icon variant="text" color="on-surface">
              <v-avatar size="36" color="primary"
                ><v-icon color="white">mdi-account</v-icon></v-avatar
              >
            </v-btn>
          </template>
          <v-list>
            <v-list-item>
              <v-list-item-title>{{ authStore.user.name }}</v-list-item-title>
              <v-list-item-subtitle>{{
                authStore.user.email
              }}</v-list-item-subtitle>
            </v-list-item>
            <v-divider></v-divider>
            <v-list-item href="/peticionador/logout">
              <template v-slot:prepend><v-icon>mdi-logout</v-icon></template>
              <v-list-item-title>Sair</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-app-bar>
    </template>
    <v-main>
      <v-container fluid class="pa-8">
        <router-view />
      </v-container>
    </v-main>
    <v-overlay v-model="loading" class="align-center justify-center" persistent>
      <v-progress-circular
        indeterminate
        color="primary"
        size="64"
      ></v-progress-circular>
    </v-overlay>

    <!-- Snackbar Global para Erros -->
    <v-snackbar
      v-model="snackbar"
      :timeout="6000"
      color="error"
      location="top right"
      multi-line
    >
      {{ snackbarMessage }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar = false"> Fechar </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>
<style>
.v-main {
  background-color: rgb(var(--v-theme-background));
}
</style>
