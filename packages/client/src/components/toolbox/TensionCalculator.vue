<script setup lang="ts">
/**
 * TensionCalculator - Standalone string tension calculator for Calculator Hub
 * Wraps TensionCalculatorPanel with state management
 */
import { ref, computed } from 'vue'
import TensionCalculatorPanel from './scale-length/TensionCalculatorPanel.vue'

interface StringData {
  name: string
  gauge: number
  note: string
  freq: number
}

const GAUGE_SETS: Record<string, number[]> = {
  light: [0.009, 0.011, 0.016, 0.024, 0.032, 0.042],
  regular: [0.010, 0.013, 0.017, 0.026, 0.036, 0.046],
  medium: [0.011, 0.014, 0.018, 0.028, 0.038, 0.049],
  heavy: [0.012, 0.016, 0.020, 0.032, 0.042, 0.053],
  baritone: [0.013, 0.017, 0.026, 0.036, 0.046, 0.062]
}

const STRING_NOTES = [
  { name: 'E (1st)', note: 'E4', freq: 329.63 },
  { name: 'B (2nd)', note: 'B3', freq: 246.94 },
  { name: 'G (3rd)', note: 'G3', freq: 196.00 },
  { name: 'D (4th)', note: 'D3', freq: 146.83 },
  { name: 'A (5th)', note: 'A2', freq: 110.00 },
  { name: 'E (6th)', note: 'E2', freq: 82.41 }
]

const customScale = ref(25.5)
const scaleUnit = ref<'in' | 'mm'>('in')

const strings = ref<StringData[]>(
  STRING_NOTES.map((s, i) => ({
    ...s,
    gauge: GAUGE_SETS.regular[i]
  }))
)

function calculateTension(idx: number): number {
  const s = strings.value[idx]
  if (!s) return 0
  const scale = scaleUnit.value === 'mm' ? customScale.value / 25.4 : customScale.value
  const mu = Math.pow(s.gauge, 2) * 0.000037
  return Math.round((mu * Math.pow(2 * scale * s.freq, 2)) / 4 * 10) / 10
}

const stringTensions = computed(() => strings.value.map((_, i) => calculateTension(i)))

const totalTension = computed(() =>
  stringTensions.value.reduce((sum, t) => sum + t, 0)
)

const averageTension = computed(() =>
  strings.value.length > 0 ? totalTension.value / strings.value.length : 0
)

const tensionRange = computed(() => {
  const tensions = stringTensions.value
  if (tensions.length === 0) return 0
  return Math.max(...tensions) - Math.min(...tensions)
})

function updateCustomScale(value: number) {
  customScale.value = value
}

function updateScaleUnit(value: 'in' | 'mm') {
  scaleUnit.value = value
}

function updateStringGauge(index: number, gauge: number) {
  if (strings.value[index]) {
    strings.value[index].gauge = gauge
  }
}

function applyGaugeSet(set: string) {
  const gauges = GAUGE_SETS[set]
  if (!gauges) return
  strings.value = STRING_NOTES.map((s, i) => ({
    ...s,
    gauge: gauges[i] || gauges[gauges.length - 1]
  }))
}
</script>

<template>
  <div class="tension-calculator-wrapper">
    <TensionCalculatorPanel
      :custom-scale="customScale"
      :scale-unit="scaleUnit"
      :strings="strings"
      :total-tension="totalTension"
      :average-tension="averageTension"
      :tension-range="tensionRange"
      @update:custom-scale="updateCustomScale"
      @update:scale-unit="updateScaleUnit"
      @update-string-gauge="updateStringGauge"
      @apply-gauge-set="applyGaugeSet"
    />
  </div>
</template>

<style scoped>
.tension-calculator-wrapper {
  padding: 1.5rem;
  background: #1e1e1e;
  min-height: 100%;
}
</style>
