<script setup lang="ts">
/**
 * FairModePanel - Fairing mode controls for CurveLab
 * Extracted from CurveLab.vue
 */
defineProps<{
  lam: number
  preserve: boolean
}>()

const emit = defineEmits<{
  'update:lam': [value: number]
  'update:preserve': [value: boolean]
  'apply': []
}>()
</script>

<template>
  <div class="params flex gap-3 items-center flex-wrap">
    <label class="param-label">
      λ (Lambda)
      <input
        :value="lam"
        type="number"
        class="param-input"
        step="1"
        min="0"
        @input="emit('update:lam', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </label>
    <label class="param-checkbox">
      <input
        :checked="preserve"
        type="checkbox"
        @change="emit('update:preserve', ($event.target as HTMLInputElement).checked)"
      >
      Preserve endpoints
    </label>
    <button
      class="btn btn-primary"
      @click="emit('apply')"
    >
      Apply Fairing
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

.param-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #475569;
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
