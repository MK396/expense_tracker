<script setup>
import { computed, ref } from 'vue'
import { Pie, Bar } from 'vue-chartjs'
import { 
  Chart as ChartJS, 
  ArcElement, 
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip, 
  Legend, 
  Title,
  PieController,
  BarController
} from 'chart.js'

ChartJS.register(
  ArcElement, 
  BarElement, 
  CategoryScale, 
  LinearScale, 
  Tooltip, 
  Legend, 
  Title,
  PieController,
  BarController
)

const props = defineProps({
  expenses: {
    type: Array,
    required: true,
    default: () => []
  }
})

const timeRange = defineModel('timeRange', { default: '30' })
const barChartGrouping = ref('date') 

// Funkcja pomocnicza do formatowania daty na DD-MM-YYYY
const formatDate = (rawDate) => {
  if (!rawDate) return ''
  const d = new Date(rawDate)
  if (isNaN(d.getTime())) return rawDate

  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()

  return `${day}-${month}-${year}`
}

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

const getCategoryEmojiOnly = (categoryName) => {
  return categoryEmojis[categoryName] || '🏷️'
}

const getCategoryColor = (categoryName) => {
  if (categoryColors[categoryName]) {
    return categoryColors[categoryName]
  }

  let hash = 0
  const name = categoryName || 'Inne'
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash) % 360
  return `hsl(${hue}, 65%, 75%)`
}

const getCategoryName = (category) => {
  if (!category) return 'Inne'
  return typeof category === 'object' ? (category.name || 'Inne') : category
}

const filteredExpenses = computed(() => {
  if (timeRange.value === 'all') {
    return props.expenses
  }
  
  const now = new Date()
  return props.expenses.filter(expense => {
    const expDate = new Date(expense.date)
    const diffTime = Math.abs(now - expDate)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    return diffDays <= parseInt(timeRange.value)
  })
})

const pieChartData = computed(() => {
  const categoriesMap = {}

  filteredExpenses.value.forEach(expense => {
    const category = getCategoryName(expense.category)
    const amount = parseFloat(expense.amount) || 0
    
    if (categoriesMap[category]) {
      categoriesMap[category] += amount
    } else {
      categoriesMap[category] = amount
    }
  })

  const labels = Object.keys(categoriesMap)
  const backgroundColors = labels.map(getCategoryColor)

  return {
    labels: labels, 
    datasets: [{
      label: 'Suma wydatków (zł)',
      backgroundColor: backgroundColors,
      borderWidth: 2,
      borderColor: '#ffffff',
      data: Object.values(categoriesMap)
    }]
  }
})

const barChartData = computed(() => {
  const groupedData = {}
  
  filteredExpenses.value.forEach(expense => {
    const expDate = new Date(expense.date)
    const amount = parseFloat(expense.amount) || 0
    let key = ''
    let displayKey = ''
    let sortKey = 0

    if (barChartGrouping.value === 'date') {
      key = expense.date 
      displayKey = formatDate(expense.date) // <-- Formatowanie daty na DD-MM-YYYY
      sortKey = key 
    } 
    else if (barChartGrouping.value === 'dayOfWeek') {
      const days = ['Niedziela', 'Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota']
      const dayIndex = expDate.getDay()
      key = days[dayIndex]
      displayKey = key
      sortKey = dayIndex === 0 ? 7 : dayIndex 
    } 
    else if (barChartGrouping.value === 'month') {
      const months = ['Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec', 'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień']
      const monthIndex = expDate.getMonth()
      const year = expDate.getFullYear()
      key = `${months[monthIndex]} ${year}`
      displayKey = key
      sortKey = (year * 100) + monthIndex 
    }

    if (!groupedData[key]) {
      groupedData[key] = { amount: 0, sortOrder: sortKey, label: displayKey }
    }
    groupedData[key].amount += amount
  })

  const sortedItems = Object.entries(groupedData).sort((a, b) => {
    if (a[1].sortOrder < b[1].sortOrder) return -1;
    if (a[1].sortOrder > b[1].sortOrder) return 1;
    return 0;
  })

  return {
    labels: sortedItems.map(item => item[1].label),
    datasets: [{
      label: 'Suma wydatków (zł)',
      backgroundColor: '#BDD9D7',
      borderRadius: 4,
      data: sortedItems.map(item => item[1].amount)
    }]
  }
})

const pieChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        usePointStyle: true,
        padding: 20,
        font: { size: 12 }
      }
    },
    tooltip: {
      callbacks: {
        label: function(context) {
          const categoryName = context.label || '';
          const emoji = getCategoryEmojiOnly(categoryName);
          const value = context.raw || 0;
          return ` ${emoji} : ${value.toFixed(2)} zł`;
        }
      }
    }
  }
}

// Opcje z wyłączoną legendą dla wykresu słupkowego
const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false // <-- UKRYCIE LEGENDRY POD WYKRESEM
    },
    tooltip: {
      callbacks: {
        label: function(context) {
          const value = context.raw || 0;
          return ` Suma: ${value.toFixed(2)} zł`;
        }
      }
    }
  }
}
</script>

<template>
  <div class="chart-container">
    <div v-if="props.expenses.length > 0" class="controls-wrapper">
      <div class="control-group">
        <label for="time-range">Zakres czasu (Ogólny):</label>
        <select id="time-range" v-model="timeRange" class="range-selector">
          <option value="7">Ostatnie 7 dni</option>
          <option value="30">Ostatnie 30 dni</option>
          <option value="365">Ostatni rok</option>
          <option value="all">Wszystko</option>
        </select>
      </div>

      <div class="control-group">
        <label for="bar-grouping">Grupuj wykres słupkowy po:</label>
        <select id="bar-grouping" v-model="barChartGrouping" class="range-selector">
          <option value="date">Konkretnych dniach</option>
          <option value="dayOfWeek">Dniach tygodnia</option>
          <option value="month">Miesiącach</option>
        </select>
      </div>
    </div>

    <div v-if="filteredExpenses.length > 0" class="charts-grid">
      <div class="canvas-wrapper">
        <h4 class="chart-title">Podział na kategorie</h4>
        <div class="chart-area">
          <Pie :data="pieChartData" :options="pieChartOptions" />
        </div>
      </div>
      
      <div class="canvas-wrapper">
        <h4 class="chart-title">Wydatki w czasie</h4>
        <div class="chart-area">
          <Bar :data="barChartData" :options="barChartOptions" />
        </div>
      </div>
    </div>
    
    <div v-else-if="props.expenses.length > 0" class="no-data-placeholder">
      <p>Brak wydatków w wybranym okresie czasu.</p>
    </div>

    <div v-else class="no-data-placeholder">
      <p>Brak danych. Dodaj pierwszy wydatek!</p>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  padding: 25px;
  border-radius: 16px;
  box-shadow: var(--shadow);
  margin-bottom: 40px; 
}

.controls-wrapper {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 15px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-group label {
  font-size: 14px;
  color: var(--accent);
  font-weight: 500;
}

.range-selector {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background-color: var(--bg);
  color: var(--text-h); 
  font-family: inherit;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s;
}

.range-selector:focus {
  border-color: var(--accent);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 400px), 1fr));
  gap: 30px;
  width: 100%;
}

.canvas-wrapper {
  display: flex;
  flex-direction: column;
  min-width: 0;
  width: 100%;
  gap: 10px; 
}

.chart-area {
  position: relative;
  height: 320px; 
  width: 100%;
}

.chart-title {
  text-align: center;
  color: var(--accent);
  margin-bottom: 10px;
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.85rem;
  letter-spacing: 0.05em;
}

.no-data-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  font-style: italic;
  border: 2px dashed var(--accent);
  border-radius: 12px;
}

@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  .controls-wrapper {
    justify-content: flex-start;
  }
}
</style>