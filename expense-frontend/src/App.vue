<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// Importy komponentów
import AppHeader from './components/AppHeader.vue'
import ExpenseStats from './components/ExpenseStats.vue'
import ExpenseList from './components/ExpenseList.vue'
import ExpenseForm from './components/ExpenseForm.vue'
import BaseModal from './components/BaseModal.vue'

// Stan aplikacji
const expenses = ref([])
const isDark = ref(false)
const showForm = ref(false)

// Logika motywu
const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

// Logika danych
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
    />

    <ExpenseStats :expenses="expenses" />
    
    <ExpenseList :expenses="expenses" />

    <BaseModal :show="showForm" @close="showForm = false">
      <ExpenseForm @expense-added="handleExpenseAdded" />
    </BaseModal>
  </div>
</template>

<style>
/* Tu zostaw tylko globalne style kontenera */
.container {
  width: 100%;           /* Zajmij 100% szerokości */
  max-width: 100%;       /* Usuń ograniczenie do 1000px */
  padding: 0 40px;       /* Zostaw tylko lekki margines wewnętrzny, żeby treść nie dotykała krawędzi ekranu */
  box-sizing: border-box; /* Ważne: zapobiega wychodzeniu poza ekran przy paddingu */
}
</style>