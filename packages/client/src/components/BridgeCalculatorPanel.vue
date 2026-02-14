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
      ⚠️ {{ presetError }} — using fallback presets.
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
          <div><strong>Angle θ:</strong> {{ angleDeg.toFixed(3) }}°</div>
          <div><strong>Treble (x):</strong> {{ fmt(treble.x) }} {{ unitLabel }}</div>
          <div><strong>Bass (x):</strong> {{ fmt(bass.x) }} {{ unitLabel }}</div>
        </div>
      </section>

      <section class="calc-card preview-card">
        <h4>Preview (not to scale)</h4>
        <svg
          :viewBox="svgViewBox"
          preserveAspectRatio="xMidYMid meet"
          class="preview"
        >
          <line
            :x1="0"
            :y1="-svgH/2"
            :x2="0"
            :y2="svgH/2"
            stroke="#cbd5f5"
            stroke-dasharray="2,2"
            stroke-width="0.3"
          />
          <line
            :x1="scale"
            y1="-3"
            :x2="scale"
            y2="3"
            stroke="#94a3b8"
            stroke-width="0.4"
          />
          <line
            :x1="treble.x"
            :y1="treble.y"
            :x2="bass.x"
            :y2="bass.y"
            stroke="#0ea5e9"
            stroke-width="0.7"
          />
          <polygon
            :points="slotPolygonPoints"
            fill="rgba(14,165,233,0.2)"
            stroke="#0284c7"
            stroke-width="0.5"
          />
          <circle
            :cx="treble.x"
            :cy="treble.y"
            r="0.8"
            fill="#0ea5e9"
          />
          <circle
            :cx="bass.x"
            :cy="bass.y"
            r="0.8"
            fill="#0ea5e9"
          />
        </svg>

        <div class="action-row">
          <button
            class="btn"
            @click="copyJSON"
          >
            Copy JSON
          </button>
          <button
            class="btn"
            @click="downloadSVG"
          >
            Download SVG
          </button>
          <button
            class="btn btn-export"
            :disabled="exporting"
            @click="exportDXF"
          >
            {{ exporting ? 'Exporting…' : 'Export DXF' }}
          </button>
        </div>
      </section>
    </div>

    <details>
      <summary>Math notes</summary>
      <p>Treble endpoint uses (scale + Cₜ, -spread/2); bass endpoint uses (scale + Cᵦ, +spread/2). Slot polygon extends {{ ui.slotLength.toFixed(1) }} {{ unitLabel }} along the saddle line and {{ ui.slotWidth.toFixed(1) }} {{ unitLabel }} across.</p>
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
import { computed, reactive, ref, onMounted, watch } from 'vue'

type UnitMode = 'mm' | 'inch'

type FamilyPreset = {
  id: string
  label: string
  scaleLength: number
  stringSpread: number
  compTreble: number
  compBass: number
  slotWidth: number
  slotLength: number
}

type AdjustmentPreset = {
  id: string
  label: string
  compAdjust?: number
  trebleAdjust?: number
  bassAdjust?: number
}

type UiFieldKey = 'scale' | 'spread' | 'compTreble' | 'compBass' | 'slotWidth' | 'slotLength'

const FALLBACK_FAMILIES: FamilyPreset[] = [
  { id: 'les_paul', label: 'Les Paul (24.75")', scaleLength: 628.65, stringSpread: 52, compTreble: 1.5, compBass: 3, slotWidth: 3, slotLength: 75 },
  { id: 'strat_tele', label: 'Strat/Tele (25.5")', scaleLength: 647.7, stringSpread: 52.5, compTreble: 2, compBass: 3.5, slotWidth: 3, slotLength: 75 },
  { id: 'om', label: 'OM Acoustic (25.4")', scaleLength: 645.16, stringSpread: 54, compTreble: 2, compBass: 4.2, slotWidth: 3.2, slotLength: 80 },
  { id: 'dread', label: 'Dreadnought (25.4")', scaleLength: 645.16, stringSpread: 54, compTreble: 2, compBass: 4.5, slotWidth: 3.2, slotLength: 80 },
  { id: 'archtop', label: 'Archtop (25.0")', scaleLength: 635, stringSpread: 52, compTreble: 1.8, compBass: 3.2, slotWidth: 3, slotLength: 75 }
]

const FALLBACK_GAUGES: AdjustmentPreset[] = [
  { id: 'light', label: 'Light Gauge', trebleAdjust: -0.3, bassAdjust: -0.3 },
  { id: 'medium', label: 'Medium Gauge', trebleAdjust: 0, bassAdjust: 0 },
  { id: 'heavy', label: 'Heavy Gauge', trebleAdjust: 0.3, bassAdjust: 0.4 }
]

const FALLBACK_ACTIONS: AdjustmentPreset[] = [
  { id: 'low', label: 'Low Action', trebleAdjust: -0.2, bassAdjust: -0.2 },
  { id: 'standard', label: 'Standard Action', trebleAdjust: 0, bassAdjust: 0 },
  { id: 'high', label: 'High Action', trebleAdjust: 0.3, bassAdjust: 0.4 }
]

const emit = defineEmits<{ (e: 'dxf-generated', file: File): void }>()

const isMetric = ref(true)
const unitLabel = computed(() => (isMetric.value ? 'mm' : 'in'))
const unitMode = computed<UnitMode>(() => (isMetric.value ? 'mm' : 'inch'))

const familyPresets = ref<FamilyPreset[]>([...FALLBACK_FAMILIES])
const gaugePresets = ref<AdjustmentPreset[]>([...FALLBACK_GAUGES])
const actionPresets = ref<AdjustmentPreset[]>([...FALLBACK_ACTIONS])
const presetFamily = ref<FamilyPreset['id']>(familyPresets.value[1]?.id ?? 'strat_tele')
const gaugePresetId = ref<AdjustmentPreset['id']>('medium')
const actionPresetId = ref<AdjustmentPreset['id']>('standard')
const presetsLoading = ref(false)
const presetError = ref<string | null>(null)

const exporting = ref(false)
const statusMessage = ref<string | null>(null)

const ui = reactive<Record<UiFieldKey, number>>({
  scale: familyPresets.value[1]?.scaleLength ?? 647.7,
  spread: familyPresets.value[1]?.stringSpread ?? 52.5,
  compTreble: 2.0,
  compBass: 3.5,
  slotWidth: 3.0,
  slotLength: 75.0
})

const geometryFields = computed<Array<{ key: UiFieldKey; label: string; step: number; unit: string }>>(() => [
  { key: 'scale', label: 'Scale length', step: 0.01, unit: unitLabel.value },
  { key: 'spread', label: 'Saddle string spread', step: 0.01, unit: unitLabel.value },
  { key: 'compTreble', label: 'Compensation — Treble', step: 0.01, unit: unitLabel.value },
  { key: 'compBass', label: 'Compensation — Bass', step: 0.01, unit: unitLabel.value },
  { key: 'slotWidth', label: 'Slot width', step: 0.01, unit: unitLabel.value },
  { key: 'slotLength', label: 'Slot length (visual)', step: 0.1, unit: unitLabel.value }
])

const scale = computed(() => ui.scale)
const spread = computed(() => ui.spread)
const Ct = computed(() => ui.compTreble)
const Cb = computed(() => ui.compBass)
const angleDeg = computed(() => Math.atan((Cb.value - Ct.value) / Math.max(spread.value, 1e-6)) * (180 / Math.PI))
const treble = computed(() => ({ x: scale.value + Ct.value, y: -spread.value / 2 }))
const bass = computed(() => ({ x: scale.value + Cb.value, y: spread.value / 2 }))

const slotPoly = computed(() => {
  const x1 = treble.value.x
  const y1 = treble.value.y
  const x2 = bass.value.x
  const y2 = bass.value.y
  const dx = x2 - x1
  const dy = y2 - y1
  const length = Math.hypot(dx, dy) || 1
  const nx = -dy / length
  const ny = dx / length
  const halfWidth = ui.slotWidth / 2
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2
  const tx = dx / length
  const ty = dy / length
  const halfLen = ui.slotLength / 2

  const A = { x: mx - halfLen * tx + halfWidth * nx, y: my - halfLen * ty + halfWidth * ny }
  const B = { x: mx + halfLen * tx + halfWidth * nx, y: my + halfLen * ty + halfWidth * ny }
  const C = { x: mx + halfLen * tx - halfWidth * nx, y: my + halfLen * ty - halfWidth * ny }
  const D = { x: mx - halfLen * tx - halfWidth * nx, y: my - halfLen * ty - halfWidth * ny }
  return [A, B, C, D]
})

const svgPadding = 10
const svgH = computed(() => spread.value + svgPadding * 2)
const svgViewBox = computed(() => {
  const minX = Math.min(0, treble.value.x, bass.value.x) - svgPadding
  const minY = -spread.value / 2 - svgPadding
  const width = (Math.max(treble.value.x, bass.value.x) + svgPadding) - minX
  const height = svgH.value
  return `${minX} ${minY} ${width} ${height}`
})
const slotPolygonPoints = computed(() => slotPoly.value.map((p) => `${p.x},${p.y}`).join(' '))

onMounted(async () => {
  await loadPresets()
  applyFamilyPreset(presetFamily.value)
})

watch(isMetric, (next, prev) => {
  if (next === prev) return
  if (next) {
    convertUiToMetric()
  } else {
    convertUiToImperial()
  }
})

function convertUiToMetric() {
  ui.scale = inToMm(ui.scale)
  ui.spread = inToMm(ui.spread)
  ui.compTreble = inToMm(ui.compTreble)
  ui.compBass = inToMm(ui.compBass)
  ui.slotWidth = inToMm(ui.slotWidth)
  ui.slotLength = inToMm(ui.slotLength)
}

function convertUiToImperial() {
  ui.scale = mmToIn(ui.scale)
  ui.spread = mmToIn(ui.spread)
  ui.compTreble = mmToIn(ui.compTreble)
  ui.compBass = mmToIn(ui.compBass)
  ui.slotWidth = mmToIn(ui.slotWidth)
  ui.slotLength = mmToIn(ui.slotLength)
}

function mmToIn(value: number): number {
  return value / 25.4
}

function inToMm(value: number): number {
  return value * 25.4
}

async function loadPresets() {
  // Fallback presets are already loaded by default initialization
  // API presets endpoint is optional - silently use fallbacks if unavailable
  try {
    presetsLoading.value = true
    presetError.value = null
    const response = await fetch('/api/cam/bridge/presets')
    if (response.ok) {
      const data = await response.json()
      if (Array.isArray(data?.families) && data.families.length) {
        familyPresets.value = data.families
      }
      if (Array.isArray(data?.gauges) && data.gauges.length) {
        gaugePresets.value = data.gauges
      }
      if (Array.isArray(data?.actions) && data.actions.length) {
        actionPresets.value = data.actions
      }
    }
    // Non-2xx response silently uses fallbacks (no error shown to user)
  } catch {
    // Network errors silently use fallbacks (no error shown to user)
    console.debug('Bridge presets API unavailable, using fallback presets')
  } finally {
    presetsLoading.value = false
  }
}

function applyFamilyPreset(id: string) {
  const preset = familyPresets.value.find((f) => f.id === id) ?? familyPresets.value[0]
  if (!preset) return
  if (unitMode.value === 'mm') {
    ui.scale = preset.scaleLength
    ui.spread = preset.stringSpread
    ui.compTreble = preset.compTreble
    ui.compBass = preset.compBass
    ui.slotWidth = preset.slotWidth
    ui.slotLength = preset.slotLength
  } else {
    ui.scale = mmToIn(preset.scaleLength)
    ui.spread = mmToIn(preset.stringSpread)
    ui.compTreble = mmToIn(preset.compTreble)
    ui.compBass = mmToIn(preset.compBass)
    ui.slotWidth = mmToIn(preset.slotWidth)
    ui.slotLength = mmToIn(preset.slotLength)
  }
}

function getPresetAdjust(presets: AdjustmentPreset[], id: string): { treble: number; bass: number } {
  const preset = presets.find((p) => p.id === id)
  return {
    treble: preset?.trebleAdjust ?? preset?.compAdjust ?? 0,
    bass: preset?.bassAdjust ?? preset?.compAdjust ?? 0
  }
}

function applyPresets() {
  applyFamilyPreset(presetFamily.value)
  const gauge = getPresetAdjust(gaugePresets.value, gaugePresetId.value)
  const action = getPresetAdjust(actionPresets.value, actionPresetId.value)
  const trebleDelta = gauge.treble + action.treble
  const bassDelta = gauge.bass + action.bass
  const factor = unitMode.value === 'mm' ? 1 : 1 / 25.4
  ui.compTreble += trebleDelta * factor
  ui.compBass += bassDelta * factor
}

function currentModel() {
  return {
    units: unitMode.value,
    scaleLength: round2(ui.scale),
    stringSpread: round2(ui.spread),
    compTreble: round2(ui.compTreble),
    compBass: round2(ui.compBass),
    slotWidth: round2(ui.slotWidth),
    slotLength: round2(ui.slotLength),
    angleDeg: round3(angleDeg.value),
    endpoints: {
      treble: { x: round3(treble.value.x), y: round3(treble.value.y) },
      bass: { x: round3(bass.value.x), y: round3(bass.value.y) }
    },
    slotPolygon: slotPoly.value.map((p) => ({ x: round3(p.x), y: round3(p.y) }))
  }
}

function round2(value: number) {
  return Math.round(value * 100) / 100
}

function round3(value: number) {
  return Math.round(value * 1000) / 1000
}

async function copyJSON() {
  try {
    await navigator.clipboard?.writeText(JSON.stringify(currentModel(), null, 2))
    statusMessage.value = 'Model JSON copied to clipboard.'
  } catch (error) {
    console.error('Clipboard error', error)
    statusMessage.value = 'Unable to copy JSON — clipboard permissions denied.'
  }
}

function downloadSVG() {
  const vb = svgViewBox.value.split(' ').map(Number)
  const svg = `<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.join(' ')}">\n  <line x1="0" y1="${-svgH.value / 2}" x2="0" y2="${svgH.value / 2}" stroke="#cbd5f5" stroke-dasharray="2,2" stroke-width="0.3"/>\n  <line x1="${scale.value}" y1="-3" x2="${scale.value}" y2="3" stroke="#94a3b8" stroke-width="0.4"/>\n  <line x1="${treble.value.x}" y1="${treble.value.y}" x2="${bass.value.x}" y2="${bass.value.y}" stroke="#0ea5e9" stroke-width="0.7"/>\n  <polygon points="${slotPolygonPoints.value}" fill="rgba(14,165,233,0.2)" stroke="#0284c7" stroke-width="0.5"/>\n</svg>`
  const blob = new Blob([svg], { type: 'image/svg+xml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `bridge_saddle_${unitMode.value}.svg`
  a.click()
  URL.revokeObjectURL(url)
}

async function exportDXF() {
  try {
    exporting.value = true
    statusMessage.value = null
    const model = currentModel()
    const payload = {
      geometry: model,
      filename: `bridge_${model.scaleLength.toFixed(1)}${model.units}_ct${model.compTreble.toFixed(1)}_cb${model.compBass.toFixed(1)}`
    }
    const response = await fetch('/api/cam/bridge/export_dxf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!response.ok) {
      throw new Error(await response.text())
    }
    const blob = await response.blob()
    const fileName = `${payload.filename}.dxf`
    const file = new File([blob], fileName, { type: 'application/dxf' })
    emit('dxf-generated', file)

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    a.click()
    URL.revokeObjectURL(url)

    statusMessage.value = `DXF exported: ${fileName}`
  } catch (error) {
    console.error('DXF export error', error)
    statusMessage.value = `DXF export failed: ${error instanceof Error ? error.message : error}`
  } finally {
    exporting.value = false
  }
}

function fmt(value: number) {
  return value.toFixed(2)
}
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
  gap: 1rem;
  flex-wrap: wrap;
}

.panel-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.panel-header p {
  margin: 0.25rem 0 0;
  color: #6b7280;
}

.unit-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.preset-row select {
  min-width: 10rem;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  background: #3b82f6;
  color: white;
  font-weight: 500;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-export {
  background: #10b981;
}

.calc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.calc-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.25rem;
  border: 1px solid #e5e7eb;
}

.calc-card h4 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
}

.field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  gap: 1rem;
}

.field label {
  font-weight: 500;
  color: #374151;
}

.field-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.field-input input {
  width: 8rem;
  padding: 0.35rem 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.375rem;
}

.preview-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.preview {
  width: 100%;
  height: 320px;
  background: #fff;
  border: 1px dashed #e2e8f0;
  border-radius: 0.5rem;
}

.summary {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #0f172a;
  display: grid;
  gap: 0.25rem;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.error-text {
  color: #b45309;
  margin: 0;
}

.status-text {
  margin: 0;
  color: #047857;
  font-weight: 500;
}

details {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  background: white;
}

details summary {
  cursor: pointer;
  font-weight: 600;
}

@media (max-width: 768px) {
  .preset-row {
    flex-direction: column;
  }
}
</style>
