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
  },
  selectedMonth: {
    type: Number,
    default: () => new Date().getMonth()
  },
  selectedYear: {
    type: Number,
    default: () => new Date().getFullYear()
  }
})

const barChartGrouping = ref('month')

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

// 1. DANE FILTROWANE DLA WYKRESU KOŁOWEGO (Strictly wybrany miesiąc i rok)
const pieChartExpenses = computed(() => {
  return props.expenses.filter(expense => {
    const expDate = new Date(expense.date)
    return (
      expDate.getMonth() === Number(props.selectedMonth) &&
      expDate.getFullYear() === Number(props.selectedYear)
    )
  })
})

const pieChartData = computed(() => {
  const categoriesMap = {}

  pieChartExpenses.value.forEach(expense => {
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

// 2. DANE FILTROWANE DLA WYKRESU SŁUPKOWEGO (Zależne od barChartGrouping)
const barChartExpenses = computed(() => {
  return props.expenses.filter(expense => {
    const expDate = new Date(expense.date)

    if (barChartGrouping.value === 'month' || barChartGrouping.value === 'year') {
      return expDate.getFullYear() === Number(props.selectedYear)
    }

    return (
      expDate.getMonth() === Number(props.selectedMonth) &&
      expDate.getFullYear() === Number(props.selectedYear)
    )
  })
})

const barChartData = computed(() => {
  const groupedData = {}
  
  barChartExpenses.value.forEach(expense => {
    const expDate = new Date(expense.date)
    const amount = parseFloat(expense.amount) || 0
    let key = ''
    let displayKey = ''
    let sortKey = 0

    if (barChartGrouping.value === 'dayOfWeek') {
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
    else if (barChartGrouping.value === 'year') {
      const year = expDate.getFullYear()
      key = `${year}`
      displayKey = key
      sortKey = year 
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
      position: 'left',
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

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
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
        <label for="bar-grouping">Grupuj wykres słupkowy po:</label>
        <select id="bar-grouping" v-model="barChartGrouping" class="range-selector">
          <option value="dayOfWeek">Dniach tygodnia</option>
          <option value="month">Miesiącach</option>
          <option value="year">Roku</option>
        </select>
      </div>
    </div>

    <div v-if="barChartExpenses.length > 0 || pieChartExpenses.length > 0" class="charts-grid">
      <div class="canvas-wrapper">
        <div v-if="pieChartExpenses.length > 0" class="chart-area">
          <Pie :data="pieChartData" :options="pieChartOptions" />
        </div>
        <div v-else class="no-data-placeholder">
          <p>Brak wydatków w wybranym miesiącu.</p>
        </div>
      </div>
      
      <div class="canvas-wrapper">
        <div v-if="barChartExpenses.length > 0" class="chart-area">
          <Bar :data="barChartData" :options="barChartOptions" />
        </div>
        <div v-else class="no-data-placeholder">
          <p>Brak danych dla wykresu słupkowego.</p>
        </div>
      </div>
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
  height: 420px; 
  width: 100%;
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