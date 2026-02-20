<script setup lang="ts">
/**
 * TensionCalculatorPanel - String tension calculator for scale length design
 * Extracted from ScaleLengthDesigner.vue
 */
import styles from "./TensionCalculatorPanel.module.css";

interface StringData {
  name: string
  gauge: number
  note: string
  freq: number
}

const props = defineProps<{
  customScale: number
  scaleUnit: 'in' | 'mm'
  strings: StringData[]
  totalTension: number
  averageTension: number
  tensionRange: number
}>()

const emit = defineEmits<{
  'update:customScale': [value: number]
  'update:scaleUnit': [value: 'in' | 'mm']
  'updateStringGauge': [index: number, gauge: number]
  'applyGaugeSet': [set: string]
}>()

function calculateTension(idx: number): number {
  // Simplified tension calculation: T = (μ × (2 × L × f)²) / 4
  // This is a placeholder - actual calculation should use composable
  const s = props.strings[idx]
  if (!s) return 0
  const scale = props.scaleUnit === 'mm' ? props.customScale / 25.4 : props.customScale
  const mu = Math.pow(s.gauge, 2) * 0.000037 // Approximate linear density
  return Math.round((mu * Math.pow(2 * scale * s.freq, 2)) / 4 * 10) / 10
}

function getTensionClass(tension: number): string {
  if (tension < 13) return styles.tooLoose
  if (tension > 16) return styles.tooTight
  return styles.good
}
</script>

<template>
  <div :class="styles.tensionCalculator">
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
              @input="emit('update:customScale', Number(($event.target as HTMLInputElement).value))"
            >
            <select
              :value="scaleUnit"
              @change="emit('update:scaleUnit', ($event.target as HTMLSelectElement).value as 'in' | 'mm')"
            >
              <option value="in">inches</option>
              <option value="mm">mm</option>
            </select>
          </div>
        </div>

        <div :class="styles.stringInputs">
          <h3>String Gauges (inches)</h3>
          <div
            v-for="(s, idx) in strings"
            :key="idx"
            :class="styles.stringRow"
          >
            <div :class="styles.stringLabel">{{ s.name }}</div>
            <input
              :value="s.gauge"
              type="number"
              step="0.001"
              min="0.008"
              max="0.070"
              @input="emit('updateStringGauge', idx, Number(($event.target as HTMLInputElement).value))"
            >
            <div :class="styles.stringFreq">{{ s.note }} ({{ s.freq }} Hz)</div>
            <div :class="[styles.stringTension, getTensionClass(calculateTension(idx))]">
              {{ calculateTension(idx).toFixed(1) }} lbs
            </div>
          </div>
        </div>

        <div :class="styles.presetGauges">
          <button
            :class="styles.btnGauge"
            @click="emit('applyGaugeSet', 'light')"
          >
            Light (.009-.042)
          </button>
          <button
            :class="styles.btnGauge"
            @click="emit('applyGaugeSet', 'regular')"
          >
            Regular (.010-.046)
          </button>
          <button
            :class="styles.btnGauge"
            @click="emit('applyGaugeSet', 'medium')"
          >
            Medium (.011-.049)
          </button>
          <button
            :class="styles.btnGauge"
            @click="emit('applyGaugeSet', 'heavy')"
          >
            Heavy (.012-.053)
          </button>
          <button
            :class="styles.btnGauge"
            @click="emit('applyGaugeSet', 'baritone')"
          >
            Baritone (.013-.062)
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
        <div :class="[styles.guideRow, styles.guideRowTooLoose]">
          <div :class="styles.guideIndicator" />
          <div :class="styles.guideText">
            <strong>Too Loose (&lt; 13 lbs):</strong> Floppy feel, poor intonation, fret buzz
          </div>
        </div>
        <div :class="[styles.guideRow, styles.guideRowGood]">
          <div :class="styles.guideIndicator" />
          <div :class="styles.guideText">
            <strong>Good (13-16 lbs):</strong> Comfortable, balanced, stable tuning
          </div>
        </div>
        <div :class="[styles.guideRow, styles.guideRowTooTight]">
          <div :class="styles.guideIndicator" />
          <div :class="styles.guideText">
            <strong>Too Tight (&gt; 16 lbs):</strong> Hard to bend, high action required
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

