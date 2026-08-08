<script setup>
import { computed } from 'vue';

const props = defineProps({
  expenses: {
    type: Array,
    required: true
  }
});

const monthlyLimit = 2000;

const totalAmount = computed(() => {
  return props.expenses
    .reduce((sum, item) => sum + Number(item.amount || item.kwota || 0), 0)
    .toLocaleString('pl-PL', { minimumFractionDigits: 2 });
});

const monthlyAmountRaw = computed(() => {
  const now = new Date();
  const currentMonth = now.getMonth();
  const currentYear = now.getFullYear();

  return props.expenses
    .filter(item => {
      const d = new Date(item.date || item.data);
      return d.getMonth() === currentMonth && d.getFullYear() === currentYear;
    })
    .reduce((sum, item) => sum + Number(item.amount || item.kwota || 0), 0);
});

const monthlyAmount = computed(() => {
  return monthlyAmountRaw.value.toLocaleString('pl-PL', { minimumFractionDigits: 2 });
});

const budgetPercentage = computed(() => {
  const percentage = (monthlyAmountRaw.value / monthlyLimit) * 100;
  return percentage.toFixed(1);
});

const barWidth = computed(() => {
  const percentage = (monthlyAmountRaw.value / monthlyLimit) * 100;
  return Math.min(percentage, 100);
});

const isWarning = computed(() => {
  const pct = (monthlyAmountRaw.value / monthlyLimit) * 100;
  return pct >= 75 && pct < 100;
});

const isDanger = computed(() => {
  return (monthlyAmountRaw.value / monthlyLimit) * 100 >= 100;
});
</script>

<template>
  <div class="stats-container">
    <div class="card">
      <div class="card-icon">💰</div>
      <div class="card-info">
        <h3>Suma całkowita</h3>
        <p>{{ totalAmount }} zł</p>
      </div>
    </div>

    <div class="card">
      <div class="card-icon">📅</div>
      <div class="card-info">
        <h3>W tym miesiącu</h3>
        <p>{{ monthlyAmount }} zł</p>

        <div class="budget-container">
          <div class="budget-info">
            <span>Limit: {{ monthlyLimit }} zł</span>
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

    <div class="card">
      <div class="card-icon">📊</div>
      <div class="card-info">
        <h3>Liczba wpisów</h3>
        <p>{{ expenses.length }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
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

.card-icon {
  font-size: 2rem;
  padding: 10px;
  border-radius: 12px;
}

.card-info {
  flex: 1;
  min-width: 0;
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
}

.budget-container {
  margin-top: 10px;
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