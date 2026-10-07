<template>
  <div class="auth-overlay">
    <div class="auth-card">
      <h2>{{ isRegistering ? 'Załóż nowe konto' : 'Logowanie do Expense Tracker' }}</h2>
      <p class="subtitle">
        {{ isRegistering ? 'Utwórz konto, aby zarządzać swoimi wydatkami' : 'Wprowadź dane, aby uzyskać dostęp do swoich wydatków' }}
      </p>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="username">Login</label>
          <input 
            id="username" 
            v-model="username" 
            type="text" 
            placeholder="np. admin" 
            required 
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label for="password">Hasło</label>
          <input 
            id="password" 
            v-model="password" 
            type="password" 
            placeholder="••••••••" 
            required 
            autocomplete="current-password"
          />
        </div>

        <button type="submit" :disabled="loading" class="btn-submit">
          {{ loading ? 'Przetwarzanie...' : (isRegistering ? 'Zarejestruj się' : 'Zaloguj się') }}
        </button>

        <p v-if="error" class="error-msg">{{ error }}</p>

        <div class="switch-mode">
          <span>{{ isRegistering ? 'Masz już konto?' : 'Nie masz konta?' }}</span>
          <button type="button" class="link-btn" @click="toggleMode">
            {{ isRegistering ? 'Zaloguj się' : 'Zarejestruj się' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import api from '../api';

const emit = defineEmits(['login-success']);

const isRegistering = ref(false);
const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

const toggleMode = () => {
  isRegistering.value = !isRegistering.value;
  error.value = '';
};

const handleSubmit = async () => {
  loading.value = true;
  error.value = '';

  try {
    if (isRegistering.value) {
      // 1. Rejestracja nowego użytkownika w API
      await api.post('register/', {
        username: username.value,
        password: password.value,
      });
    }

    // 2. Pobranie tokenów JWT (dla logowania lub automatycznie po rejestracji)
    const res = await api.post('token/', {
      username: username.value,
      password: password.value,
    });

    localStorage.setItem('access_token', res.data.access);
    localStorage.setItem('refresh_token', res.data.refresh);
    emit('login-success');
  } catch (err) {
    if (isRegistering.value) {
      // Obsługa błędów walidacji z Django (np. "Użytkownik o tej nazwie już istnieje")
      const data = err.response?.data;
      if (data?.username) {
        error.value = Array.isArray(data.username) ? data.username[0] : data.username;
      } else if (data?.password) {
        error.value = Array.isArray(data.password) ? data.password[0] : data.password;
      } else {
        error.value = 'Błąd rejestracji. Sprawdź poprawność danych.';
      }
    } else {
      error.value = 'Niepoprawny login lub hasło.';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.auth-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.auth-card {
  background: #ffffff;
  padding: 2.5rem;
  border-radius: 12px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  color: #1e293b;
}

.subtitle {
  color: #64748b;
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
  display: flex;
  flex-direction: column;
}

label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
  margin-bottom: 0.35rem;
}

input {
  padding: 0.65rem 0.85rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.2s;
}

input:focus {
  border-color: #3b82f6;
}

.btn-submit {
  width: 100%;
  padding: 0.75rem;
  background-color: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 0.5rem;
}

.btn-submit:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.btn-submit:disabled {
  background-color: #94a3b8;
  cursor: not-allowed;
}

.error-msg {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 1rem;
  text-align: center;
}

.switch-mode {
  margin-top: 1.25rem;
  text-align: center;
  font-size: 0.875rem;
  color: #64748b;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.35rem;
}

.link-btn {
  background: none;
  border: none;
  color: #2563eb;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  font-size: 0.875rem;
  text-decoration: underline;
}

.link-btn:hover {
  color: #1d4ed8;
}
</style>