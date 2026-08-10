<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const emit = defineEmits(['expense-added'])

// Stan formularza
const name = ref('')
const amount = ref('')
const category = ref('')
const date = ref(new Date().toISOString().split('T')[0])

const categories = ref([])
const newCategoryName = ref('')
const showAddCategory = ref(false)

// Słownik emotikon dla kategorii
const categoryEmojis = {
  'Jedzenie': '🍔',
  'Alkohol': '🍷',
  'Transport': '🚗',
  'Dom': '🏠',
  'Sport': '🏋️',
  'Restauracje': '🍽️',
  'Edukacja': '📚',
  'Prezenty': '🎁'
}

const getEmoji = (catName) => categoryEmojis[catName] || '🏷️'

// 1. Pobieranie kategorii z API
const fetchCategories = async () => {
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/categories/')
    categories.value = data.map(cat => cat.name)
    
    if (categories.value.length > 0 && !category.value) {
      category.value = categories.value[0]
    }
  } catch (error) {
    console.error("Błąd podczas pobierania kategorii:", error)
  }
}

// 2. Dodawanie nowej kategorii do bazy danych Django
const addNewCategory = async () => {
  const trimmed = newCategoryName.value.trim()
  if (trimmed && !categories.value.includes(trimmed)) {
    try {
      await axios.post('http://127.0.0.1:8000/api/categories/', { name: trimmed })
      
      categories.value.push(trimmed)
      category.value = trimmed 
      newCategoryName.value = ''
      showAddCategory.value = false
    } catch (error) {
      console.error("Błąd zapisu kategorii:", error)
      alert("Nie udało się zapisać nowej kategorii na serwerze.")
    }
  }
}

// 3. Wysyłanie wydatku
const handleSubmit = async () => {
  if (!name.value || !amount.value || !category.value) {
    return alert("Wypełnij wszystkie pola, w tym kategorię!")
  }

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
    console.error("Błąd podczas dodawania wydatku:", error)
    alert("Błąd połączenia z serwerem.")
  }
}

onMounted(fetchCategories)
</script>

<template>
  <div class="form-card">
    <div class="form-header">
      <h3>Dodaj Nowy Wydatek</h3>
    </div>

    <div class="inputs-grid">
      <div class="input-group">
        <label>Kwota (zł)</label>
        <input v-model="amount" type="number" step="0.01" placeholder="0.00" class="amount-input" />
      </div>

      <div class="input-group">
        <label>Nazwa wydatku</label>
        <input v-model="name" type="text" placeholder="np. Zakupy spożywcze" />
      </div>

      <div class="input-group">
        <label>Data</label>
        <input v-model="date" type="date" class="date-input" @click="$event.target.showPicker?.()" />
      </div>
    </div>

    <div class="category-section">
      <label>Kategoria</label>
      <div class="category-picker">
        <button 
          v-for="cat in categories" 
          :key="cat"
          type="button"
          :class="['category-btn', { active: category === cat }]"
          @click="category = cat"
        >
          <span>{{ getEmoji(cat) }}</span> {{ cat }}
        </button>
        
        <button 
          v-if="!showAddCategory"
          type="button" 
          class="category-btn add-btn" 
          @click="showAddCategory = true"
        >
          ➕ Nowa
        </button>
      </div>

      <div v-if="showAddCategory" class="add-category-input">
        <input 
          v-model="newCategoryName" 
          type="text" 
          placeholder="Nazwa kategorii..." 
          @keyup.enter="addNewCategory"
        />
        <button type="button" class="btn-save-cat" @click="addNewCategory">Dodaj</button>
        <button type="button" class="btn-cancel-cat" @click="showAddCategory = false">✕</button>
      </div>
    </div>

    <button class="submit-btn" @click="handleSubmit">Dodaj Wydatek +</button>
  </div>
</template>

<style scoped>
/* GŁÓWNY POJEMNIK W STYLU KAFELKA PODSUMOWANIA */
.form-card {
  background: var(--accent-text);
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  box-sizing: border-border-box;
}

.form-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}


.form-header h3 {
  margin: 0;
  font-size: 0.85rem;
  color: var(--accent);
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
}

/* SIATKA INPUTÓW */
.inputs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.input-group label,
.category-section label {
  font-size: 0.75rem;
  color: var(--accent);
  opacity: 0.8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

input {
  background: var(--bg);
  color: var(--text-h);
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  font-size: 0.95rem;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s ease;
}

input:focus {
  border-color: var(--accent);
}

.amount-input {
  font-weight: 800;
  color: var(--accent);
}

/* SEKCJA KATEGORII */
.category-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}

.category-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.category-btn {
  background: var(--bg);
  color: var(--accent);
  border: 1px solid var(--border);
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.category-btn:hover {
  background: var(--accent-bg);
}

.category-btn.active {
  background: var(--accent);
  color: var(--accent-text);
  border-color: var(--accent);
}

.add-btn {
  border: 1px dashed var(--accent);
  background: transparent;
  color: var(--accent);
}

/* INPUT DLA NOWEJ KATEGORII */
.add-category-input {
  display: flex;
  gap: 8px;
  margin-top: 6px;
  animation: fadeIn 0.2s ease;
}

.add-category-input input {
  flex: 1;
}

.btn-save-cat {
  background: var(--accent);
  color: var(--accent-text);
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
}

.btn-cancel-cat {
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 8px 12px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
}

/* PRZYCISK SUBMIT */
.submit-btn {
  background-color: var(--accent);
  color: var(--accent-text);
  font-size: 1rem;
  font-weight: 800;
  border: none;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 4px;
  transition: opacity 0.2s ease, transform 0.1s ease;
}

.submit-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>