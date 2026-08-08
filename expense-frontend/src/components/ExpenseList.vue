<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// Przyjmuje przefiltrowaną listę wydatków
const props = defineProps({
  expenses: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['refresh-expenses'])

const categories = ref([])

// Funkcja formatująca datę z YYYY-MM-DD (lub ISO) na DD-MM-YYYY
const formatDate = (rawDate) => {
  if (!rawDate) return ''
  const d = new Date(rawDate)
  if (isNaN(d.getTime())) return rawDate

  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()

  return `${day}-${month}-${year}`
}

const shopKeywords = {
  'kaufland': 'Kaufland',
  'biedronka': 'Biedronka',
  'jeronimo martins': 'Biedronka',
  'lidl': 'Lidl',
  'zabka': 'Żabka',
  'żabka': 'Żabka',
  'dino': 'Dino',
  'auchan': 'Auchan',
  'carrefour': 'Carrefour',
  'rossmann': 'Rossmann',
  'pepco': 'Pepco',
  'action': 'Action',
  'castorama': 'Castorama',
  'leroy merlin': 'Leroy Merlin',
  'orlen': 'Orlen',
  'mcdonald': 'McDonald\'s',
  'kfc': 'KFC'
}

const normalizeShopName = (rawName) => {
  if (!rawName) return 'Inne'
  const cleanName = rawName.toLowerCase().trim()

  for (const [keyword, prettyName] of Object.entries(shopKeywords)) {
    if (cleanName.includes(keyword)) {
      return prettyName
    }
  }

  return rawName
}

const categoryColors = {
  'Jedzenie': '#F8AD9D',
  'Alkohol': '#FFD166',
  'Transport': '#C77DFF',
  'Dom': '#B8C0FF',
  'Sport': '#74B9FF',
  'Restauracje': '#F4ACB7',
  'Edukacja': '#CBFFC0',
  'Prezenty': '#FFEAA7',
  'Inne': '#D3D3D3'
}

const getCategoryColor = (category) => {
  const catName = typeof category === 'object' ? category.name : category
  
  if (categoryColors[catName]) {
    return categoryColors[catName]
  }

  let hash = 0
  const name = catName || 'Inne'
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash) % 360
  return `hsl(${hue}, 65%, 75%)`
}

onMounted(async () => {
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/categories/')
    categories.value = data.map(c => c.name)
  } catch (e) {
    console.error("Błąd pobierania kategorii", e)
  }
})

const deleteExpense = async (id) => {
  if (!confirm("Na pewno chcesz usunąć ten wydatek?")) return;
  
  try {
    await axios.delete(`http://127.0.0.1:8000/api/expenses/${id}/`)
    emit('refresh-expenses')
  } catch (e) {
    alert("Wystąpił błąd podczas usuwania.")
    console.error(e)
  }
}

const toggleEdit = (expense) => {
  expense.isEditing = true
  expense.editName = expense.name
  expense.editAmount = expense.amount
  expense.editCategory = typeof expense.category === 'object' ? expense.category.name : expense.category
}

const saveExpense = async (expense) => {
  try {
    await axios.patch(`http://127.0.0.1:8000/api/expenses/${expense.id}/`, {
      name: expense.editName,
      amount: expense.editAmount,
      category: expense.editCategory
    })
    expense.isEditing = false
    emit('refresh-expenses')
  } catch (e) {
    alert("Wystąpił błąd podczas zapisywania zmian.")
    console.error(e)
  }
}
</script>

<template>
  <div class="list-wrapper">
    <div v-if="expenses.length > 0" class="expense-grid">
      <div v-for="expense in expenses" :key="expense.id" class="card">
        
        <template v-if="!expense.isEditing">
          <div class="card-main">
            <div class="card-info">
              <div class="card-header">
                <h3 :title="expense.name">{{ normalizeShopName(expense.name) }}</h3>
                
                <div class="card-actions">
                  <button @click="toggleEdit(expense)" class="action-btn" title="Edytuj">✏️</button>
                  <button @click="deleteExpense(expense.id)" class="action-btn" title="Usuń">🗑️</button>
                </div>
              </div>
              
              <p class="amount">{{ Number(expense.amount).toFixed(2) }} zł</p>
            </div>
          </div>

          <div class="card-footer">
            <span 
              class="category-badge" 
              :style="{ backgroundColor: getCategoryColor(expense.category) }"
            >
              {{ typeof expense.category === 'object' ? expense.category.name : expense.category }}
            </span>
            <span class="date">{{ formatDate(expense.date) }}</span>
          </div>
        </template>

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

    <div v-else class="no-data-msg">
      <p>Brak wydatków w wybranym przedziale czasowym.</p>
    </div>
  </div>
</template>

<style scoped>
.list-wrapper {
  width: 100%;
}

.expense-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1.25rem;
}

.card {
  background: var(--accent-text);
  padding: 1.25rem;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: var(--shadow);
  position: relative;
}

.card:hover {
  transform: translateY(-3px);
}

.card-main {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  width: 100%;
}

.card-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.card-info h3 {
  margin: 0;
  font-size: 0.8rem;
  color: var(--accent);
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
}

.card-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.card:hover .card-actions {
  opacity: 1;
}

.action-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 2px;
  line-height: 1;
  transition: transform 0.1s ease;
}

.action-btn:hover {
  transform: scale(1.2);
}

.card-info p.amount {
  margin: 4px 0 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--accent);
  text-align: center;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  margin-top: 0.25rem;
}

.category-badge {
  color: #1a252c;
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.75rem;
  white-space: nowrap;
}

.date {
  font-size: 0.75rem;
  color: var(--accent);
  opacity: 0.7;
  font-weight: 600;
  white-space: nowrap;
}

.no-data-msg {
  padding: 40px;
  text-align: center;
  color: var(--accent);
  font-style: italic;
}

.edit-mode {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.edit-input {
  background: var(--bg);
  color: var(--text-h);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 0.85rem;
  font-family: inherit;
  outline: none;
}

.edit-input:focus {
  border-color: var(--accent);
}

.amount-input {
  font-weight: bold;
  color: var(--accent);
}

.edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.btn-save {
  background: var(--accent);
  color: var(--accent-text);
  border: none;
  padding: 8px;
  border-radius: 8px;
  flex: 1;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.8rem;
  font-family: inherit;
}

.btn-cancel {
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 8px;
  border-radius: 8px;
  flex: 1;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.8rem;
  font-family: inherit;
}
</style>