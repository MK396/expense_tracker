<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'


import AppHeader from './components/AppHeader.vue'
import ExpenseStats from './components/ExpenseStats.vue'
import ExpenseList from './components/ExpenseList.vue'
import ExpenseForm from './components/ExpenseForm.vue'
import BaseModal from './components/BaseModal.vue'
import ExpenseCharts from './components/ExpenseCharts.vue'
import ScannerForm from './components/ScannerForm.vue' // NOWY IMPORT

const expenses = ref([])
const isDark = ref(false)
const showForm = ref(false)
const showScanner = ref(false) // NOWY STAN

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
      @toggle-theme="toggleTheme"
      @toggle-form="showForm = !showForm"
      @toggle-scanner="showScanner = !showScanner" 
    />

    <ExpenseStats :expenses="expenses" />
    
    <ExpenseCharts :expenses="expenses" />

    <ExpenseList :expenses="expenses" />

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