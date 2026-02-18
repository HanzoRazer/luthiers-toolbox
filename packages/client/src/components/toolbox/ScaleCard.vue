<script setup lang="ts">
/**
 * ScaleCard.vue - Scale length preset card
 *
 * Extracted from ScaleLengthDesigner.vue to reduce LOC and enable reuse.
 */
defineOptions({ name: 'ScaleCard' })

export interface ScalePreset {
  id: string
  name: string
  valueInch: number
  valueMm: number
  traits: string[]
}

defineProps<{
  preset: ScalePreset
  selected?: boolean
}>()

const emit = defineEmits<{
  select: [id: string]
}>()

function formatValue(inch: number, mm: number): string {
  return `${inch}" (${mm}mm)`
}
</script>

<template>
  <div
    class="scale-card"
    :class="{ selected }"
    role="button"
    tabindex="0"
    @click="emit('select', preset.id)"
    @keydown.enter="emit('select', preset.id)"
  >
    <div class="scale-name">{{ preset.name }}</div>
    <div class="scale-value">{{ formatValue(preset.valueInch, preset.valueMm) }}</div>
    <div class="scale-info">
      <div
        v-for="(trait, i) in preset.traits"
        :key="i"
        class="scale-trait"
      >
        • {{ trait }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.scale-card {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  background: white;
}

.scale-card:hover {
  border-color: #3b82f6;
}

.scale-card:focus {
  outline: none;
  box-shadow: 0 0 0 2px #3b82f6;
}

.scale-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.scale-name {
  font-weight: 600;
  font-size: 1rem;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.scale-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #3b82f6;
  margin-bottom: 0.75rem;
}

.scale-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.scale-trait {
  font-size: 0.875rem;
  color: #4b5563;
}
</style>
