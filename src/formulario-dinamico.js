import { createApp } from 'vue';
import { createPinia } from 'pinia';
import FormularioDinamicoApp from './components/FormularioDinamicoApp.vue';

// Aguardar DOM estar pronto
document.addEventListener('DOMContentLoaded', () => {
  const app = createApp(FormularioDinamicoApp);
  const pinia = createPinia();

  app.use(pinia);

  // Montar aplicação no container existente
  const container = document.getElementById('formulario-dinamico-vue');
  if (container) {
    app.mount(container);
  } else {
    console.error('Container #formulario-dinamico-vue não encontrado');
  }
});
