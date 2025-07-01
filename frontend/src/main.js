import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import '@mdi/font/css/materialdesignicons.css';
import 'vuetify/styles';

import App from './App.vue';

// Importar views
import ModelosView from './views/ModelosView.vue';
import ModeloFormView from './views/ModeloFormView.vue';
import PlaceholdersView from './views/PlaceholdersView.vue';
import GerarDocumentoView from './views/GerarDocumentoView.vue';
import CadastroClienteView from './views/CadastroClienteView.vue';
import TemplateManager from './views/TemplateManager.vue';

// Configuração do Router
const routes = [
  { path: '/', redirect: '/templates' },
  {
    path: '/templates',
    name: 'TemplateManager',
    component: TemplateManager,
    meta: { requiresAuth: true },
  },
  {
    path: '/modelos',
    name: 'Modelos',
    component: ModelosView,
    meta: { requiresAuth: true },
  },
  {
    path: '/modelos/novo',
    name: 'ModeloForm',
    component: ModeloFormView,
    meta: { requiresAuth: true },
  },
  {
    path: '/modelos/:id/editar',
    name: 'EditarModelo',
    component: ModeloFormView,
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/modelos/:id/placeholders',
    name: 'Placeholders',
    component: PlaceholdersView,
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/formularios/:slug/gerar',
    name: 'GerarDocumento',
    component: GerarDocumentoView,
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/templates/:id',
    name: 'TemplateDetails',
    component: ModeloFormView,
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/cadastrodecliente',
    name: 'CadastroCliente',
    component: CadastroClienteView,
    meta: { requiresAuth: false },
  },
  {
    path: '/clientes/novo',
    name: 'NovoCliente',
    component: CadastroClienteView,
    meta: { requiresAuth: false },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// =============================
// Navigation Guard (Auth)
// =============================
import { useAuthStore } from './stores/auth';

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore();

  if (to.meta.requiresAuth && !auth.access) {
    // Redireciona para a tela de login server-side
    window.location.href = '/peticionador/login';
    return; // Interrompe navegação SPA
  }

  next();
});

// Configuração do Vuetify com tema moderno e profissional
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'modernLight',
    themes: {
      modernLight: {
        dark: false,
        colors: {
          primary: '#1976D2', // Material Blue
          secondary: '#424242', // Material Grey
          accent: '#FF4081', // Material Pink
          error: '#F44336', // Material Red
          warning: '#FF9800', // Material Orange
          info: '#2196F3', // Material Light Blue
          success: '#4CAF50', // Material Green
          background: '#FAFAFA', // Light Grey Background
          surface: '#FFFFFF', // White Surface
          'surface-variant': '#F5F5F5',
          'on-surface': '#1D1D1D',
          'on-primary': '#FFFFFF',
          'on-secondary': '#FFFFFF',
          'primary-darken-1': '#1565C0',
          'secondary-darken-1': '#2E2E2E',
        },
      },
      modernDark: {
        dark: true,
        colors: {
          primary: '#2196F3', // Lighter blue for dark theme
          secondary: '#90A4AE', // Light Grey
          accent: '#FF4081', // Material Pink
          error: '#EF5350', // Lighter Red
          warning: '#FFA726', // Lighter Orange
          info: '#42A5F5', // Lighter Blue
          success: '#66BB6A', // Lighter Green
          background: '#121212', // Dark Background
          surface: '#1E1E1E', // Dark Surface
          'surface-variant': '#2C2C2C',
          'on-surface': '#FFFFFF',
          'on-primary': '#FFFFFF',
          'on-secondary': '#000000',
        },
      },
    },
  },
  defaults: {
    VCard: {
      elevation: 2,
      rounded: 'lg',
    },
    VBtn: {
      rounded: 'lg',
      style: 'text-transform: none; font-weight: 500;',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VTextarea: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VDataTable: {
      density: 'comfortable',
    },
  },
});

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(vuetify);
app.mount('#app');
