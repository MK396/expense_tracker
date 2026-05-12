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

<script setup>
import { computed } from 'vue';

// Definiujemy propsy - komponent będzie oczekiwał tablicy 'expenses'
const props = defineProps({
  expenses: {
    type: Array,
    required: true
  }
});

// Logika obliczania sumy całkowitej
const totalAmount = computed(() => {
  return props.expenses
    .reduce((sum, item) => sum + Number(item.amount || item.kwota || 0), 0)
    .toLocaleString('pl-PL', { minimumFractionDigits: 2 });
});

// Logika obliczania wydatków z obecnego miesiąca
const monthlyAmount = computed(() => {
  const now = new Date();
  const currentMonth = now.getMonth();
  const currentYear = now.getFullYear();

  const total = props.expenses
    .filter(item => {
      const d = new Date(item.date || item.data);
      return d.getMonth() === currentMonth && d.getFullYear() === currentYear;
    })
    .reduce((sum, item) => sum + Number(item.amount || item.kwota || 0), 0);

  return total.toLocaleString('pl-PL', { minimumFractionDigits: 2 });
});
</script>

<style scoped>
.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.card {
  background: white; /* Jeśli masz dark mode, zmień na zmienną lub ciemny kolor */
  padding: 1.5rem;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border-left: 6px solid #a855f7; /* Kolor fioletowy z Twojego przycisku */
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-5px);
}

.card-icon {
  font-size: 2rem;
  background: #f3e8ff;
  padding: 10px;
  border-radius: 12px;
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

/* Dostosowanie pod Dark Mode (opcjonalnie) */
@media (prefers-color-scheme: dark) {
  .card {
    background: #1f2937;
    border-left-color: #a855f7;
  }
  .card-info h3 { color: #9ca3af; }
  .card-info p { color: #f9fafb; }
  .card-icon { background: #374151; }
}
</style>