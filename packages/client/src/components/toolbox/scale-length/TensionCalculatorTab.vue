<template>
  <div :class="styles.tabContent">
    <div :class="styles.sectionHeader">
      <h2>String Tension Calculator</h2>
      <p>Calculate tension for custom scale lengths and string gauges</p>
    </div>

    <div :class="styles.calculatorSection">
      <div :class="styles.calcInputs">
        <div :class="styles.inputGroup">
          <label>Scale Length</label>
          <div :class="styles.inputWithUnit">
            <input
              :value="customScale"
              type="number"
              step="0.25"
              min="20"
              max="30"
              @input="$emit('update:customScale', Number(($event.target as HTMLInputElement).value))"
            >
            <select
              :value="scaleUnit"
              @change="$emit('update:scaleUnit', ($event.target as HTMLSelectElement).value as 'in' | 'mm')"
            >
              <option value="in">inches</option>
              <option value="mm">mm</option>
            </select>
          </div>
        </div>

        <div :class="styles.stringInputs">
          <h3>String Gauges (inches)</h3>
          <div
            v-for="(string, idx) in strings"
            :key="idx"
            :class="styles.stringRow"
          >
            <div :class="styles.stringLabel">{{ string.name }}</div>
            <input
              :value="string.gauge"
              type="number"
              step="0.001"
              min="0.008"
              max="0.070"
              @input="$emit('updateGauge', idx, Number(($event.target as HTMLInputElement).value))"
            >
            <div :class="styles.stringFreq">{{ string.note }} ({{ string.freq }} Hz)</div>
            <div :class="[styles.stringTension, getTensionClass(getTension(idx))]">
              {{ getTension(idx).toFixed(1) }} lbs
            </div>
          </div>
        </div>

        <div :class="styles.presetGauges">
          <button
            v-for="gauge in gaugePresets"
            :key="gauge.id"
            :class="styles.btnGauge"
            @click="$emit('applyGaugeSet', gauge.id)"
          >
            {{ gauge.label }}
          </button>
        </div>
      </div>

      <div :class="styles.tensionSummary">
        <div :class="styles.summaryCard">
          <div :class="styles.summaryLabel">Total Tension</div>
          <div :class="styles.summaryValue">{{ totalTension.toFixed(1) }} lbs</div>
        </div>
        <div :class="styles.summaryCard">
          <div :class="styles.summaryLabel">Average per String</div>
          <div :class="styles.summaryValue">{{ averageTension.toFixed(1) }} lbs</div>
        </div>
        <div :class="styles.summaryCard">
          <div :class="styles.summaryLabel">Tension Range</div>
          <div :class="styles.summaryValue">{{ tensionRange.toFixed(1) }} lbs</div>
        </div>
      </div>

      <div :class="styles.tensionGuide">
        <h3>Tension Guidelines</h3>
        <div :class="styles.guideRowTooLoose">
          <div :class="styles.guideIndicator" />
          <div :class="styles.guideText">
            <strong>Too Loose (&lt; 13 lbs):</strong> Floppy feel, poor intonation, fret buzz
          </div>
        </div>
        <div :class="styles.guideRowGood">
          <div :class="styles.guideIndicator" />
          <div :class="styles.guideText">
            <strong>Good (13-16 lbs):</strong> Comfortable, balanced, stable tuning
          </div>
        </div>
        <div :class="styles.guideRowTooTight">
          <div :class="styles.guideIndicator" />
          <div :class="styles.guideText">
            <strong>Too Tight (&gt; 16 lbs):</strong> Hard to bend, high action required
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from "./TensionCalculatorTab.module.css";

export interface StringData {
  name: string
  gauge: number
  note: string
  freq: number
}

defineProps<{
  customScale: number
  scaleUnit: 'in' | 'mm'
  strings: StringData[]
  totalTension: number
  averageTension: number
  tensionRange: number
  getTension: (idx: number) => number
  getTensionClass: (tension: number) => string
}>()

defineEmits<{
  'update:customScale': [value: number]
  'update:scaleUnit': [value: 'in' | 'mm']
  'updateGauge': [idx: number, value: number]
  'applyGaugeSet': [setId: string]
}>()

const gaugePresets = [
  { id: 'light', label: 'Light (.009-.042)' },
  { id: 'regular', label: 'Regular (.010-.046)' },
  { id: 'medium', label: 'Medium (.011-.049)' },
  { id: 'heavy', label: 'Heavy (.012-.053)' },
  { id: 'baritone', label: 'Baritone (.013-.062)' }
]
</script>

