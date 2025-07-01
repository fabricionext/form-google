import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import emitter from './eventBus'; // Importar o event bus

// instância principal
export const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // cookies (refresh / csrf)
});

// injeta Bearer em cada request
api.interceptors.request.use(cfg => {
  const auth = useAuthStore();
  if (auth.access) cfg.headers.Authorization = `Bearer ${auth.access}`;
  // CSRF para métodos mutantes
  if (['post', 'put', 'patch', 'delete'].includes(cfg.method ?? ''))
    cfg.headers['X-CSRF-Token'] = auth.csrf;
  return cfg;
});

// refresh automático se o access expirar
api.interceptors.response.use(null, async err => {
  const auth = useAuthStore();
  const cfg = err.config;
  if (
    err.response?.status === 401 &&
    !cfg.__isRetryRequest &&
    auth.refresh // refresh cookie presente?
  ) {
    try {
      const { data } = await api.post('/auth/refresh'); // cookie HttpOnly faz o trabalho
      auth.setAccess(data.access_token, data.csrf); // atualiza store
      cfg.__isRetryRequest = true;
      return api(cfg); // repete requisição original
    } catch {
      auth.logout();
    }
  }

  // Tratar erros de forma global
  if (err.response && err.response.status !== 401) {
    const message =
      err.response?.data?.error?.message ||
      err.response?.data?.message ||
      'Ocorreu um erro no servidor.';
    emitter.emit('api-error', `Erro ${err.response.status}: ${message}`);
  } else if (!err.response) {
    emitter.emit('api-error', 'Erro de conexão. Verifique sua rede.');
  }

  return Promise.reject(err);
});
