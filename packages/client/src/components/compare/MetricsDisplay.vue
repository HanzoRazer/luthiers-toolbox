<template>
  <div
    v-if="delta"
    class="metrics"
  >
    <h3>Delta Metrics</h3>
    <ul>
      <li>Time Δ: {{ delta.time?.toFixed(2) }} s</li>
      <li>Length Δ: {{ delta.length?.toFixed(2) }} mm</li>
      <li>Retracts Δ: {{ delta.retracts }}</li>
    </ul>
  </div>
</template>
<script setup lang="ts">
const props = defineProps<{ delta: any }>()
</script>
<style scoped>
.metrics { margin-top: 2rem; }
</style>
