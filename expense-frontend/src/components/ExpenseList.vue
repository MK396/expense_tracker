<script setup>
// Definiujemy, że ten komponent oczekuje tablicy pod nazwą 'expenses'
defineProps(['expenses'])
</script>

<template>
  <table border="1">
    <thead>
      <tr>
        <th>Nazwa</th>
        <th>Kwota</th>
        <th>Kategoria</th>
        <th>Data</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="expense in expenses" :key="expense.id">
        <td>{{ expense.name }}</td>
        <td>{{ expense.amount }} zł</td>
        <td>{{ expense.category }}</td>
        <td>{{ expense.date }}</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
th, td {
  padding: 10px;
  text-align: left;
}
</style>