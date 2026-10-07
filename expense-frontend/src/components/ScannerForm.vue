<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const emit = defineEmits(['expenses-added'])

const fileInput = ref(null)
const isLoading = ref(false)
const products = ref([])
const categories = ref([])

const shopName = ref('')
const shopNip = ref('')
const totalSum = ref('') 
const usedModel = ref('')

// Względne ścieżki zgodne z baseURL z src/api.js
const selectedEndpoint = ref('scan/') 

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

onMounted(async () => {
  try {
    const { data } = await api.get('categories/')
    categories.value = data.map(c => c.name)
  } catch (e) {
    console.error("Błąd pobierania kategorii", e)
  }
})

const triggerScan = (endpoint) => {
  selectedEndpoint.value = endpoint
  fileInput.value.click()
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  isLoading.value = true
  products.value = []
  shopName.value = ''
  shopNip.value = ''
  totalSum.value = ''
  usedModel.value = ''

  const formData = new FormData()
  formData.append('receipt', file)

  try {
    const { data } = await api.post(selectedEndpoint.value, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (data.status === 'success') {
      const scanResult = data.produkty
      
      shopName.value = scanResult.sklep
      shopNip.value = scanResult.nip
      totalSum.value = scanResult.suma_calkowita 
      if (data.model) usedModel.value = data.model

      products.value = scanResult.produkty.map(p => ({
        ...p,
        selected: true,
        split: false,
        category: categories.value.length > 0 ? categories.value[0] : ''
      }))
    }
  } catch (error) {
    alert("Wystąpił błąd podczas analizy paragonu.")
    console.error(error)
  } finally {
    isLoading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

const saveSelected = async () => {
  const selectedProducts = products.value.filter(p => p.selected)

  if (selectedProducts.length === 0) {
    return alert("Wybierz przynajmniej jeden produkt.")
  }

  const itemsList = selectedProducts.map(p => {
    const originalAmount = parseFloat(p.amount) || 0

    return {
      name: p.name,
      amount: parseFloat(originalAmount.toFixed(2)),
      category: p.category,
      split: p.split
    }
  })

  const calculatedTotal = selectedProducts.reduce((sum, p) => {
    const amt = parseFloat(p.amount) || 0
    return sum + (p.split ? amt / 2 : amt)
  }, 0)

  const mainCategory = itemsList[0]?.category || (categories.value[0] || 'Jedzenie')

  const expensePayload = {
    name: shopName.value || 'Zakupy (Paragon)',
    amount: parseFloat(calculatedTotal.toFixed(2)),
    category: mainCategory,
    date: new Date().toISOString().split('T')[0],
    items: itemsList
  }

  try {
    await api.post('expenses/', expensePayload)
    emit('expenses-added')
  } catch (e) {
    alert("Błąd zapisu paragonu. Upewnij się, że kategoria istnieje w bazie.")
    console.error(e)
  }
}
</script>

<template>
  <div class="scanner-card">
    <div class="card-header">
      <h3>Skaner Paragonów</h3>
    </div>

    <div v-if="isLoading" class="loading-box">
      <div class="spinner"></div>
      <p class="loading-text">Analizowanie paragonu</p>
    </div>

    <div v-else class="upload-section">
      <input type="file" ref="fileInput" accept="image/*" style="display: none" @change="handleFileUpload" />
      
      <div class="scan-buttons-grid">
        <button class="upload-btn" @click="triggerScan('scan/')">
          Skanuj (EasyOCR - Lokalnie)
        </button>

        <button class="upload-btn btn-gemini" @click="triggerScan('scan-gemini/')">
          Skanuj (Gemini AI - Chmura)
        </button>
      </div>
    </div>

    <div v-if="products.length > 0" class="results-section">
      <div class="metadata-box">
        <div class="meta-item">
          <span class="meta-label">Sklep:</span>
          <span class="meta-value">{{ shopName || 'Nie rozpoznano' }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">NIP:</span>
          <span class="meta-value">{{ shopNip || '-' }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Suma paragonu:</span>
          <span class="meta-value amount-meta">{{ totalSum }} zł</span>
        </div>
        <div v-if="usedModel" class="meta-item model-badge">
          <span class="meta-label">Model AI:</span>
          <span class="meta-value">{{ usedModel }}</span>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="receipt-table">
          <thead>
            <tr>
              <th class="text-center">+</th>
              <th>Produkt</th>
              <th>Cena (zł)</th>
              <th class="text-center">½</th>
              <th>Kategoria</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(prod, idx) in products" :key="idx" :class="{ 'split-row': prod.split }">
              <td class="text-center">
                <input type="checkbox" v-model="prod.selected" class="custom-checkbox" />
              </td>
              <td>
                <input type="text" v-model="prod.name" class="table-input" />
              </td>
              <td>
                <div class="price-container">
                  <input type="number" step="0.01" v-model="prod.amount" class="table-input amount-input" />
                  <span v-if="prod.split" class="split-preview">
                    ({{ (prod.amount / 2).toFixed(2) }})
                  </span>
                </div>
              </td>
              <td class="text-center">
                <input type="checkbox" v-model="prod.split" class="split-checkbox" />
              </td>
              <td>
                <select v-model="prod.category" class="table-input select-input">
                  <option v-for="cat in categories" :key="cat" :value="cat">
                    {{ getEmoji(cat) }} {{ cat }}
                  </option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <button class="submit-btn" @click="saveSelected">Zapisz wybrane wydatki +</button>
    </div>
  </div>
</template>

<style scoped>
.scanner-card {
  background: var(--accent-text);
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 650px;
  width: 100%;
  box-sizing: border-box;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.card-header h3 {
  margin: 0;
  font-size: 0.85rem;
  color: var(--accent);
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
}

.scan-buttons-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.upload-btn {
  background: var(--accent);
  color: var(--accent-text);
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.95rem;
  transition: opacity 0.2s ease, transform 0.1s ease;
  width: 100%;
}

.upload-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-gemini {
  background: var(--accent);
  border: 1px solid var(--accent);
}

.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--accent-bg);
  border-radius: 12px;
  border: 1px dashed var(--accent);
}

.loading-text {
  font-weight: 800;
  font-size: 1rem;
  margin: 12px 0 4px 0;
  color: var(--accent);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--accent-bg);
  border-top: 3px solid var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.metadata-box {
  background: var(--accent-bg);
  border-radius: 12px;
  padding: 12px 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 10px;
  text-align: left;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label {
  font-size: 0.7rem;
  color: var(--accent);
  opacity: 0.8;
  font-weight: 700;
  text-transform: uppercase;
}

.meta-value {
  font-size: 0.9rem;
  color: var(--accent);
  font-weight: 700;
}

.amount-meta {
  font-size: 1.1rem;
  font-weight: 800;
}

.table-wrapper {
  max-height: 350px;
  overflow-y: auto;
  border-radius: 8px;
}

.receipt-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.receipt-table th {
  padding: 8px;
  font-size: 0.75rem;
  color: var(--accent);
  opacity: 0.8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid var(--accent-bg);
}

.receipt-table td {
  padding: 6px 4px;
  vertical-align: middle;
}

.split-row {
  background: var(--accent-bg);
}

.table-input {
  background: var(--bg);
  color: var(--text-h);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 0.85rem;
  font-family: inherit;
  width: 100%;
  box-sizing: border-box;
  outline: none;
}

.table-input:focus {
  border-color: var(--accent);
}

.amount-input {
  font-weight: 800;
  color: var(--accent);
}

.select-input {
  cursor: pointer;
}

.price-container {
  display: flex;
  align-items: center;
  gap: 6px;
}

.split-preview {
  font-size: 0.75rem;
  color: var(--accent);
  font-weight: 800;
  white-space: nowrap;
}

.text-center {
  text-align: center;
}

.custom-checkbox,
.split-checkbox {
  cursor: pointer;
  accent-color: var(--accent);
  transform: scale(1.1);
}

.submit-btn {
  background-color: var(--accent);
  color: var(--accent-text);
  font-size: 1rem;
  font-weight: 800;
  border: none;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.2s ease, transform 0.1s ease;
  width: 100%;
}

.submit-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
</style>