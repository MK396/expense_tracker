<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api, { getAccessToken, setAccessToken } from './api'
import { enterGuestMode, getAuthMode, setAuthMode } from './guestStore'
import { listExpenses } from './dataService'

import AppHeader from './components/AppHeader.vue'
import ExpenseStats from './components/ExpenseStats.vue'
import ExpenseList from './components/ExpenseList.vue'
import ExpenseForm from './components/ExpenseForm.vue'
import BaseModal from './components/BaseModal.vue'
import ExpenseCharts from './components/ExpenseCharts.vue'
import ScannerForm from './components/ScannerForm.vue'
import LoginModal from './components/LoginModal.vue'

const isAuthenticated = ref(false)
const isGuest = ref(false)
const showLoginModal = ref(false)
const expenses = ref([])
const isDark = ref(false)
const showForm = ref(false)
const showScanner = ref(false)

const selectedMonth = ref(new Date().getMonth())
const selectedYear = ref(new Date().getFullYear())

const hasSession = computed(() => isAuthenticated.value || isGuest.value)

const checkAuth = async () => {
  const mode = getAuthMode()

  if (mode === 'guest') {
    isGuest.value = true
    isAuthenticated.value = false
    showLoginModal.value = false
    return
  }

  try {
    if (!getAccessToken()) {
      const { data } = await api.post('token/refresh/')
      setAccessToken(data.access)
    }
    isAuthenticated.value = true
    isGuest.value = false
    setAuthMode('user')
    showLoginModal.value = false
    return
  } catch {
    setAccessToken(null)
    if (mode === 'user') {
      setAuthMode(null)
    }
  }

  isAuthenticated.value = false
  isGuest.value = false
  showLoginModal.value = true
}

const handleLoginSuccess = () => {
  setAuthMode('user')
  isAuthenticated.value = true
  isGuest.value = false
  showLoginModal.value = false
  fetchExpenses()
}

const handleContinueAsGuest = () => {
  enterGuestMode()
  isGuest.value = true
  isAuthenticated.value = false
  showLoginModal.value = false
  fetchExpenses()
}

const handleLogout = async () => {
  try {
    await api.post('logout/')
  } catch {
    // ignoruj — lokalne wyczyszczenie sesji i tak następuje
  }
  setAccessToken(null)
  setAuthMode(null)
  isAuthenticated.value = false
  isGuest.value = false
  expenses.value = []
  showLoginModal.value = true
}

const openLoginFromGuest = () => {
  showLoginModal.value = true
}

const cancelLoginModal = () => {
  if (isGuest.value) {
    showLoginModal.value = false
  }
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

const fetchExpenses = async () => {
  if (!hasSession.value) return
  try {
    expenses.value = await listExpenses()
  } catch (error) {
    console.error('Błąd pobierania wydatków:', error)
  }
}

const monthlyFilteredExpenses = computed(() => {
  return expenses.value.filter((expense) => {
    const d = new Date(expense.date || expense.data)
    return (
      d.getMonth() === Number(selectedMonth.value) &&
      d.getFullYear() === Number(selectedYear.value)
    )
  })
})

const handleExpenseAdded = () => {
  fetchExpenses()
  showForm.value = false
}

const openScanner = () => {
  showScanner.value = true
}

onMounted(async () => {
  await checkAuth()
  if (hasSession.value) {
    fetchExpenses()
  }
  window.addEventListener('auth-expired', handleLogout)
})

onUnmounted(() => {
  window.removeEventListener('auth-expired', handleLogout)
})
</script>

<template>
  <LoginModal
    v-if="showLoginModal"
    :allow-guest="!isAuthenticated"
    :dismissible="isGuest"
    @login-success="handleLoginSuccess"
    @continue-as-guest="handleContinueAsGuest"
    @cancel="cancelLoginModal"
  />

  <div v-if="hasSession" class="container">
    <div class="user-session-bar">
      <span v-if="isGuest" class="guest-badge">
        Tryb gościa — dane tylko w tej przeglądarce
      </span>
      <button v-if="isGuest" class="btn-login" @click="openLoginFromGuest">
        Zaloguj się
      </button>
      <button v-else class="btn-logout" @click="handleLogout">Wyloguj</button>
    </div>

    <AppHeader 
      :is-dark="isDark" 
      :show-form="showForm"
      :expenses="expenses"
      v-model:selectedMonth="selectedMonth"
      v-model:selectedYear="selectedYear"
      @toggle-theme="toggleTheme"
      @toggle-form="showForm = !showForm"
      @toggle-scanner="openScanner" 
    />

    <ExpenseStats 
      :expenses="expenses" 
      :selected-month="selectedMonth"
      :selected-year="selectedYear"
    />
    
    <ExpenseCharts 
      :expenses="expenses" 
      :selected-month="selectedMonth" 
      :selected-year="selectedYear" 
    />

    <ExpenseList 
      :expenses="monthlyFilteredExpenses" 
      @refresh-expenses="fetchExpenses" 
    />

    <BaseModal :show="showForm" @close="showForm = false">
      <ExpenseForm @expense-added="handleExpenseAdded" />
    </BaseModal>

    <BaseModal :show="showScanner" @close="showScanner = false">
      <ScannerForm @expenses-added="() => { fetchExpenses(); showScanner = false; }" />
    </BaseModal>
  </div>
</template>

<style>
.container {
  width: 100%;
  max-width: 100%;
  padding: 0 40px;
  box-sizing: border-box;
}

.user-session-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding-top: 16px;
}

.guest-badge {
  font-size: 0.8rem;
  color: var(--accent, #64748b);
  opacity: 0.85;
}

.btn-logout,
.btn-login {
  border: none;
  padding: 6px 14px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-logout {
  background-color: #ef4444;
  color: #ffffff;
}

.btn-login {
  background-color: #2563eb;
  color: #ffffff;
}

.btn-logout:hover,
.btn-login:hover {
  opacity: 0.9;
}
</style>
