<template>
  <div class="tab-content">
    <div class="section-header">
      <h2>String Tension Calculator</h2>
      <p>Calculate tension for custom scale lengths and string gauges</p>
    </div>

    <div class="calculator-section">
      <div class="calc-inputs">
        <div class="input-group">
          <label>Scale Length</label>
          <div class="input-with-unit">
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

        <div class="string-inputs">
          <h3>String Gauges (inches)</h3>
          <div
            v-for="(string, idx) in strings"
            :key="idx"
            class="string-row"
          >
            <div class="string-label">{{ string.name }}</div>
            <input
              :value="string.gauge"
              type="number"
              step="0.001"
              min="0.008"
              max="0.070"
              @input="$emit('updateGauge', idx, Number(($event.target as HTMLInputElement).value))"
            >
            <div class="string-freq">{{ string.note }} ({{ string.freq }} Hz)</div>
            <div class="string-tension" :class="getTensionClass(getTension(idx))">
              {{ getTension(idx).toFixed(1) }} lbs
            </div>
          </div>
        </div>

        <div class="preset-gauges">
          <button
            v-for="gauge in gaugePresets"
            :key="gauge.id"
            class="btn-gauge"
            @click="$emit('applyGaugeSet', gauge.id)"
          >
            {{ gauge.label }}
          </button>
        </div>
      </div>

      <div class="tension-summary">
        <div class="summary-card">
          <div class="summary-label">Total Tension</div>
          <div class="summary-value">{{ totalTension.toFixed(1) }} lbs</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Average per String</div>
          <div class="summary-value">{{ averageTension.toFixed(1) }} lbs</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Tension Range</div>
          <div class="summary-value">{{ tensionRange.toFixed(1) }} lbs</div>
        </div>
      </div>

      <div class="tension-guide">
        <h3>Tension Guidelines</h3>
        <div class="guide-row too-loose">
          <div class="guide-indicator" />
          <div class="guide-text">
            <strong>Too Loose (&lt; 13 lbs):</strong> Floppy feel, poor intonation, fret buzz
          </div>
        </div>
        <div class="guide-row good">
          <div class="guide-indicator" />
          <div class="guide-text">
            <strong>Good (13-16 lbs):</strong> Comfortable, balanced, stable tuning
          </div>
        </div>
        <div class="guide-row too-tight">
          <div class="guide-indicator" />
          <div class="guide-text">
            <strong>Too Tight (&gt; 16 lbs):</strong> Hard to bend, high action required
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
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

<style scoped>
.tab-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-header {
  margin-bottom: 24px;
}

.section-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 8px;
}

.section-header p {
  font-size: 14px;
  color: #9aa0a6;
}

.calculator-section {
  max-width: 900px;
}

.calc-inputs {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.input-group {
  margin-bottom: 24px;
}

.input-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #e8eaed;
  margin-bottom: 8px;
}

.input-with-unit {
  display: flex;
  gap: 8px;
}

.input-with-unit input {
  flex: 1;
  background: #3c4043;
  border: 1px solid #5f6368;
  color: #e8eaed;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 16px;
}

.input-with-unit select {
  background: #3c4043;
  border: 1px solid #5f6368;
  color: #e8eaed;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.string-inputs h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 12px;
}

.string-row {
  display: grid;
  grid-template-columns: 100px 80px 1fr 100px;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
}

.string-label {
  font-size: 14px;
  font-weight: 500;
  color: #e8eaed;
}

.string-row input {
  background: #3c4043;
  border: 1px solid #5f6368;
  color: #e8eaed;
  padding: 8px;
  border-radius: 4px;
  font-size: 14px;
}

.string-freq {
  font-size: 13px;
  color: #9aa0a6;
}

.string-tension {
  font-size: 15px;
  font-weight: 600;
  text-align: center;
  padding: 6px;
  border-radius: 4px;
}

.tension-low {
  background: rgba(234, 67, 53, 0.2);
  color: #ff6b6b;
}

.tension-good {
  background: rgba(52, 168, 83, 0.2);
  color: #51cf66;
}

.tension-high {
  background: rgba(251, 188, 5, 0.2);
  color: #ffc107;
}

.preset-gauges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.btn-gauge {
  background: #3c4043;
  border: 1px solid #5f6368;
  color: #e8eaed;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-gauge:hover {
  background: #8ab4f8;
  color: #202124;
  border-color: #8ab4f8;
}

.tension-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  background: linear-gradient(135deg, #1a73e8 0%, #8ab4f8 100%);
  padding: 20px;
  border-radius: 12px;
  text-align: center;
}

.summary-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 8px;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  color: #fff;
}

.tension-guide {
  background: #292a2d;
  padding: 20px;
  border-radius: 12px;
}

.tension-guide h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 16px;
}

.guide-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px;
  border-radius: 8px;
}

.guide-row.too-loose { background: rgba(234, 67, 53, 0.1); }
.guide-row.good { background: rgba(52, 168, 83, 0.1); }
.guide-row.too-tight { background: rgba(251, 188, 5, 0.1); }

.guide-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.guide-row.too-loose .guide-indicator { background: #ff6b6b; }
.guide-row.good .guide-indicator { background: #51cf66; }
.guide-row.too-tight .guide-indicator { background: #ffc107; }

.guide-text {
  font-size: 13px;
  line-height: 1.5;
  color: #e8eaed;
}

.guide-text strong {
  color: #8ab4f8;
}

@media (max-width: 768px) {
  .string-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  .string-label {
    font-weight: 600;
  }
  .tension-summary {
    grid-template-columns: 1fr;
  }
}
</style>
