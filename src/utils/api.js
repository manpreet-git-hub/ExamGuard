import axios from 'axios';
import { TOKEN_STORAGE_KEY } from './auth';

const configuredApiUrl = (import.meta.env.VITE_API_URL || '').trim().replace(/\/$/, '');

const api = axios.create({
  baseURL: configuredApiUrl,
  timeout: 20000,
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      delete api.defaults.headers.common.Authorization;
      if (!['/login', '/register'].includes(window.location.pathname)) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

export function getWsUrl(path) {
  const origin = (configuredApiUrl || window.location.origin).replace(
    /^http/i,
    protocol => (protocol.toLowerCase() === 'https' ? 'wss' : 'ws')
  );
  return new URL(path, origin).toString();
}

export default api;
