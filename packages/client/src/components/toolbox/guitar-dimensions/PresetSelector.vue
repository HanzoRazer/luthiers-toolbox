<template>
  <section class="form-section">
    <h3>Load Preset</h3>
    <div class="preset-buttons">
      <button
        v-for="preset in presets"
        :key="preset.id"
        class="preset-btn"
        @click="emit('load', preset.id)"
      >
        {{ preset.name }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { PresetInfo } from '../composables/useGuitarDimensions'

defineProps<{
  presets: PresetInfo[]
}>()

const emit = defineEmits<{
  load: [presetId: string]
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

.preset-buttons {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.preset-btn {
  padding: 0.65rem 1.25rem;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.preset-btn:hover {
  background: #667eea;
  border-color: #667eea;
  color: white;
}
</style>
