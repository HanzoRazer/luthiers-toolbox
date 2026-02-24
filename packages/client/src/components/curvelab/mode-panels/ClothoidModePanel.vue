<script setup lang="ts">
/**
 * ClothoidModePanel - Clothoid blend mode controls for CurveLab
 * Extracted from CurveLab.vue
 */
const emit = defineEmits<{
  'reset': []
  'blend': []
}>()
</script>

<template>
  <div class="params flex gap-3 items-center flex-wrap">
    <span class="text-sm text-gray-700">
      Pick: p0 (green) → t0 (tangent) → p1 (green) → t1 (tangent)
    </span>
    <button
      class="btn btn-normal"
      @click="emit('reset')"
    >
      Reset
    </button>
    <button
      class="btn btn-primary"
      @click="emit('blend')"
    >
      Blend
    </button>
  </div>
</template>

<style scoped>
.btn {
  border: 1px solid #e2e8f0;
  padding: 8px 16px;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn:hover {
  background: #f1f5f9;
}

.btn-normal {
  color: #475569;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border-color: #2563eb;
}

.btn-primary:hover {
  background: #2563eb;
}
</style>
