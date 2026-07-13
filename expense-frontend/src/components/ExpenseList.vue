<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// Przyjmujemy listę wydatków z głównego widoku
const props = defineProps({
  expenses: {
    type: Array,
    required: true
  }
})

// Emitujemy zdarzenie do odświeżenia listy po usunięciu/edycji
const emit = defineEmits(['refresh-expenses'])

const categories = ref([])

onMounted(async () => {
  try {
    // Pobieramy kategorie, aby móc je wybierać w trybie edycji
    const { data } = await axios.get('http://127.0.0.1:8000/api/categories/')
    categories.value = data.map(c => c.name)
  } catch (e) {
    console.error("Błąd pobierania kategorii", e)
  }
})

// USUWANIE WYDATKU
const deleteExpense = async (id) => {
  if (!confirm("Na pewno chcesz usunąć ten wydatek?")) return;
  
  try {
    await axios.delete(`http://127.0.0.1:8000/api/expenses/${id}/`)
    emit('refresh-expenses') // Odśwież główny ekran
  } catch (e) {
    alert("Wystąpił błąd podczas usuwania.")
    console.error(e)
  }
}

// WŁĄCZANIE TRYBU EDYCJI NA KAFELKU
const toggleEdit = (expense) => {
  expense.isEditing = true
  // Tworzymy tymczasowe pola, żeby można było anulować bez psucia widoku
  expense.editName = expense.name
  expense.editAmount = expense.amount
  // Upewniamy się, że kategoria jest poprawnym stringiem
  expense.editCategory = typeof expense.category === 'object' ? expense.category.name : expense.category
}

// ZAPISYWANIE ZMIAN W WYDATKU
const saveExpense = async (expense) => {
  try {
    await axios.patch(`http://127.0.0.1:8000/api/expenses/${expense.id}/`, {
      name: expense.editName,
      amount: expense.editAmount,
      category: expense.editCategory
    })
    expense.isEditing = false
    emit('refresh-expenses') // Odśwież główny ekran z nową sumą
  } catch (e) {
    alert("Wystąpił błąd podczas zapisywania zmian.")
    console.error(e)
  }
}
</script>

<template>
  <div class="expense-grid">
    <div v-for="expense in expenses" :key="expense.id" class="expense-card">
      
      <!-- WIDOK STANDARDOWY KAFELKA -->
      <div v-if="!expense.isEditing" class="card-content">
        <div class="card-header">
          <!-- Dodane skracanie długich nazw -->
          <h3 class="card-title" :title="expense.name">{{ expense.name }}</h3>
          
          <!-- Akcje kafelka (Edycja i Kosz) -->
          <div class="card-actions">
            <button @click="toggleEdit(expense)" class="action-btn" title="Edytuj">✏️</button>
            <button @click="deleteExpense(expense.id)" class="action-btn delete-btn" title="Usuń">🗑️</button>
          </div>
        </div>
        
        <div class="card-body">
          <p class="amount">{{ expense.amount }} zł</p>
          <div class="card-footer">
            <span class="category-badge">{{ typeof expense.category === 'object' ? expense.category.name : expense.category }}</span>
            <span class="date">{{ expense.date }}</span>
          </div>
        </div>
      </div>

      <!-- TRYB EDYCJI (INLINE) -->
      <div v-else class="edit-mode">
        <input v-model="expense.editName" class="edit-input" placeholder="Nazwa wydatku" />
        <input type="number" step="0.01" v-model="expense.editAmount" class="edit-input amount-input" placeholder="Kwota" />
        
        <select v-model="expense.editCategory" class="edit-input">
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
        
        <div class="edit-actions">
          <button @click="saveExpense(expense)" class="btn-save">Zapisz</button>
          <button @click="expense.isEditing = false" class="btn-cancel">Anuluj</button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.expense-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.expense-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 15px;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
}

.expense-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

/* WIDOK STANDARDOWY */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.card-title {
  margin: 0;
  font-size: 1.1rem;
  color: var(--text-h);
  /* Truncate - ucinanie z wielokropkiem */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80%;
}

.card-actions {
  display: flex;
  gap: 8px;
  opacity: 0; /* Ukryte domyślnie */
  transition: opacity 0.2s;
}

/* Pokazujemy ikonki, gdy najedziesz na kafelek */
.expense-card:hover .card-actions {
  opacity: 1;
}

.action-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0;
  opacity: 0.6;
  transition: opacity 0.2s, transform 0.1s;
}

.action-btn:hover {
  opacity: 1;
  transform: scale(1.1);
}

.delete-btn:hover {
  opacity: 1;
}

.amount {
  font-size: 1.4rem;
  font-weight: bold;
  color: var(--accent);
  margin: 0 0 10px 0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: var(--text);
}

.category-badge {
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  padding: 4px 8px;
  border-radius: 8px;
  font-weight: 600;
}

/* TRYB EDYCJI */
.edit-mode {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.edit-input {
  background: var(--code-bg);
  color: var(--text-h);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px;
  font-size: 0.95rem;
}

.amount-input {
  font-weight: bold;
  color: var(--accent);
}

.edit-actions {
  display: flex;
  gap: 10px;
  margin-top: 5px;
}

.btn-save {
  background: #42b883;
  color: white;
  border: none;
  padding: 8px;
  border-radius: 6px;
  flex: 1;
  cursor: pointer;
  font-weight: bold;
}

.btn-cancel {
  background: #f43f5e;
  color: white;
  border: none;
  padding: 8px;
  border-radius: 6px;
  flex: 1;
  cursor: pointer;
  font-weight: bold;
}
</style>