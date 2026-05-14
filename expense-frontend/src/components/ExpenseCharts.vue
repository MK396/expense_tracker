<script setup>
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import { 
  Chart as ChartJS, 
  ArcElement, 
  Tooltip, 
  Legend, 
  Title 
} from 'chart.js'


ChartJS.register(ArcElement, Tooltip, Legend, Title)

const props = defineProps({
  expenses: {
    type: Array,
    required: true,
    default: () => []
  }
})

const chartData = computed(() => {
  const categoriesMap = {}

  props.expenses.forEach(expense => {
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
    datasets: [
      {
        label: 'Suma wydatków (zł)',
        backgroundColor: [
          '#42b883', // Zielony Vue
          '#35495e', // Ciemny niebieski Vue
          '#ff7675', // Czerwony
          '#74b9ff', // Jasny niebieski
          '#a29bfe', // Fioletowy
          '#ffeaa7', // Żółty
          '#fab1a0'  // Brzoskwiniowy
        ],
        borderWidth: 2,
        borderColor: '#ffffff',
        data: Object.values(categoriesMap)
      }
    ]
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
        font: {
          size: 12
        }
      }
    },
    tooltip: {
      callbacks: {
        label: function(context) {
          const label = context.label || '';
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
    <div v-if="expenses.length > 0" class="canvas-wrapper">
      <Pie :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="no-data-placeholder">
      <p>Brak danych do wyświetlenia wykresu</p>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  background: white;
  padding: 25px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}

.canvas-wrapper {
  height: 350px;
  position: relative;
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

:global([data-theme='dark']) .chart-container {
  background: #2d2d2d;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

:global([data-theme='dark']) .no-data-placeholder {
  border-color: #444;
}
</style>