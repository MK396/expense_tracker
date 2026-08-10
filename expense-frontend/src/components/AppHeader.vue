<script setup>
import { computed } from 'vue'

const props = defineProps({
  showForm: Boolean,
  expenses: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['toggle-form', 'toggle-scanner', 'toggle-theme'])

const selectedMonth = defineModel('selectedMonth', { default: new Date().getMonth() })
const selectedYear = defineModel('selectedYear', { default: new Date().getFullYear() })

const monthNames = [
  'Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec',
  'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień'
]

const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = new Set(
    props.expenses.map(item => new Date(item.date || item.data).getFullYear())
  )
  years.add(currentYear)
  return Array.from(years).sort((a, b) => b - a)
})
</script>

<template>
  <header class="header-content">
    <div class="filters-container">
      <select v-model="selectedMonth" class="filter-select">
        <option v-for="(name, index) in monthNames" :key="index" :value="index">
          {{ name }}
        </option>
      </select>

      <select v-model="selectedYear" class="filter-select">
        <option v-for="year in availableYears" :key="year" :value="year">
          {{ year }}
        </option>
      </select>
    </div>

    <div class="actions-container">
      <button @click="emit('toggle-form')" class="add-btn">Dodaj wydatek</button>
      <button @click="emit('toggle-scanner')" class="scan-btn">Skanuj paragon</button>
    </div>
  </header>
</template>

<style scoped>
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  gap: 15px;
}

.filters-container,
.actions-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--border, #ccc);
  border-radius: 8px;
  background-color: var(--accent-text, #fff);
  color: var(--accent, #333);
  font-weight: 600;
  font-size: 0.9rem;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s;
}

.filter-select:focus {
  border-color: var(--accent);
}

@media (max-width: 600px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filters-container,
  .actions-container {
    justify-content: space-between;
  }
}
</style>