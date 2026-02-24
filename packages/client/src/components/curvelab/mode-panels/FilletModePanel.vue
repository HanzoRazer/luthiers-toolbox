<script setup lang="ts">
/**
 * FilletModePanel - Fillet mode controls for CurveLab
 * Extracted from CurveLab.vue
 */
defineProps<{
  filletR: number
}>()

const emit = defineEmits<{
  'update:filletR': [value: number]
  'apply': []
}>()
</script>

<template>
  <div class="params flex gap-3 items-center flex-wrap">
    <label class="param-label">
      Radius (mm)
      <input
        :value="filletR"
        type="number"
        class="param-input"
        step="0.5"
        min="0.1"
        @input="emit('update:filletR', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </label>
    <button
      class="btn btn-primary"
      @click="emit('apply')"
    >
      Apply Fillet
    </button>
  </div>
</template>

<style scoped>
.param-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #475569;
}

.param-input {
  border: 1px solid #cbd5e1;
  padding: 6px 10px;
  border-radius: 4px;
  width: 100px;
  font-size: 14px;
}

.btn {
  border: 1px solid #e2e8f0;
  padding: 8px 16px;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
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
