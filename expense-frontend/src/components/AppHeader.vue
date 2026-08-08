<script setup>
defineProps(['showForm'])
const emit = defineEmits(['toggle-form', 'toggle-scanner'])
</script>

<template>
  <header class="header-content">
    <button @click="emit('toggle-form')" class="add-btn">Dodaj wydatek</button>
    <button @click="emit('toggle-scanner')" class="scan-btn">Skanuj paragon</button>
  </header>
</template>

<style scoped>
.header-content {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 20px 0;
  gap: 10px;
}
</style>