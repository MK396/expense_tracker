<script setup>
import { computed } from 'vue';


const props = defineProps({
  expenses: {
    type: Array,
    required: true
  }
});


const totalAmount = computed(() => {
  return props.expenses
    .reduce((sum, item) => sum + Number(item.amount || item.kwota || 0), 0)
    .toLocaleString('pl-PL', { minimumFractionDigits: 2 });
});


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

</style>