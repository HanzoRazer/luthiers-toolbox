<template>
  <div
    v-if="delta"
    class="diff-mode-toggle"
    role="radiogroup"
    aria-label="Diff display mode"
  >
    <label><input
      v-model="localValue"
      type="radio"
      value="overlay"
      :aria-checked="localValue === 'overlay'"
    > Overlay</label>
    <label><input
      v-model="localValue"
      type="radio"
      value="delta"
      :aria-checked="localValue === 'delta'"
    > Delta Only</label>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ modelValue: string, delta: any }>()
const emit = defineEmits(['update:modelValue'])
const localValue = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})
</script>
<style scoped>
.diff-mode-toggle { margin-bottom: 1rem; display: flex; gap: 1rem; }
</style>
