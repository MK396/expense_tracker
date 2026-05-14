<script setup>
defineProps(['expenses'])
</script>

<template>
  <div class="expenses-container">
    <div v-for="expense in expenses" :key="expense.id" class="expense-card">
      <div class="card-header">
        <span class="expense-name">{{ expense.name }}</span>
        <span class="expense-amount">{{ expense.amount }} zł</span>
      </div>
      
      <div class="card-body">
        <span class="expense-category">{{ expense.category }}</span>
        <span class="expense-date">{{ expense.date }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.expenses-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  padding: 20px 0;
}

.expense-card {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}

.expense-card:hover {
  transform: translateY(-5px);
  border-color: #42b883;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.expense-name {
  font-weight: bold;
  font-size: 1.1rem;
  text-transform: capitalize;
}

.expense-amount {
  color: #2c3e50;
  font-weight: 800;
}

.card-body {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #666;
}

.expense-category {
  background: #f0f0f0;
  border-radius: 4px;
  text-transform: capitalize;
}
</style>