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
  Title 
} from 'chart.js'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title)

const props = defineProps({
  expenses: {
    type: Array,
    required: true,
    default: () => []
  }
})

// Przełączniki stanu
const timeRange = ref('30')          // Filtr zakresu czasu dla obu wykresów
const barChartGrouping = ref('date') // Sposób grupowania na wykresie słupkowym

// Filtrujemy wydatki na podstawie wybranego czasu dla obu wykresów
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

// Wykres kołowy pobiera dane przefiltrowane
const pieChartData = computed(() => {
  const categoriesMap = {}

  filteredExpenses.value.forEach(expense => {
    const category = expense.category || 'Inne'
    const amount = parseFloat(expense.amount) || 0
    
    if (categoriesMap[category]) {
      categoriesMap[category] += amount
    } else {
      categoriesMap[category] = amount
    }
  })

  return {
    labels: Object.keys(categoriesMap),
    datasets: [{
      label: 'Suma wydatków (zł)',
      backgroundColor: ['#42b883', '#35495e', '#ff7675', '#74b9ff', '#a29bfe', '#ffeaa7', '#fab1a0'],
      borderWidth: 2,
      borderColor: '#ffffff',
      data: Object.values(categoriesMap)
    }]
  }
})

// Wykres słupkowy - grupuje dane w zależności od wyboru użytkownika
const barChartData = computed(() => {
  const groupedData = {}
  
  filteredExpenses.value.forEach(expense => {
    const expDate = new Date(expense.date)
    const amount = parseFloat(expense.amount) || 0
    let key = ''
    let sortKey = 0

    if (barChartGrouping.value === 'date') {
      // Grupowanie dzień po dniu (YYYY-MM-DD)
      key = expense.date 
      sortKey = key // sortowanie alfabetyczne po dacie zadziała
    } 
    else if (barChartGrouping.value === 'dayOfWeek') {
      // Grupowanie po dniach tygodnia
      const days = ['Niedziela', 'Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota']
      const dayIndex = expDate.getDay()
      key = days[dayIndex]
      // Poniedziałek jako pierwszy dzień tygodnia (w Polsce) do sortowania
      sortKey = dayIndex === 0 ? 7 : dayIndex 
    } 
    else if (barChartGrouping.value === 'month') {
      // Grupowanie miesiącami (np. "Lipiec 2026")
      const months = ['Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec', 'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień']
      const monthIndex = expDate.getMonth()
      const year = expDate.getFullYear()
      key = `${months[monthIndex]} ${year}`
      // Matematyczny klucz do sortowania chronologicznego (np. 202606)
      sortKey = (year * 100) + monthIndex 
    }

    // Dodawanie wartości do odpowiedniej grupy
    if (!groupedData[key]) {
      groupedData[key] = { amount: 0, sortOrder: sortKey }
    }
    groupedData[key].amount += amount
  })

  // Sortowanie wygenerowanych kluczy
  const sortedItems = Object.entries(groupedData).sort((a, b) => {
    if (a[1].sortOrder < b[1].sortOrder) return -1;
    if (a[1].sortOrder > b[1].sortOrder) return 1;
    return 0;
  })

  return {
    labels: sortedItems.map(item => item[0]),
    datasets: [{
      label: 'Suma wydatków (zł)',
      backgroundColor: '#42b883',
      borderRadius: 4,
      data: sortedItems.map(item => item[1].amount)
    }]
  }
})

const chartOptions = {
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
          const label = context.dataset.label || context.label || '';
          const value = context.raw || 0;
          return ` ${label}: ${value.toFixed(2)} zł`;
        }
      }
    }
  }
}
</script>

<template>
  <div class="chart-container">
    
    <!-- Paski z filtrami widoczne, jeśli są dane -->
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

    <!-- Wykresy -->
    <div v-if="filteredExpenses.length > 0" class="charts-grid">
      <div class="canvas-wrapper">
        <h4 class="chart-title">Podział na kategorie</h4>
        <!-- Nowy kontener trzymający w ryzach sam wykres -->
        <div class="chart-area">
          <Pie :data="pieChartData" :options="chartOptions" />
        </div>
      </div>
      
      <div class="canvas-wrapper">
        <h4 class="chart-title">Wydatki w czasie</h4>
        <!-- Nowy kontener trzymający w ryzach sam wykres -->
        <div class="chart-area">
          <Bar :data="barChartData" :options="chartOptions" />
        </div>
      </div>
    </div>
    
    <!-- Komunikaty o braku danych -->
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
  background: white;
  padding: 25px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  margin-bottom: 40px; /* Zmień tę wartość z 20px na 40px */
}

.controls-wrapper {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-group label {
  font-size: 14px;
  color: #555;
  font-weight: 500;
}

.range-selector {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f8f9fa;
  color: #333; /* <-- Ta linijka naprawia problem z widocznością tekstu */
  font-family: inherit;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s;
}

.range-selector:focus {
  border-color: #42b883;
}

.charts-grid {
  display: grid;
  /* Automatycznie zawija do 1 kolumny, gdy brakuje miejsca (mniej niż 400px na wykres) */
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 400px), 1fr));
  gap: 30px;
  width: 100%;
}

.canvas-wrapper {
  display: flex;
  flex-direction: column;
  min-width: 0;
  width: 100%;
  gap: 10px; /* Dodaje lekki odstęp między tytułem a wykresem */
}

.chart-area {
  position: relative;
  height: 320px; /* Definiujemy sztywną wysokość tylko dla samego wykresu */
  width: 100%;
}

@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  .controls-wrapper {
    justify-content: flex-start;
  }
}

.chart-title {
  text-align: center;
  color: #333;
  margin-bottom: 10px;
  font-weight: 600;
}

.no-data-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-style: italic;
  border: 2px dashed #eee;
  border-radius: 12px;
}

/* Tryb ciemny */
:global([data-theme='dark']) .chart-container {
  background: #2d2d2d;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

:global([data-theme='dark']) .controls-wrapper {
  border-bottom-color: #444;
}

:global([data-theme='dark']) .no-data-placeholder {
  border-color: #444;
}

:global([data-theme='dark']) .chart-title,
:global([data-theme='dark']) .control-group label {
  color: #eee;
}

:global([data-theme='dark']) .range-selector {
  background: #444;
  color: white;
  border-color: #555;
}
</style>