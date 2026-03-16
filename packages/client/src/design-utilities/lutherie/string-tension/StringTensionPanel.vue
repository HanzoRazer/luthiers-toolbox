<!--
  StringTensionPanel.vue
  ========================
  The Production Shop — String Tension Calculator

  Lutherie Geometry suite — CalculatorHub card: "String Tension"

  Architecture:
    useTension()   — physics engine, string set state, set analysis
    useBreakAngle() — break angle API wrapper + manual override

  Placement:
    CalculatorHub.vue → Lutherie Geometry category
    Route: /calculators (tab/panel within hub)

  Known debt:
    R-7 — bridge_break_angle.py must be updated to v2 geometry before
           break angle computed mode is fully reliable.
           Current v1 API thresholds are overridden client-side using
           Carruth 6° floor when instrumentType.useCarruthThresholds = true.
-->

<template>
  <div class="stp">

    <!-- ===================================================================
         TOOLBAR
    ==================================================================== -->
    <div class="stp-toolbar">

      <!-- Instrument type -->
      <div class="stp-field-group">
        <label class="stp-label">Instrument</label>
        <select v-model="instrumentType" class="stp-select">
          <option
            v-for="t in INSTRUMENT_TYPES"
            :key="t.id"
            :value="t.id"
          >{{ t.label }}</option>
        </select>
      </div>

      <!-- Global scale length -->
      <div class="stp-field-group">
        <label class="stp-label">Scale</label>
        <input
          v-model.number="globalScaleLength"
          type="number"
          step="0.1"
          min="10"
          max="42"
          class="stp-input stp-input--narrow"
        >
        <span class="stp-unit">in</span>
      </div>

      <!-- Multi-scale toggle -->
      <button
        :class="['stp-toggle', { 'stp-toggle--on': multiScale }]"
        @click="multiScale = !multiScale"
      >
        Multi-scale {{ multiScale ? 'on' : 'off' }}
      </button>

      <!-- Unit selector -->
      <div class="stp-unit-group">
        <button
          v-for="u in (['lbs', 'N', 'kg'] as TensionUnit[])"
          :key="u"
          :class="['stp-unit-btn', { 'stp-unit-btn--on': unit === u }]"
          @click="unit = u"
        >{{ u }}</button>
      </div>
    </div>

    <!-- ===================================================================
         PRESET STRIP
    ==================================================================== -->
    <div class="stp-preset-bar">
      <!-- Category tabs -->
      <div class="stp-cat-tabs">
        <button
          v-for="cat in PRESET_CATEGORIES"
          :key="cat.id"
          :class="['stp-cat-tab', { 'stp-cat-tab--on': activeCat === cat.id }, cat.id === 'validated' ? 'stp-cat-tab--valid' : '']"
          @click="activeCat = cat.id"
        >{{ cat.label }}</button>
      </div>

      <!-- Preset buttons -->
      <div class="stp-presets">
        <button
          v-for="p in visiblePresets"
          :key="p.id"
          :class="[
            'stp-preset-btn',
            { 'stp-preset-btn--on': activePresetId === p.id },
            p.validated ? 'stp-preset-btn--valid' : '',
          ]"
          @click="loadPreset(p.id)"
        >{{ p.label }}</button>
      </div>
    </div>

    <!-- ===================================================================
         MAIN BODY — strings table + side panel
    ==================================================================== -->
    <div class="stp-body">

      <!-- String table -->
      <div class="stp-table-wrap">
        <table class="stp-table">
          <thead>
            <tr>
              <th style="width:24px">#</th>
              <th style="width:58px">Note</th>
              <th style="width:40px">Oct</th>
              <th style="width:56px">Gauge</th>
              <th>Material</th>
              <th v-if="multiScale" style="width:64px">Scale</th>
              <th>Tension</th>
              <th style="width:74px; text-align:right">Value</th>
              <th style="width:28px"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(s, idx) in strings"
              :key="s.id"
              class="stp-row"
            >
              <!-- Number dot -->
              <td>
                <div
                  class="stp-dot"
                  :style="{ background: tensionColor(results[idx]?.tensionLbs ?? 0) }"
                >{{ idx + 1 }}</div>
              </td>

              <!-- Note -->
              <td>
                <select
                  :value="s.note"
                  class="stp-cell-select"
                  @change="updateString(s.id, { note: ($event.target as HTMLSelectElement).value as NoteName })"
                >
                  <option v-for="n in noteNames" :key="n" :value="n">{{ n }}</option>
                </select>
              </td>

              <!-- Octave -->
              <td>
                <select
                  :value="s.octave"
                  class="stp-cell-select"
                  @change="updateString(s.id, { octave: parseInt(($event.target as HTMLSelectElement).value) })"
                >
                  <option v-for="o in [0,1,2,3,4,5,6]" :key="o" :value="o">{{ o }}</option>
                </select>
              </td>

              <!-- Gauge -->
              <td>
                <input
                  :value="s.gauge"
                  type="number"
                  min="7"
                  max="150"
                  step="1"
                  class="stp-cell-input"
                  :class="{ 'stp-cell-input--override': results[idx]?.isOverride }"
                  @change="updateString(s.id, { gauge: parseInt(($event.target as HTMLInputElement).value) || s.gauge })"
                >
              </td>

              <!-- Material -->
              <td>
                <select
                  :value="s.material"
                  class="stp-cell-select"
                  @change="updateString(s.id, { material: ($event.target as HTMLSelectElement).value as StringMaterial })"
                >
                  <option v-for="m in MATERIALS" :key="m.id" :value="m.id">{{ m.label }}</option>
                </select>
              </td>

              <!-- Per-string scale (multi-scale mode) -->
              <td v-if="multiScale">
                <input
                  :value="s.scaleLength"
                  type="number"
                  min="10"
                  max="42"
                  step="0.1"
                  class="stp-cell-input"
                  @change="updateString(s.id, { scaleLength: parseFloat(($event.target as HTMLInputElement).value) || s.scaleLength })"
                >
              </td>

              <!-- Bar -->
              <td>
                <div class="stp-bar-track">
                  <div
                    class="stp-bar-fill"
                    :style="{
                      width: barWidth(results[idx]?.tensionLbs ?? 0) + '%',
                      background: tensionColor(results[idx]?.tensionLbs ?? 0),
                    }"
                  />
                </div>
              </td>

              <!-- Value -->
              <td class="stp-value" :style="{ color: tensionColor(results[idx]?.tensionLbs ?? 0) }">
                {{ formatTension(results[idx]?.tensionLbs ?? 0) }}
              </td>

              <!-- Remove -->
              <td>
                <button
                  class="stp-remove-btn"
                  title="Remove string"
                  @click="removeString(s.id)"
                >×</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="stp-table-footer">
          <button class="stp-add-btn" @click="addString">+ Add string</button>
          <span v-if="hasOverrides" class="stp-override-note">
            † grey gauge = empirical UW override active
          </span>
        </div>
      </div>

      <!-- Side panel -->
      <div class="stp-side">

        <!-- Total load -->
        <div class="stp-card">
          <div class="stp-card-label">Total load</div>
          <div class="stp-card-value stp-card-value--amber">
            {{ formatTension(setAnalysis.totalTensionLbs) }}
          </div>
          <div class="stp-card-sub">
            {{ formatTensionAlt(setAnalysis.totalTensionLbs) }} ·
            {{ formatTension(setAnalysis.avgTensionLbs) }} avg
          </div>
        </div>

        <!-- Balance -->
        <div class="stp-card">
          <div class="stp-card-label">Set balance</div>
          <div class="stp-balance-row">
            <span
              class="stp-card-value"
              :style="{ color: balanceColor(setAnalysis.balanceScore) }"
            >{{ (setAnalysis.balanceScore * 100).toFixed(0) }}%</span>
            <div>
              <div
                class="stp-balance-label"
                :style="{ color: balanceColor(setAnalysis.balanceScore) }"
              >{{ balanceLabel(setAnalysis.balanceScore) }}</div>
              <div class="stp-card-sub">tension CV</div>
            </div>
          </div>
          <div class="stp-bar-track stp-bar-track--thick" style="margin-top:8px">
            <div
              class="stp-bar-fill"
              :style="{
                width: (setAnalysis.balanceScore * 100).toFixed(0) + '%',
                background: balanceColor(setAnalysis.balanceScore),
              }"
            />
          </div>
        </div>

        <!-- Structural outputs -->
        <div class="stp-card">
          <div class="stp-card-label">Structural</div>

          <div class="stp-stat-row">
            <span class="stp-stat-key">Neck load</span>
            <span class="stp-stat-val stp-stat-val--blue">{{ formatTension(setAnalysis.neckLoadLbs) }}</span>
          </div>
          <div class="stp-stat-row">
            <span class="stp-stat-key">Top / bridge</span>
            <span class="stp-stat-val stp-stat-val--blue">{{ formatTension(setAnalysis.topLoadLbs) }}</span>
          </div>

          <!-- Break angle section -->
          <div class="stp-break-angle">
            <div class="stp-break-angle-header">
              <span class="stp-stat-key">Break angle</span>
              <div class="stp-mode-pills">
                <button
                  :class="['stp-pill', { 'stp-pill--on': breakAngle.mode.value === 'manual' }]"
                  @click="breakAngle.setMode('manual')"
                >Manual</button>
                <button
                  :class="['stp-pill', { 'stp-pill--on': breakAngle.mode.value === 'computed' }]"
                  @click="breakAngle.setMode('computed')"
                >Computed</button>
              </div>
            </div>

            <!-- Manual input -->
            <div v-if="breakAngle.mode.value === 'manual'" class="stp-break-manual">
              <input
                v-model.number="breakAngle.manualDeg.value"
                type="number"
                min="0"
                max="60"
                step="0.5"
                class="stp-input stp-input--narrow"
                @input="syncBreakAngle"
              >
              <span class="stp-unit">°</span>
              <span class="stp-manual-badge">unvalidated</span>
            </div>

            <!-- Computed geometry inputs -->
            <div v-else class="stp-break-computed">
              <div class="stp-break-field">
                <label class="stp-break-label">Pin→saddle center (mm)</label>
                <input
                  :value="breakAngle.geometry.value.pinToSaddleCenterMm"
                  type="number"
                  min="3"
                  max="10"
                  step="0.1"
                  class="stp-input stp-input--narrow"
                  @change="breakAngle.updateGeometry({ pinToSaddleCenterMm: parseFloat(($event.target as HTMLInputElement).value) })"
                >
              </div>
              <div class="stp-break-field">
                <label class="stp-break-label">Saddle protrusion (mm)</label>
                <input
                  :value="breakAngle.geometry.value.saddleProtrusionMm"
                  type="number"
                  min="0.5"
                  max="8"
                  step="0.1"
                  class="stp-input stp-input--narrow"
                  @change="breakAngle.updateGeometry({ saddleProtrusionMm: parseFloat(($event.target as HTMLInputElement).value) })"
                >
              </div>
              <button
                class="stp-compute-btn"
                :disabled="breakAngle.loading.value"
                @click="computeBreakAngle"
              >
                {{ breakAngle.loading.value ? 'Calculating…' : 'Calculate' }}
              </button>
              <div v-if="breakAngle.error.value" class="stp-break-error">
                {{ breakAngle.error.value }}
              </div>
              <div v-if="breakAngle.apiResult.value" class="stp-break-result">
                <span
                  class="stp-break-deg"
                  :style="{ color: breakAngleColor }"
                >{{ breakAngle.resolved.value.deg.toFixed(1) }}°</span>
                <span
                  class="stp-break-status"
                  :style="{ color: breakAngleColor }"
                >{{ breakAngle.resolved.value.statusLabel }}</span>
              </div>
            </div>

            <!-- Carruth note (acoustic pin bridge only) -->
            <div v-if="useCarruthThresholds" class="stp-carruth-note">
              Carruth min: 6° (acoustic pin bridge)
              <span
                v-if="breakAngleAdequacy"
                class="stp-carruth-badge"
                :class="`stp-carruth-badge--${breakAngleAdequacy}`"
              >{{ breakAngleAdequacy }}</span>
            </div>

            <!-- Risk flags from API -->
            <div
              v-for="flag in breakAngle.resolved.value.riskFlags"
              :key="flag.code"
              class="stp-flag"
              :class="`stp-flag--${flag.severity}`"
            >
              {{ flag.message }}
            </div>

            <!-- v1 debt notice -->
            <div v-if="breakAngle.mode.value === 'computed'" class="stp-debt-notice">
              ⚠ API thresholds are v1 (pending R-7 correction)
            </div>
          </div>
        </div>

        <!-- Unit weight reference -->
        <div class="stp-card">
          <div class="stp-card-label">
            Unit weights (lbs/in)
            <span v-if="hasOverrides" class="stp-uw-note">† = empirical/measured</span>
          </div>
          <div
            v-for="(s, idx) in strings"
            :key="s.id"
            class="stp-stat-row"
          >
            <span class="stp-stat-key stp-mono">
              {{ s.note }}{{ s.octave }} .{{ String(s.gauge).padStart(3, '0') }}
              <span v-if="results[idx]?.isOverride" class="stp-uw-dagger">†</span>
            </span>
            <span class="stp-stat-val stp-mono stp-stat-val--muted">
              {{ ((results[idx]?.unitWeight ?? 0) * 1e6).toFixed(2) }}×10⁻⁶
            </span>
          </div>
        </div>

        <!-- Validated reference comparison (shown for validated presets) -->
        <div v-if="activePreset?.validated && activePreset.refTensionsN" class="stp-card stp-card--valid">
          <div class="stp-card-label stp-card-label--green">
            Validation — {{ activePreset.validationSource }}
          </div>
          <div v-if="activePreset.note" class="stp-valid-note">{{ activePreset.note }}</div>
          <table class="stp-valid-table">
            <thead>
              <tr>
                <th>String</th>
                <th>Ref</th>
                <th>Calc</th>
                <th>Δ</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(refN, idx) in activePreset.refTensionsN" :key="idx">
                <td class="stp-mono">{{ strings[idx]?.note }}{{ strings[idx]?.octave }} .{{ String(strings[idx]?.gauge ?? 0).padStart(3,'0') }}</td>
                <td class="stp-mono">{{ formatValidationTension(refN) }}</td>
                <td class="stp-mono">{{ formatTension(results[idx]?.tensionLbs ?? 0) }}</td>
                <td class="stp-mono" :class="deltaClass(refN, results[idx]?.tensionLbs ?? 0)">
                  {{ formatDelta(refN, results[idx]?.tensionLbs ?? 0) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>
    </div>

    <!-- Physics footnote -->
    <div class="stp-footnote">
      T = UW × (2LF)² / 386.4 · steel ρ=0.2836 · nylon ρ=0.0412 lb/in³ · wound UW: D'Addario ref ·
      validated µ: Achilles 2000 (Physics 398 EMI, UIUC)
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useTension } from './useTension'
import { useBreakAngle } from './useBreakAngle'
import { INSTRUMENT_TYPES, MATERIALS } from './types'
import type { TensionUnit, StringMaterial, NoteName } from './types'

// ============================================================================
// COMPOSABLES
// ============================================================================

const tension = useTension()
const {
  instrumentType,
  globalScaleLength,
  multiScale,
  unit,
  strings,
  results,
  setAnalysis,
  breakAngleAdequacy,
  useCarruthThresholds,
  activePresetId,
  formatTension,
  formatTensionAlt,
  loadPreset,
  updateString,
  addString,
  removeString,
  setBreakAngle,
  noteNames,
  presets,
} = tension

const breakAngle = useBreakAngle(useCarruthThresholds)

// ============================================================================
// PRESET CATEGORIES
// ============================================================================

const PRESET_CATEGORIES = [
  { id: 'all',       label: 'All' },
  { id: 'guitar',    label: 'Guitar / Bass' },
  { id: 'mando',     label: 'Mando / Lute' },
  { id: 'uke',       label: 'Uke / Banjo' },
  { id: 'folk',      label: 'Folk' },
  { id: 'orch',      label: 'Orchestral' },
  { id: 'validated', label: 'Validated ‡' },
] as const

type PresetCat = typeof PRESET_CATEGORIES[number]['id']
const activeCat = ref<PresetCat>('all')

const visiblePresets = computed(() =>
  activeCat.value === 'all'
    ? presets
    : presets.filter(p => p.category === activeCat.value)
)

const activePreset = computed(() => presets.find(p => p.id === activePresetId.value))

// ============================================================================
// BREAK ANGLE SYNC
// ============================================================================

function syncBreakAngle(): void {
  setBreakAngle(breakAngle.manualDeg.value, false)
}

async function computeBreakAngle(): Promise<void> {
  await breakAngle.fetchBreakAngle()
  if (breakAngle.resolved.value.deg) {
    setBreakAngle(breakAngle.resolved.value.deg, true)
  }
}

// Keep useTension in sync when break angle resolves
watch(() => breakAngle.resolved.value.deg, (deg) => {
  setBreakAngle(deg, breakAngle.mode.value === 'computed')
})

// Reset break angle mode when instrument type changes
watch(instrumentType, () => {
  breakAngle.resetToManual()
  setBreakAngle(tension.instrumentTypeInfo.value.defaultBreakAngleDeg, false)
  breakAngle.manualDeg.value = tension.instrumentTypeInfo.value.defaultBreakAngleDeg
})

// ============================================================================
// DISPLAY HELPERS
// ============================================================================

const hasOverrides = computed(() => results.value.some(r => r.isOverride))

const maxTension = computed(() => Math.max(...results.value.map(r => r.tensionLbs), 1))

function barWidth(lbs: number): number {
  return Math.min(100, (lbs / (maxTension.value * 1.05)) * 100)
}

function tensionColor(lbs: number): string {
  if (lbs < 8)  return '#378ADD'
  if (lbs < 15) return '#1D9E75'
  if (lbs < 22) return '#BA7517'
  if (lbs < 30) return '#D85A30'
  return '#E24B4A'
}

function balanceColor(score: number): string {
  if (score > 0.82) return '#1D9E75'
  if (score > 0.65) return '#BA7517'
  return '#E24B4A'
}

function balanceLabel(score: number): string {
  if (score > 0.82) return 'Well balanced'
  if (score > 0.65) return 'Acceptable'
  return 'Unbalanced'
}

const breakAngleColor = computed(() => {
  const deg = breakAngle.resolved.value.deg
  if (deg >= 38) return '#E24B4A'
  if (useCarruthThresholds.value && deg < 6) return '#D85A30'
  return '#1D9E75'
})

// Validation table helpers
function formatValidationTension(refN: number): string {
  const refLbs = refN / 4.44822
  switch (unit.value) {
    case 'N':  return `${refN.toFixed(1)} N`
    case 'kg': return `${(refN / 9.80665).toFixed(2)} kg`
    default:   return `${refLbs.toFixed(2)} lb`
  }
}

function formatDelta(refN: number, calcLbs: number): string {
  const refLbs = refN / 4.44822
  const delta = ((calcLbs - refLbs) / refLbs) * 100
  return `${delta > 0 ? '+' : ''}${delta.toFixed(1)}%`
}

function deltaClass(refN: number, calcLbs: number): string {
  const refLbs = refN / 4.44822
  const delta = Math.abs(((calcLbs - refLbs) / refLbs) * 100)
  if (delta < 3) return 'stp-delta--ok'
  if (delta < 8) return 'stp-delta--warn'
  return 'stp-delta--bad'
}
</script>

<style scoped>
.stp { font-family: var(--font-sans, system-ui); padding: 4px 0; }

/* Toolbar */
.stp-toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; background: var(--color-background-secondary); border-radius: var(--border-radius-md); padding: 7px 12px; margin-bottom: 10px; }
.stp-field-group { display: flex; align-items: center; gap: 5px; }
.stp-label { font-size: 12px; color: var(--color-text-secondary); white-space: nowrap; }
.stp-select { font-size: 12px; padding: 3px 6px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-primary); font-family: inherit; }
.stp-input { font-size: 12px; padding: 3px 5px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-primary); font-family: var(--font-mono, monospace); }
.stp-input--narrow { width: 64px; }
.stp-unit { font-size: 12px; color: var(--color-text-secondary); }
.stp-toggle { font-size: 12px; padding: 3px 9px; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-secondary); cursor: pointer; font-family: inherit; }
.stp-toggle--on { background: var(--color-background-warning); color: var(--color-text-warning); border-color: var(--color-border-warning); }
.stp-unit-group { display: flex; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); overflow: hidden; margin-left: auto; }
.stp-unit-btn { font-size: 12px; padding: 3px 9px; background: transparent; border: none; color: var(--color-text-secondary); cursor: pointer; font-family: inherit; }
.stp-unit-btn--on { background: var(--color-background-warning); color: var(--color-text-warning); }

/* Preset bar */
.stp-preset-bar { margin-bottom: 10px; }
.stp-cat-tabs { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 6px; }
.stp-cat-tab { font-size: 11px; padding: 2px 9px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: transparent; color: var(--color-text-tertiary); cursor: pointer; font-family: inherit; }
.stp-cat-tab--on { background: var(--color-background-tertiary); color: var(--color-text-primary); border-color: var(--color-border-secondary); }
.stp-cat-tab--valid { border-color: #1D9E75; color: #1D9E75; }
.stp-cat-tab--valid.stp-cat-tab--on { background: #E1F5EE; color: #085041; }
.stp-presets { display: flex; gap: 5px; flex-wrap: wrap; }
.stp-preset-btn { font-size: 12px; padding: 3px 10px; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-secondary); cursor: pointer; font-family: inherit; white-space: nowrap; }
.stp-preset-btn--on { background: var(--color-background-warning); color: var(--color-text-warning); border-color: var(--color-border-warning); }
.stp-preset-btn--valid { border-color: #1D9E75; }
.stp-preset-btn--valid.stp-preset-btn--on { background: #E1F5EE; color: #085041; border-color: #1D9E75; }

/* Body layout */
.stp-body { display: grid; grid-template-columns: 1fr 256px; gap: 12px; align-items: start; }
@media (max-width: 700px) { .stp-body { grid-template-columns: 1fr; } }

/* Table */
.stp-table-wrap { border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-lg); overflow: hidden; overflow-x: auto; }
.stp-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.stp-table th { font-size: 10px; font-weight: 500; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.04em; padding: 5px 7px; text-align: left; background: var(--color-background-secondary); border-bottom: 0.5px solid var(--color-border-tertiary); white-space: nowrap; }
.stp-table td { padding: 3px 7px; border-bottom: 0.5px solid var(--color-border-tertiary); vertical-align: middle; }
.stp-row:last-child td { border-bottom: none; }
.stp-row:hover td { background: var(--color-background-secondary); }
.stp-dot { width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #fff; flex-shrink: 0; }
.stp-cell-select { font-size: 11px; padding: 2px 3px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-primary); width: 100%; font-family: inherit; }
.stp-cell-input { font-size: 11px; padding: 2px 4px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-primary); width: 100%; font-family: var(--font-mono, monospace); }
.stp-cell-input--override { color: var(--color-text-tertiary); }
.stp-bar-track { height: 4px; background: var(--color-background-tertiary); border-radius: 2px; overflow: hidden; min-width: 40px; }
.stp-bar-track--thick { height: 5px; }
.stp-bar-fill { height: 100%; border-radius: 2px; transition: width .25s, background .25s; }
.stp-value { text-align: right; font-family: var(--font-mono, monospace); font-size: 11px; font-weight: 500; white-space: nowrap; }
.stp-remove-btn { background: none; border: none; color: var(--color-text-tertiary); cursor: pointer; font-size: 14px; padding: 0 2px; line-height: 1; }
.stp-remove-btn:hover { color: var(--color-text-danger, #E24B4A); }
.stp-table-footer { display: flex; align-items: center; gap: 12px; padding: 6px 10px; background: var(--color-background-secondary); }
.stp-add-btn { font-size: 12px; padding: 2px 10px; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-secondary); cursor: pointer; font-family: inherit; }
.stp-override-note { font-size: 10px; color: var(--color-text-tertiary); }

/* Side panel cards */
.stp-side { display: flex; flex-direction: column; gap: 8px; }
.stp-card { background: var(--color-background-secondary); border-radius: var(--border-radius-md); padding: 10px 12px; }
.stp-card--valid { border: 0.5px solid #1D9E75; }
.stp-card-label { font-size: 10px; font-weight: 500; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 5px; }
.stp-card-label--green { color: #1D9E75; }
.stp-card-value { font-family: var(--font-mono, monospace); font-size: 19px; font-weight: 500; }
.stp-card-value--amber { color: #BA7517; }
.stp-card-sub { font-size: 11px; color: var(--color-text-secondary); margin-top: 2px; }
.stp-balance-row { display: flex; align-items: center; gap: 9px; margin-top: 2px; }
.stp-balance-label { font-size: 12px; font-weight: 500; }
.stp-stat-row { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 0.5px solid var(--color-border-tertiary); font-size: 11px; }
.stp-stat-row:last-child { border-bottom: none; }
.stp-stat-key { color: var(--color-text-secondary); }
.stp-stat-val { font-family: var(--font-mono, monospace); font-size: 11px; font-weight: 500; }
.stp-stat-val--blue { color: #378ADD; }
.stp-stat-val--muted { color: var(--color-text-tertiary); }
.stp-mono { font-family: var(--font-mono, monospace); }
.stp-uw-dagger { color: var(--color-text-tertiary); }
.stp-uw-note { font-size: 9px; font-weight: 400; text-transform: none; margin-left: 4px; }

/* Break angle */
.stp-break-angle { border-top: 0.5px solid var(--color-border-tertiary); margin-top: 8px; padding-top: 8px; }
.stp-break-angle-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.stp-mode-pills { display: flex; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); overflow: hidden; }
.stp-pill { font-size: 10px; padding: 2px 7px; background: transparent; border: none; color: var(--color-text-secondary); cursor: pointer; font-family: inherit; }
.stp-pill--on { background: var(--color-background-warning); color: var(--color-text-warning); }
.stp-break-manual { display: flex; align-items: center; gap: 5px; margin-bottom: 4px; }
.stp-manual-badge { font-size: 9px; color: var(--color-text-tertiary); border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); padding: 1px 5px; }
.stp-break-computed { display: flex; flex-direction: column; gap: 5px; }
.stp-break-field { display: flex; flex-direction: column; gap: 2px; }
.stp-break-label { font-size: 10px; color: var(--color-text-secondary); }
.stp-compute-btn { font-size: 12px; padding: 4px 10px; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-secondary); cursor: pointer; font-family: inherit; margin-top: 2px; }
.stp-compute-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.stp-break-error { font-size: 11px; color: var(--color-text-danger, #E24B4A); margin-top: 3px; }
.stp-break-result { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.stp-break-deg { font-family: var(--font-mono, monospace); font-size: 16px; font-weight: 500; }
.stp-break-status { font-size: 11px; font-weight: 500; }
.stp-carruth-note { font-size: 10px; color: var(--color-text-tertiary); margin-top: 5px; display: flex; align-items: center; gap: 6px; }
.stp-carruth-badge { font-size: 9px; padding: 1px 6px; border-radius: var(--border-radius-md); font-weight: 500; }
.stp-carruth-badge--adequate { background: #E1F5EE; color: #085041; }
.stp-carruth-badge--too_shallow { background: #FAECE7; color: #4A1B0C; }
.stp-carruth-badge--too_steep { background: #FCEBEB; color: #501313; }
.stp-flag { font-size: 10px; padding: 4px 6px; border-radius: var(--border-radius-md); margin-top: 3px; line-height: 1.4; }
.stp-flag--info { background: var(--color-background-info); color: var(--color-text-info); }
.stp-flag--warning { background: var(--color-background-warning); color: var(--color-text-warning); }
.stp-flag--critical { background: var(--color-background-danger); color: var(--color-text-danger); }
.stp-debt-notice { font-size: 9px; color: var(--color-text-tertiary); margin-top: 4px; font-style: italic; }

/* Validated comparison table */
.stp-valid-note { font-size: 10px; color: var(--color-text-secondary); margin-bottom: 6px; line-height: 1.5; }
.stp-valid-table { width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 4px; }
.stp-valid-table th { font-size: 9px; font-weight: 500; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.03em; padding: 3px 4px; border-bottom: 0.5px solid var(--color-border-tertiary); }
.stp-valid-table td { padding: 3px 4px; border-bottom: 0.5px solid var(--color-border-tertiary); font-family: var(--font-mono, monospace); }
.stp-valid-table tr:last-child td { border-bottom: none; }
.stp-delta--ok { color: #1D9E75; }
.stp-delta--warn { color: #BA7517; }
.stp-delta--bad { color: #E24B4A; }

/* Footnote */
.stp-footnote { margin-top: 8px; font-family: var(--font-mono, monospace); font-size: 10px; color: var(--color-text-tertiary); text-align: center; line-height: 1.8; }
</style>
