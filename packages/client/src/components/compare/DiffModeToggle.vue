<template>
  <div class="diff-mode-toggle" v-if="delta" role="radiogroup" aria-label="Diff display mode">
    <label><input type="radio" v-model="modelValue" value="overlay" :aria-checked="modelValue === 'overlay'" /> Overlay</label>
    <label><input type="radio" v-model="modelValue" value="delta" :aria-checked="modelValue === 'delta'" /> Delta Only</label>
  </div>
</template>
<script setup lang="ts">
const props = defineProps<{ modelValue: string, delta: any }>()
const emit = defineEmits(['update:modelValue'])
</script>
<style scoped>
.diff-mode-toggle { margin-bottom: 1rem; display: flex; gap: 1rem; }
</style>
