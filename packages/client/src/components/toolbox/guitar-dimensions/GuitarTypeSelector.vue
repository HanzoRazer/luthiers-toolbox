<template>
  <section class="form-section">
    <h3>Guitar Type</h3>
    <div class="button-group">
      <button
        v-for="type in guitarTypes"
        :key="type.id"
        :class="{ active: modelValue === type.id }"
        @click="emit('update:modelValue', type.id)"
      >
        {{ type.icon }} {{ type.label }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { GuitarTypeInfo } from '../composables/useGuitarDimensions'

defineProps<{
  modelValue: string
  guitarTypes: GuitarTypeInfo[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<style scoped>
.form-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #eee;
}

.form-section h3 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  color: #444;
}

.button-group {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.button-group button {
  padding: 0.75rem 1.5rem;
  border: 2px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.button-group button:hover {
  border-color: #667eea;
  color: #667eea;
}

.button-group button.active {
  background: #667eea;
  border-color: #667eea;
  color: white;
}
</style>
