<script setup>
defineProps(['isDark', 'showForm'])
const emit = defineEmits(['toggle-theme', 'toggle-form'])
</script>

<template>
  <header class="header-content">
    <h1>Tracker Wydatków</h1>
    <div class="header-actions">
      <button @click="emit('toggle-form')" class="add-btn">Dodaj wydatek</button>
      <button class="scan-btn">Skanuj paragon</button>
      <button @click="emit('toggle-theme')" class="theme-toggle">{{ isDark ? '☀️' : '🌙' }}</button>
    </div>
  </header>
</template>

<style scoped>
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
}
.add-btn, .scan-btn, .theme-toggle {
  background-color: var(--accent);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  margin-right: 10px;
}
</style>