<template>
  <div class="bridge-calculator-panel">
    <div class="panel-header">
      <div>
        <h3>Bridge Calculator</h3>
        <p>Seed acoustic bridge geometry, visualize the saddle line, then export DXF directly into Bridge Lab.</p>
      </div>
      <label class="unit-toggle">
        <input
          v-model="isMetric"
          type="checkbox"
        >
        <span>Units: {{ unitLabel }}</span>
      </label>
    </div>

    <div class="preset-row">
      <select v-model="presetFamily">
        <option
          v-for="family in familyPresets"
          :key="family.id"
          :value="family.id"
        >
          {{ family.label }}
        </option>
      </select>
      <select v-model="gaugePresetId">
        <option
          v-for="gauge in gaugePresets"
          :key="gauge.id"
          :value="gauge.id"
        >
          {{ gauge.label }}
        </option>
      </select>
      <select v-model="actionPresetId">
        <option
          v-for="action in actionPresets"
          :key="action.id"
          :value="action.id"
        >
          {{ action.label }}
        </option>
      </select>
      <button
        class="btn"
        :disabled="presetsLoading"
        @click="applyPresets"
      >
        {{ presetsLoading ? 'Loading presets…' : 'Apply Presets' }}
      </button>
    </div>

    <p
      v-if="presetError"
      class="error-text"
    >
      {{ presetError }} — using fallback presets.
    </p>

    <div class="calc-grid">
      <section class="calc-card">
        <h4>Scale & Compensation</h4>
        <div
          v-for="field in geometryFields"
          :key="field.key"
          class="field"
        >
          <label :for="field.key">{{ field.label }}</label>
          <div class="field-input">
            <input
              :id="field.key"
              v-model.number="ui[field.key]"
              type="number"
              :step="field.step"
            >
            <span>{{ field.unit }}</span>
          </div>
        </div>

        <div class="summary">
          <div><strong>Angle:</strong> {{ angleDeg.toFixed(3) }}</div>
          <div><strong>Treble (x):</strong> {{ fmt(treble.x) }} {{ unitLabel }}</div>
          <div><strong>Bass (x):</strong> {{ fmt(bass.x) }} {{ unitLabel }}</div>
        </div>
      </section>

      <PreviewCard
        :svg-view-box="svgViewBox"
        :svg-h="svgH"
        :scale="scale"
        :treble="treble"
        :bass="bass"
        :slot-polygon-points="slotPolygonPoints"
        :exporting="exporting"
        @copy-j-s-o-n="copyJSON"
        @download-s-v-g="downloadSVG"
        @export-d-x-f="exportDXF"
      />
    </div>

    <details>
      <summary>Math notes</summary>
      <p>Treble endpoint uses (scale + Ct, -spread/2); bass endpoint uses (scale + Cb, +spread/2). Slot polygon extends {{ ui.slotLength.toFixed(1) }} {{ unitLabel }} along the saddle line and {{ ui.slotWidth.toFixed(1) }} {{ unitLabel }} across.</p>
    </details>

    <p
      v-if="statusMessage"
      class="status-text"
    >
      {{ statusMessage }}
    </p>
  </div>
</template>

<script setup lang="ts">
/**
 * BridgeCalculatorPanel.vue
 *
 * Bridge saddle geometry calculator with preset support,
 * unit conversion, and DXF export.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { watch, onMounted } from 'vue'
import PreviewCard from './PreviewCard.vue'
import {
  useBridgeState,
  useBridgeGeometry,
  useBridgePresets,
  useBridgeUnits,
  useBridgeExport
} from './composables'

// =============================================================================
// EMITS
// =============================================================================

const emit = defineEmits<{ (e: 'dxf-generated', file: File): void }>()

// =============================================================================
// COMPOSABLES
// =============================================================================

const {
  isMetric,
  unitLabel,
  unitMode,
  familyPresets,
  gaugePresets,
  actionPresets,
  presetFamily,
  gaugePresetId,
  actionPresetId,
  presetsLoading,
  presetError,
  ui,
  exporting,
  statusMessage,
  geometryFields
} = useBridgeState()

const {
  scale,
  angleDeg,
  treble,
  bass,
  slotPoly,
  svgH,
  svgViewBox,
  slotPolygonPoints
} = useBridgeGeometry(ui)

const { loadPresets, applyFamilyPreset, applyPresets } = useBridgePresets(
  familyPresets,
  gaugePresets,
  actionPresets,
  presetFamily,
  gaugePresetId,
  actionPresetId,
  presetsLoading,
  presetError,
  unitMode,
  ui
)

const { convertUiToMetric, convertUiToImperial } = useBridgeUnits(ui)

const { copyJSON, downloadSVG, exportDXF, fmt } = useBridgeExport(
  ui,
  unitMode,
  angleDeg,
  treble,
  bass,
  slotPoly,
  svgViewBox,
  svgH,
  scale,
  slotPolygonPoints,
  exporting,
  statusMessage,
  emit
)

// =============================================================================
// WATCHERS
// =============================================================================

watch(isMetric, (next, prev) => {
  if (next === prev) return
  if (next) {
    convertUiToMetric()
  } else {
    convertUiToImperial()
  }
})

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(async () => {
  await loadPresets()
  applyFamilyPreset(presetFamily.value)
})
</script>

<style scoped>
.bridge-calculator-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.panel-header h3 {
  margin: 0;
  font-size: 1.25rem;
}

.panel-header p {
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
  color: #64748b;
}

.unit-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  white-space: nowrap;
}

.preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.preset-row select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-text {
  color: #dc2626;
  font-size: 0.875rem;
}

.calc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.calc-card {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  background: white;
}

.calc-card h4 {
  margin: 0 0 1rem;
  font-size: 1rem;
  color: #374151;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.field label {
  font-size: 0.75rem;
  color: #6b7280;
}

.field-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.field-input input {
  flex: 1;
  padding: 0.375rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.field-input span {
  font-size: 0.75rem;
  color: #9ca3af;
  min-width: 2rem;
}

.summary {
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e5e7eb;
  font-size: 0.875rem;
}

.summary div {
  margin-bottom: 0.25rem;
}

details {
  font-size: 0.875rem;
  color: #6b7280;
}

details summary {
  cursor: pointer;
  user-select: none;
}

details p {
  margin: 0.5rem 0 0;
  padding-left: 1rem;
}

.status-text {
  font-size: 0.875rem;
  color: #059669;
  padding: 0.5rem;
  background: #ecfdf5;
  border-radius: 0.25rem;
}
</style>
