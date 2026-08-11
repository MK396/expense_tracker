<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  expenses: {
    type: Array,
    required: true
  },
  selectedMonth: {
    type: Number,
    default: () => new Date().getMonth()
  },
  selectedYear: {
    type: Number,
    default: () => new Date().getFullYear()
  }
});

// POBIERANIE ZAPISANEGO LIMITU Z LOCALSTORAGE LUB WARTOŚĆ DOMYŚLNA 2000 ZŁ
const savedLimit = localStorage.getItem('user_monthly_limit');
const monthlyLimit = ref(savedLimit ? Number(savedLimit) : 2000);

// STANY DLA EDYCJI LIMITU
const isEditingLimit = ref(false);
const tempLimit = ref(monthlyLimit.value);

const startEditingLimit = () => {
  tempLimit.value = monthlyLimit.value;
  isEditingLimit.value = true;
};

const saveLimit = () => {
  const val = Number(tempLimit.value);
  if (!isNaN(val) && val > 0) {
    monthlyLimit.value = val;
    localStorage.setItem('user_monthly_limit', val);
  }
  isEditingLimit.value = false;
};

const now = new Date();

// Wydatki dla wybranego miesiąca
const filteredMonthlyExpenses = computed(() => {
  return props.expenses.filter(item => {
    const d = new Date(item.date || item.data);
    return (
      d.getMonth() === Number(props.selectedMonth) &&
      d.getFullYear() === Number(props.selectedYear)
    );
  });
});

// Suma w wybranym miesiącu
const monthlyAmountRaw = computed(() => {
  return filteredMonthlyExpenses.value
    .reduce((sum, item) => sum + Number(item.amount || item.kwota || 0), 0);
});

const monthlyAmount = computed(() => {
  return monthlyAmountRaw.value.toLocaleString('pl-PL', { minimumFractionDigits: 2 });
});

// Pozostały budżet
const remainingBudget = computed(() => {
  const remaining = monthlyLimit.value - monthlyAmountRaw.value;
  return remaining.toLocaleString('pl-PL', { minimumFractionDigits: 2 });
});

// Liczba dni w miesiącu oraz minione dni
const daysInMonth = computed(() => {
  return new Date(props.selectedYear, Number(props.selectedMonth) + 1, 0).getDate();
});

const elapsedDays = computed(() => {
  const isCurrentMonth = 
    Number(props.selectedYear) === now.getFullYear() && 
    Number(props.selectedMonth) === now.getMonth();
    
  return isCurrentMonth ? now.getDate() : daysInMonth.value;
});

// Średnia dzienna
const dailyAverageRaw = computed(() => {
  return monthlyAmountRaw.value / (elapsedDays.value || 1);
});

const dailyAverage = computed(() => {
  return dailyAverageRaw.value.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
});

// Prognoza na koniec miesiąca (raw numeryczna)
const forecastAmountRaw = computed(() => {
  return dailyAverageRaw.value * daysInMonth.value;
});

const forecastAmount = computed(() => {
  return forecastAmountRaw.value.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
});

// Największy wydatek
const topExpense = computed(() => {
  if (filteredMonthlyExpenses.value.length === 0) return null;
  return [...filteredMonthlyExpenses.value].sort((a, b) => 
    Number(b.amount || b.kwota || 0) - Number(a.amount || a.kwota || 0)
  )[0];
});

const budgetPercentage = computed(() => {
  const percentage = (monthlyAmountRaw.value / monthlyLimit.value) * 100;
  return percentage.toFixed(1);
});

const barWidth = computed(() => {
  const percentage = (monthlyAmountRaw.value / monthlyLimit.value) * 100;
  return Math.min(percentage, 100);
});

// Stany koloru paska postępu
const isWarning = computed(() => {
  const pct = (monthlyAmountRaw.value / monthlyLimit.value) * 100;
  return pct >= 75 && pct < 100;
});

const isDanger = computed(() => {
  return (monthlyAmountRaw.value / monthlyLimit.value) * 100 >= 100;
});

// Stany koloru tekstu prognozy
const isForecastWarning = computed(() => {
  const pct = (forecastAmountRaw.value / monthlyLimit.value) * 100;
  return pct >= 75 && pct < 100;
});

const isForecastDanger = computed(() => {
  return (forecastAmountRaw.value / monthlyLimit.value) * 100 >= 100;
});
</script>

<template>
  <div class="stats-container">
    <!-- KARTA 1: ŚREDNIA DZIENNA I PROGNOZA NA KONIEC MIESIĄCA -->
    <div class="card">
      <div class="card-info">
        <div class="card-split">
          <div class="split-col">
            <h3>Średnio dziennie</h3>
            <p>{{ dailyAverage }} zł</p>
          </div>
          <div class="split-col">
            <h3>Prognoza</h3>
            <p :class="{ 'text-warning': isForecastWarning, 'text-danger': isForecastDanger }">
              {{ forecastAmount }} zł
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- KARTA 2: WYDATKI MIESIĘCZNE I POZOSTAŁY BUDŻET -->
    <div class="card">
      <div class="card-info">
        <div class="card-split">
          <div class="split-col">
            <h3>W tym miesiącu</h3>
            <p>{{ monthlyAmount }} zł</p>
          </div>
          <div class="split-col">
            <h3>Pozostało</h3>
            <p>{{ remainingBudget }} zł</p>
          </div>
        </div>

        <div class="budget-container">
          <div class="budget-info">
            <!-- EDITABLE LIMIT -->
            <span v-if="isEditingLimit" class="limit-edit-box">
              Limit: 
              <input 
                v-model="tempLimit" 
                type="number" 
                class="limit-input" 
                @keyup.enter="saveLimit"
                @blur="saveLimit"
                autofocus
              /> zł
            </span>

            <span v-else class="limit-clickable" @click="startEditingLimit" title="Kliknij, aby zmienić limit">
              Limit: {{ monthlyLimit }} zł ✏️
            </span>

            <span>{{ budgetPercentage }}%</span>
          </div>
          <div class="progress-bar-bg">
            <div 
              class="progress-bar-fill" 
              :class="{ 'warning-mode': isWarning, 'danger-mode': isDanger }"
              :style="{ width: barWidth + '%' }"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- KARTA 3: NAJWIĘKSZY WYDATEK -->
    <div class="card">
      <div class="card-info">
        <h3>Największy wydatek</h3>
        <p v-if="topExpense">
          {{ Number(topExpense.amount || topExpense.kwota || 0).toLocaleString('pl-PL', { minimumFractionDigits: 2 }) }} zł
        </p>
        <p v-else>-</p>
        <small v-if="topExpense" class="top-expense-title">
          {{ topExpense.title || topExpense.nazwa || topExpense.category }}
        </small>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.card {
  background: var(--accent-text);
  padding: 1.5rem;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.2s ease;
  box-shadow: var(--shadow);
}

.card:hover {
  transform: translateY(-5px);
}

.card-info {
  flex: 1;
  min-width: 0;
}

.card-split {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  text-align: center;
}

.split-col {
  flex: 1;
}

.split-col:first-child {
  border-right: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  padding-right: 1rem;
}

.card-info h3 {
  margin: 0;
  font-size: 0.8rem;
  color: var(--accent);
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
}

.card-info p {
  margin: 4px 0 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--accent);
  transition: color 0.3s ease;
}

/* Kolory tekstu prognozy */
.text-warning {
  color: #f97316 !important;
}

.text-danger {
  color: #ef4444 !important;
}

.top-expense-title {
  display: block;
  margin-top: 4px;
  font-size: 0.85rem;
  color: var(--accent);
  opacity: 0.75;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.budget-container {
  margin-top: 12px;
  width: 100%;
}

.budget-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--accent);
  font-weight: 600;
  margin-bottom: 5px;
}

.limit-clickable {
  cursor: pointer;
  transition: opacity 0.2s;
}

.limit-clickable:hover {
  opacity: 0.7;
}

.limit-edit-box {
  display: flex;
  align-items: center;
  gap: 4px;
}

.limit-input {
  width: 70px;
  background: var(--bg, #fff);
  color: var(--accent, #333);
  border: 1px solid var(--accent);
  border-radius: 4px;
  padding: 1px 4px;
  font-size: 0.75rem;
  font-weight: bold;
  outline: none;
}

.progress-bar-bg {
  height: 8px;
  width: 100%;
  background: var(--accent-bg);
  border-radius: 10px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 10px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.3s ease;
}

.progress-bar-fill.warning-mode {
  background: #f97316; 
}

.progress-bar-fill.danger-mode {
  background: #ef4444; 
}
</style>