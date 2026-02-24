<script setup lang="ts">
/**
 * InstrumentGeometryForm - Scale length, fret count, and compound radius form
 * Extracted from ArtStudioSidebar.vue
 */
import { ref } from 'vue'

interface EngineState {
  loading: { instrument: boolean }
  fretPositions: { value: number[] }
  bridgeLocationMm: { value: number | null }
  fretboardLengthMm: { value: number | null }
  radiusProfile: { value: number[] }
}

const props = defineProps<{
  engine: EngineState
}>()

const emit = defineEmits<{
  'compute': [params: {
    scale_length_mm: number
    fret_count: number
    nut_width_mm: number
    heel_width_mm: number
    base_radius_mm?: number
    end_radius_mm?: number
  }]
}>()

// Preset configurations
const PRESETS: Record<string, { scale: number; nut: number; heel: number }> = {
  'fender_25.5': { scale: 647.7, nut: 42.86, heel: 56 },
  'gibson_24.75': { scale: 628.65, nut: 43.05, heel: 55 },
  prs_25: { scale: 635, nut: 42.5, heel: 55.5 },
  classical: { scale: 650, nut: 52, heel: 62 },
}

// Local state
const selectedPreset = ref('')
const scaleLengthMm = ref(648) // 25.5"
const fretCount = ref(22)
const nutWidthMm = ref(42)
const heelWidthMm = ref(56)
const baseRadiusMm = ref<number | undefined>(undefined)
const endRadiusMm = ref<number | undefined>(undefined)

function onPresetChange() {
  if (selectedPreset.value && PRESETS[selectedPreset.value]) {
    const preset = PRESETS[selectedPreset.value]
    scaleLengthMm.value = preset.scale
    nutWidthMm.value = preset.nut
    heelWidthMm.value = preset.heel
  }
}

function onComputeGeometry() {
  emit('compute', {
    scale_length_mm: scaleLengthMm.value,
    fret_count: fretCount.value,
    nut_width_mm: nutWidthMm.value,
    heel_width_mm: heelWidthMm.value,
    base_radius_mm: baseRadiusMm.value,
    end_radius_mm: endRadiusMm.value,
  })
}
</script>

<template>
  <section class="sidebar-section">
    <h3>Instrument Geometry</h3>

    <!-- Presets -->
    <div class="form-row">
      <label>Preset</label>
      <select
        v-model="selectedPreset"
        @change="onPresetChange"
      >
        <option value="">
          Custom
        </option>
        <option value="fender_25.5">
          Fender 25.5"
        </option>
        <option value="gibson_24.75">
          Gibson 24.75"
        </option>
        <option value="prs_25">
          PRS 25"
        </option>
        <option value="classical">
          Classical
        </option>
      </select>
    </div>

    <div class="form-row">
      <label>Scale Length (mm)</label>
      <input
        v-model.number="scaleLengthMm"
        type="number"
        step="0.1"
      >
    </div>

    <div class="form-row">
      <label>Fret Count</label>
      <input
        v-model.number="fretCount"
        type="number"
        min="1"
        max="36"
      >
    </div>

    <div class="form-row">
      <label>Nut Width (mm)</label>
      <input
        v-model.number="nutWidthMm"
        type="number"
        step="0.1"
      >
    </div>

    <div class="form-row">
      <label>Heel Width (mm)</label>
      <input
        v-model.number="heelWidthMm"
        type="number"
        step="0.1"
      >
    </div>

    <details class="advanced-options">
      <summary>Compound Radius</summary>
      <div class="form-row">
        <label>Base Radius (mm)</label>
        <input
          v-model.number="baseRadiusMm"
          type="number"
          step="1"
          placeholder="e.g., 184 (7.25in)"
        >
      </div>
      <div class="form-row">
        <label>End Radius (mm)</label>
        <input
          v-model.number="endRadiusMm"
          type="number"
          step="1"
          placeholder="e.g., 305 (12in)"
        >
      </div>
    </details>

    <button
      :disabled="engine.loading.instrument"
      class="primary-button"
      @click="onComputeGeometry"
    >
      {{ engine.loading.instrument ? "Computing..." : "Compute Geometry" }}
    </button>

    <!-- Results -->
    <div
      v-if="engine.fretPositions.value.length"
      class="instrument-results"
    >
      <p>{{ engine.fretPositions.value.length }} frets calculated</p>
      <p v-if="engine.bridgeLocationMm.value !== null">
        Bridge @ {{ engine.bridgeLocationMm.value?.toFixed(2) }}mm
      </p>
      <p v-if="engine.fretboardLengthMm.value !== null">
        Fretboard length: {{ engine.fretboardLengthMm.value?.toFixed(2) }}mm
      </p>
      <p v-if="engine.radiusProfile.value.length">
        Compound radius: {{ engine.radiusProfile.value[0]?.toFixed(1) }}mm →
        {{
          engine.radiusProfile.value[
            engine.radiusProfile.value.length - 1
          ]?.toFixed(1)
        }}mm
      </p>
    </div>
  </section>
</template>

<style scoped>
.sidebar-section {
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 0.75rem;
}

.sidebar-section h3 {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #212529;
}

.form-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 0.35rem;
}

.form-row label {
  font-size: 0.75rem;
  color: #6c757d;
  margin-bottom: 0.15rem;
}

.form-row input,
.form-row select {
  padding: 0.3rem 0.4rem;
  font-size: 0.8rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
}

.advanced-options {
  margin: 0.5rem 0;
  padding: 0.25rem;
  background: #f1f3f4;
  border-radius: 4px;
}

.advanced-options summary {
  font-size: 0.75rem;
  color: #495057;
  cursor: pointer;
  padding: 0.25rem;
}

.primary-button {
  width: 100%;
  padding: 0.5rem;
  font-size: 0.8rem;
  font-weight: 500;
  border: none;
  background: #0d6efd;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.5rem;
}

.primary-button:hover:not(:disabled) {
  background: #0b5ed7;
}

.primary-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.instrument-results {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #d1e7dd;
  border-radius: 4px;
  font-size: 0.75rem;
}

.instrument-results p {
  margin: 0.15rem 0;
}
</style>
