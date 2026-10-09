import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Zezwala na obsługę ciasteczek HttpOnly
  headers: {
    'Content-Type': 'application/json',
  },
});

// Access token przechowywany bezpiecznie w pamięci podręcznej (nie w localStorage)
let currentAccessToken = null;

export const setAccessToken = (token) => {
  currentAccessToken = token;
};

export const getAccessToken = () => currentAccessToken;

// Interceptor żądań: automatycznie dodaje nagłówek Authorization
api.interceptors.request.use((config) => {
  if (currentAccessToken && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${currentAccessToken}`;
  }
  return config;
});

// Zmienne do obsługi jednoczesnych zapytań w trakcie odświeżania
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Interceptor odpowiedzi: cichy refresh tokena (Silent Refresh)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Pomijamy odświeżanie, jeśli błąd dotyczy samego endpointu logowania lub odświeżania
    const isAuthEndpoint = originalRequest.url?.includes('token/');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        // Jeśli inne zapytanie już odświeża token, wrzucamy to żądanie do kolejki oczekujących
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Ciasteczko HttpOnly z refresh_tokenem zostanie przesłane automatycznie
        const response = await api.post('token/refresh/');
        const newAccessToken = response.data.access;

        setAccessToken(newAccessToken);
        processQueue(null, newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh token wygasł lub jest nieprawidłowy – sesja zakończona
        processQueue(refreshError, null);
        setAccessToken(null);
        window.dispatchEvent(new Event('auth-expired'));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;