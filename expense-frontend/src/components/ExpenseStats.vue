<script setup>
import { computed } from 'vue';

const props = defineProps({
  expenses: {
    type: Array,
    required: true
  }
});

// --- SUMA CAŁKOWITA ---
const totalAmount = computed(() => {
  return props.expenses
    .reduce((sum, item) => sum + Number(item.amount || item.kwota || 0), 0)
    .toLocaleString('pl-PL', { minimumFractionDigits: 2 });
});

// --- LOGIKA BUDŻETU I BIEŻĄCEGO MIESIĄCA ---
const monthlyLimit = 2000;

// 1. Zmienna z surową wartością liczbową (potrzebna do wyliczenia procentów)
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

// 2. Zmienna z ładnym polskim formatowaniem (do wyświetlenia na ekranie)
const monthlyAmount = computed(() => {
  return monthlyAmountRaw.value.toLocaleString('pl-PL', { minimumFractionDigits: 2 });
});

// 3. Obliczenie zapełnienia paska (max 100%)
const budgetPercentage = computed(() => {
  const percentage = (monthlyAmountRaw.value / monthlyLimit) * 100;
  return Math.min(percentage, 100).toFixed(1);
});

// 4. Sprawdzenie, czy wydatki przekraczają 80% limitu
const isOverBudget = computed(() => {
  return (monthlyAmountRaw.value / monthlyLimit) * 100 > 80;
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

    <!-- KAFELEK Z PASKIEM POSTĘPU -->
    <div class="card">
      <div class="card-icon">📅</div>
      <div class="card-info">
        <h3>W tym miesiącu</h3>
        <p>{{ monthlyAmount }} zł</p>

        <!-- Pasek budżetu -->
        <div class="budget-container">
          <div class="budget-info">
            <span>Limit: {{ monthlyLimit }} zł</span>
            <span>{{ budgetPercentage }}%</span>
          </div>
          <div class="progress-bar-bg">
            <div 
              class="progress-bar-fill" 
              :class="{ 'danger-mode': isOverBudget }"
              :style="{ width: budgetPercentage + '%' }"
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
  background: rgb(182, 182, 182);
  padding: 1.5rem;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.2s;
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
  flex: 1; /* Pozwala sekcji informacyjnej zająć całą resztę miejsca (wymagane dla paska!) */
  min-width: 0;
}

.card-info h3 {
  margin: 0;
  font-size: 0.8rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.card-info p {
  margin: 4px 0 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: #1f2937;
}

/* --- STYLE DLA PASKA BUDŻETU --- */
.budget-container {
  margin-top: 10px;
  width: 100%;
}

.budget-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #4b5563; /* Ciemniejszy szary dla czytelności */
  font-weight: 600;
  margin-bottom: 5px;
}

.progress-bar-bg {
  height: 8px;
  width: 100%;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 10px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: #10b981; /* Zielony */
  border-radius: 10px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.3s ease;
}

/* Zmienia kolor na czerwony, jeśli aktywuje się 'danger-mode' */
.progress-bar-fill.danger-mode {
  background: #ef4444; 
}
</style>