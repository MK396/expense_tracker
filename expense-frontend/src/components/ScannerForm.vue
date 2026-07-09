<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const emit = defineEmits(['expenses-added'])

const fileInput = ref(null)
const isLoading = ref(false)
const products = ref([])
const categories = ref([])

// Nowy stan informujący o aktywnym skanerze
const currentStatusMessage = ref('')

// STANY NA METADANE
const shopName = ref('')
const shopNip = ref('')
const totalSum = ref('') 
const usedModel = ref('') // przechowuje model zwrócony z API

// STAN NA WYBÓR SKANERA (EasyOCR vs Gemini)
const selectedEndpoint = ref('/api/scan/') 

onMounted(async () => {
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/categories/')
    categories.value = data.map(c => c.name)
  } catch (e) {
    console.error("Błąd pobierania kategorii", e)
  }
})

const triggerScan = (endpoint) => {
  selectedEndpoint.value = endpoint
  if (endpoint.includes('gemini')) {
    currentStatusMessage.value = 'Inicjalizacja Gemini AI... Sprawdzanie dostępności modeli.'
  } else {
    currentStatusMessage.value = 'Przetwarzanie lokalne (EasyOCR)...'
  }
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

  // Jeśli wybrano Gemini, dajemy znać użytkownikowi, że wysyłamy plik
  if (selectedEndpoint.value.includes('gemini')) {
    currentStatusMessage.value = 'Wysyłanie obrazu do chmury i analiza dokumentu...'
  }

  try {
    const { data } = await axios.post(`http://127.0.0.1:8000${selectedEndpoint.value}`, formData)
    
    if (data.status === 'success') {
      const scanResult = data.produkty
      
      shopName.value = scanResult.sklep
      shopNip.value = scanResult.nip
      totalSum.value = scanResult.suma_calkowita 
      if (data.model) usedModel.value = data.model

      products.value = scanResult.produkty.map(p => ({
        ...p,
        selected: true,
        category: categories.value.length > 0 ? categories.value[0] : ''
      }))
    }
  } catch (error) {
    alert("Wystąpił błąd podczas analizy paragonu.")
    console.error(error)
  } finally {
    isLoading.value = false
    currentStatusMessage.value = ''
    if (fileInput.value) fileInput.value.value = ''
  }
}

const saveSelected = async () => {
  const selectedProducts = products.value.filter(p => p.selected)

  if (selectedProducts.length === 0) {
    return alert("Wybierz przynajmniej jeden produkt.")
  }

  const groupedExpenses = {}

  selectedProducts.forEach(p => {
    const cat = p.category
    if (!groupedExpenses[cat]) {
      groupedExpenses[cat] = {
        name: shopName.value, // Usunięto doklejanie " - ${cat}" z nazwy głównej
        amount: 0,
        category: cat,
        date: new Date().toISOString().split('T')[0],
        details: []
      }
    }
    
    groupedExpenses[cat].amount += parseFloat(p.amount)
    
    groupedExpenses[cat].details.push({
      name: p.name,
      amount: parseFloat(p.amount)
    })
  })

  const toSave = Object.values(groupedExpenses).map(expense => ({
    ...expense,
    amount: parseFloat(expense.amount.toFixed(2))
  }))

  try {
    await axios.post('http://127.0.0.1:8000/api/expenses/', toSave)
    emit('expenses-added')
  } catch (e) {
    alert("Błąd zapisu. Upewnij się, że wybrane kategorie istnieją w bazie danych.")
    console.error(e)
  }
}
</script>

<template>
  <div class="scanner-container">
    <h2>Skaner Paragonów</h2>
    
    <!-- Jeśli trwa ładowanie, ukrywamy przyciski i pokazujemy jeden czysty status -->
    <div v-if="isLoading" class="loading-box">
      <div class="spinner"></div>
      <p class="loading-text">Analizowanie...</p>
      <p class="sub-loading-text">{{ currentStatusMessage }}</p>
    </div>

    <div v-else class="upload-section">
      <input type="file" ref="fileInput" accept="image/*" style="display: none" @change="handleFileUpload" />
      
      <!-- Przycisk 1: EasyOCR -->
      <button class="upload-btn" @click="triggerScan('/api/scan/')">
        Skanuj (EasyOCR - Lokalnie)
      </button>

      <!-- Przycisk 2: Gemini AI -->
      <button class="upload-btn btn-gemini" @click="triggerScan('/api/scan-gemini/')">
        Skanuj (Gemini AI - Chmura)
      </button>
    </div>

    <div v-if="products.length > 0" class="results-section">
      <div class="metadata-box">
        <p><strong>Sklep:</strong> {{ shopName }}</p>
        <p><strong>NIP:</strong> {{ shopNip }}</p>
        <p><strong>Łączna suma:</strong> {{ totalSum }}</p>
        <p v-if="usedModel" class="model-badge"><strong>Użyty model:</strong> {{ usedModel }}</p>
      </div>

      <table class="receipt-table">
        <thead>
          <tr>
            <th>+</th>
            <th>Produkt</th>
            <th>Cena</th>
            <th>Kategoria</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(prod, idx) in products" :key="idx">
            <td><input type="checkbox" v-model="prod.selected" /></td>
            <td><input type="text" v-model="prod.name" class="table-input" /></td>
            <td><input type="number" step="0.01" v-model="prod.amount" class="table-input amount-input" /></td>
            <td>
              <select v-model="prod.category" class="table-input">
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
      
      <button class="submit-btn" @click="saveSelected">Zapisz wybrane wydatki</button>
    </div>
  </div>
</template>

<style scoped>
.scanner-container {
  background: var(--code-bg); 
  padding: 20px; 
  border-radius: 12px; 
  max-width: 600px;
  max-height: 85vh; 
  overflow-y: auto; 
}

.scanner-container::-webkit-scrollbar {
  width: 8px;
}
.scanner-container::-webkit-scrollbar-track {
  background: transparent;
}
.scanner-container::-webkit-scrollbar-thumb {
  background-color: #aa3bff; 
  border-radius: 10px;
}

/* Style sekcji ładowania */
.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 10px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
  border: 1px dashed var(--border);
}

.loading-text {
  font-weight: bold;
  font-size: 1.2rem;
  margin: 10px 0 5px 0;
  color: var(--text-h);
}

.sub-loading-text {
  font-size: 0.9rem;
  color: #666;
  text-align: center;
  font-style: italic;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.upload-btn {
  background: var(--accent); color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%;
}

.btn-gemini {
  background: #2563eb; 
  margin-top: 10px;
}
.btn-gemini:hover {
  background: #1d4ed8;
}

.results-section { margin-top: 20px; }

.metadata-box {
  background: var(--bg);
  border-left: 4px solid var(--accent);
  padding: 10px 15px;
  margin-bottom: 15px;
  border-radius: 4px;
}
.metadata-box p {
  margin: 5px 0;
  color: var(--text);
  font-size: 0.95em;
}

.model-badge {
  font-size: 0.85rem;
  color: #2563eb !important;
}

.receipt-table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
.receipt-table th { text-align: left; padding-bottom: 10px; font-size: 0.9em; color: var(--text); }
.receipt-table td { padding: 5px 0; }
.table-input { background: var(--bg); color: var(--text-h); border: 1px solid var(--border); border-radius: 4px; padding: 5px; width: 90%; }
.amount-input { width: 70px; }
.submit-btn { background: #42b883; color: white; border: none; padding: 12px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold; }
</style>