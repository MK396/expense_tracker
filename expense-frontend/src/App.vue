<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from './api'

import AppHeader from './components/AppHeader.vue'
import ExpenseStats from './components/ExpenseStats.vue'
import ExpenseList from './components/ExpenseList.vue'
import ExpenseForm from './components/ExpenseForm.vue'
import BaseModal from './components/BaseModal.vue'
import ExpenseCharts from './components/ExpenseCharts.vue'
import ScannerForm from './components/ScannerForm.vue'
import LoginModal from './components/LoginModal.vue'

const isAuthenticated = ref(false)
const expenses = ref([])
const isDark = ref(false)
const showForm = ref(false)
const showScanner = ref(false)
const timeRange = ref('30')

// Główny stan filtru miesiąca i roku
const selectedMonth = ref(new Date().getMonth())
const selectedYear = ref(new Date().getFullYear())

const checkAuth = () => {
  isAuthenticated.value = !!localStorage.getItem('access_token')
}

const handleLoginSuccess = () => {
  isAuthenticated.value = true
  fetchExpenses()
}

const handleLogout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  isAuthenticated.value = false
  expenses.value = []
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

const fetchExpenses = async () => {
  if (!isAuthenticated.value) return
  try {
    const { data } = await api.get('expenses/')
    expenses.value = data
  } catch (error) {
    console.error("Błąd pobierania wydatków:", error)
  }
}

// Wyselekcjonowane wydatki dla wybranego miesiąca i roku (dla listy i statystyk)
const monthlyFilteredExpenses = computed(() => {
  return expenses.value.filter(expense => {
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

onMounted(() => {
  checkAuth()
  if (isAuthenticated.value) {
    fetchExpenses()
  }
  window.addEventListener('auth-expired', handleLogout)
})

onUnmounted(() => {
  window.removeEventListener('auth-expired', handleLogout)
})
</script>

<template>
  <!-- Modal logowania, gdy użytkownik nie ma aktywnego tokenu -->
  <LoginModal v-if="!isAuthenticated" @login-success="handleLoginSuccess" />

  <!-- Główny interfejs aplikacji po poprawnym zalogowaniu -->
  <div v-else class="container">
    <div class="user-session-bar">
      <button class="btn-logout" @click="handleLogout">Wyloguj</button>
    </div>

    <AppHeader 
      :is-dark="isDark" 
      :show-form="showForm"
      :expenses="expenses"
      v-model:selectedMonth="selectedMonth"
      v-model:selectedYear="selectedYear"
      @toggle-theme="toggleTheme"
      @toggle-form="showForm = !showForm"
      @toggle-scanner="showScanner = !showScanner" 
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

    <!-- Przekazujemy przefiltrowaną listę po wybranym miesiącu -->
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
  padding-top: 16px;
}

.btn-logout {
  background-color: #ef4444;
  color: #ffffff;
  border: none;
  padding: 6px 14px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-logout:hover {
  opacity: 0.9;
}
</style>