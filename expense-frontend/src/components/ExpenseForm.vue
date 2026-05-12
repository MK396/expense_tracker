<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['expense-added'])
const getTodayDate = () => new Date().toISOString().split('T')[0]

const categories = ['Jedzenie', 'Transport', 'Rozrywka', 'Mieszkanie', 'Inne']
const name = ref('')
const amount = ref('')
const category = ref('Jedzenie')
const date = ref(getTodayDate())

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
    </div>
    <button @click="handleSubmit">Dodaj +</button>
  </div>
</template>

<style scoped>
.form-container {
  /* Używamy zmiennej --code-bg jako tła panelu */

  background: var(--code-bg);
  padding: 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
  border: 1px solid var(--border);
  transition: all 0.3s ease;
}

input, select {
  background: var(--bg);
  color: var(--text-h);
  padding: 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  font-family: var(--sans);
  flex: 1;
}

/* Styl dla placeholderów, żeby zmieniały kolor w Dark Mode */
input::placeholder {
  color: var(--text);
  opacity: 0.6;
}

button {
  background-color: var(--accent);
  color: #fff;
  padding: 10px 20px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-family: var(--heading);
  transition: transform 0.1s, opacity 0.2s;
}

button:hover {
  opacity: 0.9;
}

button:active {
  transform: scale(0.98);
}

.date-input {
  background: var(--bg);
  color: var(--text-h);
  padding: 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  font-family: var(--sans);
}

.category-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 10px 0;
}

.category-btn {
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 20px; /* Zaokrąglone przyciski typu "pills" */
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  flex-grow: 1; /* Przyciski wypełnią szerokość */
}

/* Styl dla aktywnego (wybranego) przycisku */
.category-btn.active {
  background-color: var(--accent);
  color: white;
  border-color: var(--accent);
  box-shadow: var(--shadow);
}

.category-btn:hover:not(.active) {
  border-color: var(--accent);
}


/* W niektórych przeglądarkach ikonka kalendarza jest ciemna, 
   można ją odwrócić w trybie ciemnym */
[data-theme='dark'] .date-input::-webkit-calendar-picker-indicator {
  filter: invert(1);
}

/* RWD - na telefonach formularz będzie w pionie */
@media (max-width: 600px) {
  .form-container {
    flex-direction: column;
  }
}
</style>