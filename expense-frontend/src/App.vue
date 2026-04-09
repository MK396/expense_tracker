<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// 1. Reaktywna zmienna na wydatki
const expenses = ref([])

// 2. Funkcja pobierająca dane z Django
const fetchExpenses = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/expenses/')
    expenses.value = response.data
  } catch (error) {
    console.error("Błąd pobierania:", error)
    alert("Nie udało się połączyć z API Django!")
  }
}

// 3. Uruchom pobieranie, gdy strona się załaduje
onMounted(() => {
  fetchExpenses()
})
</script>

<template>
  <div class="container">
    <h1>Mój Tracker Wydatków</h1>
    
    <div v-if="expenses.length === 0">Ładowanie wydatków lub brak danych...</div>
    
    <table v-else border="1">
      <thead>
        <tr>
          <th>Nazwa</th>
          <th>Kwota</th>
          <th>Kategoria</th>
          <th>Data</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="expense in expenses" :key="expense.id">
          <td>{{ expense.name }}</td>
          <td>{{ expense.amount }} zł</td>
          <td>{{ expense.category }}</td>
          <td>{{ expense.date }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style>
</style>