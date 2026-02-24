<script setup lang="ts">
/**
 * OffsetModePanel - Offset mode controls for CurveLab
 * Extracted from CurveLab.vue
 */
defineProps<{
  offsetDist: number
  join: 'round' | 'miter' | 'bevel'
}>()

const emit = defineEmits<{
  'update:offsetDist': [value: number]
  'update:join': [value: 'round' | 'miter' | 'bevel']
  'apply': []
}>()
</script>

<template>
  <div class="params flex gap-3 items-center flex-wrap">
    <label class="param-label">
      Distance (mm)
      <input
        :value="offsetDist"
        type="number"
        class="param-input"
        step="0.5"
        @input="emit('update:offsetDist', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </label>
    <label class="param-label">
      Join Type
      <select
        :value="join"
        class="param-select"
        @change="emit('update:join', ($event.target as HTMLSelectElement).value as 'round' | 'miter' | 'bevel')"
      >
        <option value="round">Round</option>
        <option value="miter">Miter</option>
        <option value="bevel">Bevel</option>
      </select>
    </label>
    <button
      class="btn btn-primary"
      @click="emit('apply')"
    >
      Apply Offset
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

.param-input,
.param-select {
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
