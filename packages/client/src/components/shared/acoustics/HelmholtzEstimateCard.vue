<script setup lang="ts">
/**
 * HelmholtzEstimateCard — First-order Helmholtz estimate helper
 *
 * Dev Order 27: First Phase-3B acoustic calculation.
 * Estimate helper, not calibrated prediction.
 */
import { ref, computed, watch } from 'vue'
import { GateBadge } from '@/components/shared/workflow'
import type { ApertureGeometryLike, AcousticState } from '@/types/acoustics'
import type { HelmholtzEstimateResult } from '@/types/helmholtz'
import { estimateHelmholtzFrequency, getDefaultSpeedOfSound } from '@/utils/acoustics/helmholtzEstimate'

const props = defineProps<{
  label: string
  apertureGeometry: ApertureGeometryLike | null
  acousticState: AcousticState | null
}>()

const emit = defineEmits<{
  'attach-estimate': [result: HelmholtzEstimateResult, volumeLiters: number, effectiveLengthMm: number]
}>()

const volumeLiters = ref<number | undefined>(undefined)
const effectiveLengthMm = ref<number | undefined>(undefined)
const speedOfSoundMps = ref<number>(getDefaultSpeedOfSound())

const currentEstimate = ref<HelmholtzEstimateResult | null>(null)

const areaFromGeometry = computed(() => props.apertureGeometry?.area_mm2 ?? null)

const existingEstimate = computed(() => props.acousticState?.estimatedHelmholtzHz ?? null)

const canEstimate = computed(() => {
  return (
    areaFromGeometry.value !== null &&
    areaFromGeometry.value > 0 &&
    volumeLiters.value !== undefined &&
    volumeLiters.value > 0 &&
    effectiveLengthMm.value !== undefined &&
    effectiveLengthMm.value > 0 &&
    speedOfSoundMps.value > 0
  )
})

watch(
  () => props.acousticState?.bodyVolumeLiters,
  (newVal) => {
    if (newVal !== undefined && volumeLiters.value === undefined) {
      volumeLiters.value = newVal
    }
  },
  { immediate: true }
)

watch(
  () => props.acousticState?.estimatedEffectiveLengthMm,
  (newVal) => {
    if (newVal !== undefined && effectiveLengthMm.value === undefined) {
      effectiveLengthMm.value = newVal
    }
  },
  { immediate: true }
)

function runEstimate() {
  if (!canEstimate.value || areaFromGeometry.value === null) return

  const result = estimateHelmholtzFrequency({
    areaMm2: areaFromGeometry.value,
    volumeLiters: volumeLiters.value!,
    effectiveLengthMm: effectiveLengthMm.value!,
    speedOfSoundMps: speedOfSoundMps.value,
  })

  currentEstimate.value = result
}

function attachEstimate() {
  if (!currentEstimate.value || volumeLiters.value === undefined || effectiveLengthMm.value === undefined) return
  emit('attach-estimate', currentEstimate.value, volumeLiters.value, effectiveLengthMm.value)
}

function clearEstimate() {
  currentEstimate.value = null
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">{{ label }}</span>
      <GateBadge gate="yellow" label="Helper" />
    </div>

    <!-- Warning banner -->
    <div :class="$style.warningBanner">
      First-order Helmholtz estimate only. Not calibrated prediction.
    </div>

    <!-- Existing estimate display -->
    <div v-if="existingEstimate !== null" :class="$style.existingEstimate">
      <span :class="$style.existingLabel">Current attached estimate:</span>
      <span :class="$style.existingValue">{{ existingEstimate.toFixed(1) }} Hz</span>
    </div>

    <!-- Input section -->
    <div :class="$style.inputSection">
      <div :class="$style.inputRow">
        <label :class="$style.inputLabel">
          Aperture Area (mm²)
          <span :class="$style.fromGeometry">(from geometry)</span>
        </label>
        <input
          type="text"
          :value="areaFromGeometry !== null ? areaFromGeometry.toFixed(1) : '—'"
          disabled
          :class="$style.inputDisabled"
        />
      </div>

      <div :class="$style.inputRow">
        <label :class="$style.inputLabel">Body Volume (liters)</label>
        <input
          v-model.number="volumeLiters"
          type="number"
          step="0.1"
          min="0"
          placeholder="e.g. 15"
          :class="$style.input"
          @input="clearEstimate"
        />
      </div>

      <div :class="$style.inputRow">
        <label :class="$style.inputLabel">Effective Length (mm)</label>
        <input
          v-model.number="effectiveLengthMm"
          type="number"
          step="1"
          min="0"
          placeholder="e.g. 20"
          :class="$style.input"
          @input="clearEstimate"
        />
      </div>

      <div :class="$style.inputRow">
        <label :class="$style.inputLabel">Speed of Sound (m/s)</label>
        <input
          v-model.number="speedOfSoundMps"
          type="number"
          step="1"
          min="0"
          :class="$style.input"
          @input="clearEstimate"
        />
      </div>
    </div>

    <!-- Estimate button -->
    <button
      :disabled="!canEstimate"
      :class="[$style.button, $style.estimateButton]"
      @click="runEstimate"
    >
      Estimate Helmholtz
    </button>

    <!-- Estimate result -->
    <div v-if="currentEstimate" :class="$style.resultSection">
      <div :class="$style.resultHeader">
        <span :class="$style.resultLabel">Estimated Helmholtz Frequency</span>
        <span :class="$style.resultValue">{{ currentEstimate.estimatedHelmholtzHz.toFixed(1) }} Hz</span>
      </div>

      <div :class="$style.resultMeta">
        <span>Method: {{ currentEstimate.method }}</span>
        <span>Confidence: {{ currentEstimate.confidence }}</span>
      </div>

      <!-- Assumptions -->
      <div :class="$style.assumptions">
        <span :class="$style.assumptionsLabel">Assumptions:</span>
        <ul :class="$style.assumptionsList">
          <li v-for="(assumption, idx) in currentEstimate.assumptions" :key="idx">
            {{ assumption }}
          </li>
        </ul>
      </div>

      <!-- Warnings -->
      <div :class="$style.warnings">
        <span :class="$style.warningsLabel">Warnings:</span>
        <ul :class="$style.warningsList">
          <li v-for="(warning, idx) in currentEstimate.warnings" :key="idx">
            {{ warning }}
          </li>
        </ul>
      </div>

      <!-- Replace notice -->
      <div v-if="existingEstimate !== null" :class="$style.replaceNotice">
        Existing estimate will be replaced if you attach this result.
      </div>

      <!-- Attach button -->
      <button
        :class="[$style.button, $style.attachButton]"
        @click="attachEstimate"
      >
        {{ existingEstimate !== null ? 'Attach / Replace Estimate' : 'Attach to Acoustic State' }}
      </button>
    </div>

    <!-- Info notice -->
    <div :class="$style.infoNotice">
      This estimate does not include two-cavity coupling, modal interaction, tornavoz effects, or measured calibration.
    </div>
  </div>
</template>

<style module>
.card {
  background: #111827;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  padding: 0.75rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #374151;
}

.label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #f9fafb;
}

.warningBanner {
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 0.25rem;
  padding: 0.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.75rem;
  color: #fbbf24;
  font-weight: 500;
  text-align: center;
}

.existingEstimate {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.375rem 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
  font-size: 0.75rem;
}

.existingLabel {
  color: #9ca3af;
}

.existingValue {
  color: #818cf8;
  font-weight: 600;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.inputSection {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.inputRow {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.inputLabel {
  font-size: 0.6875rem;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.fromGeometry {
  color: #6b7280;
  font-style: italic;
  text-transform: none;
  letter-spacing: normal;
}

.input {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  padding: 0.375rem 0.5rem;
  font-size: 0.8125rem;
  color: #f9fafb;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.input:focus {
  outline: none;
  border-color: #6366f1;
}

.inputDisabled {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  padding: 0.375rem 0.5rem;
  font-size: 0.8125rem;
  color: #6b7280;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.button {
  width: 100%;
  padding: 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.estimateButton {
  background: #374151;
  border: 1px solid #4b5563;
  color: #f9fafb;
}

.estimateButton:hover:not(:disabled) {
  background: #4b5563;
}

.resultSection {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 0.25rem;
}

.resultHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.resultLabel {
  font-size: 0.75rem;
  color: #9ca3af;
}

.resultValue {
  font-size: 1.125rem;
  font-weight: 600;
  color: #10b981;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.resultMeta {
  display: flex;
  gap: 1rem;
  font-size: 0.6875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.assumptions,
.warnings {
  margin-bottom: 0.5rem;
}

.assumptionsLabel,
.warningsLabel {
  font-size: 0.6875rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.assumptionsList,
.warningsList {
  margin: 0.25rem 0 0 1rem;
  padding: 0;
  font-size: 0.6875rem;
  color: #9ca3af;
}

.warningsList {
  color: #fbbf24;
}

.replaceNotice {
  font-size: 0.6875rem;
  color: #f59e0b;
  padding: 0.375rem 0.5rem;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.attachButton {
  background: #10b981;
  border: 1px solid #059669;
  color: #ffffff;
  margin-top: 0.5rem;
}

.attachButton:hover {
  background: #059669;
}

.infoNotice {
  margin-top: 0.75rem;
  font-size: 0.6875rem;
  color: #6b7280;
  font-style: italic;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
}
</style>
