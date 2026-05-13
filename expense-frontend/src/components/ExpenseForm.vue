<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['expense-added'])
const getTodayDate = () => new Date().toISOString().split('T')[0]

// Zamieniamy na ref, aby tablica była reaktywna
const categories = ref(['Jedzenie', 'Transport', 'Rozrywka', 'Mieszkanie', 'Inne'])
const newCategoryName = ref('')
const showAddCategory = ref(false)

const name = ref('')
const amount = ref('')
const category = ref('Jedzenie')
const date = ref(getTodayDate())

// Funkcja dodawania nowej kategorii do listy
const addNewCategory = () => {
  const trimmed = newCategoryName.value.trim()
  if (trimmed && !categories.value.includes(trimmed)) {
    categories.value.push(trimmed)
    category.value = trimmed // Automatycznie wybierz nową kategorię
    newCategoryName.value = ''
    showAddCategory.value = false
  }
}

const handleSubmit = async () => {
  if (!name.value || !amount.value) return alert("Wypełnij wszystkie pola!")

  const newExpense = {
    name: name.value,
    amount: parseFloat(amount.value),
    category: category.value,
    date: date.value
  }

  try {
    await axios.post('http://127.0.0.1:8000/api/expenses/', newExpense)
    name.value = ''
    amount.value = ''
    emit('expense-added')
  } catch (error) {
    console.error("Błąd podczas dodawania:", error)
    alert("Błąd połączenia z serwerem.")
  }
}
</script>

<template>
  <div class="form-container">
    <input v-model="amount" type="number" placeholder="Kwota" />
    <input v-model="name" type="text" placeholder="Nazwa wydatku" />
    <input v-model="date" type="date" class="date-input" @click="$event.target.showPicker?.()" />
    
    <div class="category-section">
      <label>Kategoria:</label>
      <div class="category-picker">
          <button 
            v-for="cat in categories" 
            :key="cat"
            type="button"
            :class="['category-btn', { active: category === cat }]"
            @click="category = cat"
          >
            {{ cat }}
          </button>
          
          <!-- Przycisk otwierający pole dodawania -->
          <button 
            v-if="!showAddCategory"
            type="button" 
            class="category-btn add-btn" 
            @click="showAddCategory = true"
          >
            + Nowa
          </button>
      </div>

      <!-- Ukryte pole dodawania nowej kategorii -->
      <div v-if="showAddCategory" class="add-category-input">
        <input 
          v-model="newCategoryName" 
          type="text" 
          placeholder="Nazwa kategorii..." 
          @keyup.enter="addNewCategory"
        />
        <button type="button" @click="addNewCategory">Dodaj</button>
        <button type="button" class="cancel-btn" @click="showAddCategory = false">✕</button>
      </div>
    </div>

    <button class="submit-btn" @click="handleSubmit">Dodaj Wydatek +</button>
  </div>
</template>

<style scoped>
/* Zachowujemy Twoje style i dodajemy poprawki dla kategorii */

.category-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-section label {
  font-size: 0.9rem;
  color: var(--text);
  font-weight: 600;
}

.category-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.add-btn {
  border: 1px dashed var(--accent) !important;
  color: var(--accent) !important;
  background: transparent !important;
}

.add-category-input {
  display: flex;
  gap: 8px;
  margin-top: 5px;
  animation: fadeIn 0.3s ease;
}

.cancel-btn {
  background: #ff7675 !important;
}

.submit-btn {
  margin-top: 10px;
  background-color: var(--accent);
  font-size: 1.1rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Reszta Twoich stylów ... */
.form-container {
  background: var(--code-bg);
  padding: 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 1px solid var(--border);
}

input {
  background: var(--bg);
  color: var(--text-h);
  padding: 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
}

.category-btn {
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
}

.category-btn.active {
  background-color: var(--accent);
  color: white;
}
</style>