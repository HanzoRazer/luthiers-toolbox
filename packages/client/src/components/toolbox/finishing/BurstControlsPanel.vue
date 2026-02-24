<script setup lang="ts">
/**
 * BurstControlsPanel - Burst pattern designer controls
 * Extracted from FinishingDesigner.vue
 */
defineProps<{
  styles: Record<string, string>
  burstType: string
  centerColor: string
  midColor: string
  edgeColor: string
  fadeStart: number
  fadeEnd: number
}>()

const emit = defineEmits<{
  'update:burstType': [value: string]
  'update:centerColor': [value: string]
  'update:midColor': [value: string]
  'update:edgeColor': [value: string]
  'update:fadeStart': [value: number]
  'update:fadeEnd': [value: number]
  'applyPreset': [preset: string]
  'exportCsv': []
}>()

const burstTypes = [
  { id: 'solid', name: 'Solid Color' },
  { id: '2-color', name: '2-Color Burst' },
  { id: '3-color', name: '3-Color Burst' }
]
</script>

<template>
  <div :class="styles.burstControls">
    <h3>Burst Type</h3>
    <div :class="styles.burstTypeSelector">
      <div
        v-for="type in burstTypes"
        :key="type.id"
        :class="[styles.burstTypeCard, { [styles.burstTypeCardActive]: burstType === type.id }]"
        @click="emit('update:burstType', type.id)"
      >
        {{ type.name }}
      </div>
    </div>

    <h3>Colors</h3>
    <div :class="styles.colorInputs">
      <div :class="styles.colorInput">
        <label>Center Color</label>
        <input
          :value="centerColor"
          type="color"
          @input="emit('update:centerColor', ($event.target as HTMLInputElement).value)"
        >
        <span>{{ centerColor }}</span>
      </div>
      <div
        v-if="burstType !== 'solid'"
        :class="styles.colorInput"
      >
        <label>Mid Color (optional)</label>
        <input
          :value="midColor"
          type="color"
          @input="emit('update:midColor', ($event.target as HTMLInputElement).value)"
        >
        <span>{{ midColor }}</span>
      </div>
      <div
        v-if="burstType !== 'solid'"
        :class="styles.colorInput"
      >
        <label>Edge Color</label>
        <input
          :value="edgeColor"
          type="color"
          @input="emit('update:edgeColor', ($event.target as HTMLInputElement).value)"
        >
        <span>{{ edgeColor }}</span>
      </div>
    </div>

    <h3>Burst Parameters</h3>
    <div :class="styles.paramInputs">
      <div :class="styles.paramInput">
        <label>Fade Start (mm from center)</label>
        <input
          :value="fadeStart"
          type="number"
          step="5"
          min="0"
          max="150"
          @input="emit('update:fadeStart', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div :class="styles.paramInput">
        <label>Fade End (mm from center)</label>
        <input
          :value="fadeEnd"
          type="number"
          step="5"
          min="0"
          max="200"
          @input="emit('update:fadeEnd', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>

    <h3>Classic Presets</h3>
    <div :class="styles.burstPresets">
      <button
        :class="styles.btnBurst"
        @click="emit('applyPreset', 'tobacco')"
      >
        Tobacco Sunburst
      </button>
      <button
        :class="styles.btnBurst"
        @click="emit('applyPreset', 'cherry')"
      >
        Cherry Sunburst
      </button>
      <button
        :class="styles.btnBurst"
        @click="emit('applyPreset', 'honeyburst')"
      >
        Honeyburst
      </button>
      <button
        :class="styles.btnBurst"
        @click="emit('applyPreset', 'lemondrop')"
      >
        Lemon Drop
      </button>
    </div>

    <button
      :class="styles.btnExport"
      @click="emit('exportCsv')"
    >
      Export CSV for Robotic Spray
    </button>
  </div>
</template>
