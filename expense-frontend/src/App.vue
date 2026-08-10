<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

import AppHeader from './components/AppHeader.vue'
import ExpenseStats from './components/ExpenseStats.vue'
import ExpenseList from './components/ExpenseList.vue'
import ExpenseForm from './components/ExpenseForm.vue'
import BaseModal from './components/BaseModal.vue'
import ExpenseCharts from './components/ExpenseCharts.vue'
import ScannerForm from './components/ScannerForm.vue'

const expenses = ref([])
const isDark = ref(false)
const showForm = ref(false)
const showScanner = ref(false)
const timeRange = ref('30')

// Główny stan filtru miesiąca i roku
const selectedMonth = ref(new Date().getMonth())
const selectedYear = ref(new Date().getFullYear())

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

const fetchExpenses = async () => {
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/expenses/')
    expenses.value = data
  } catch (error) {
    console.error("Błąd:", error)
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

onMounted(fetchExpenses)
</script>

<template>
  <div class="container">
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
      v-model:timeRange="timeRange" 
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
</style>