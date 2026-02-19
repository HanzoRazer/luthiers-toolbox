<template>
  <div class="display-container">
    <div class="expression">{{ expression || '\u00A0' }}</div>
    <div class="display">{{ display }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  expression: string
  display: string
}>()
</script>

<style scoped>
.display-container {
  background: #292a2d;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  min-height: 80px;
}

.expression {
  font-size: 14px;
  color: #9aa0a6;
  min-height: 20px;
  text-align: right;
  margin-bottom: 8px;
}

.display {
  font-size: 32px;
  font-weight: 300;
  text-align: right;
  color: #e8eaed;
  word-break: break-all;
}
</style>
