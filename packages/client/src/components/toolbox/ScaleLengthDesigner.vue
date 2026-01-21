<template>
  <div class="scale-designer">
    <!-- Header -->
    <div class="designer-header">
      <h1 class="designer-title">
        🎸 Scale Length Designer
      </h1>
      <p class="designer-subtitle">
        Educational tool for understanding guitar scale length physics, string tension, and intonation compensation
      </p>
    </div>

    <!-- Tab Navigation -->
    <div class="designer-tabs">
      <div 
        v-for="tab in tabs" 
        :key="tab.id"
        class="designer-tab" 
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </div>
    </div>

    <!-- Tab 1: Scale Length Presets & Education -->
    <div
      v-if="activeTab === 'presets'"
      class="tab-content"
    >
      <div class="section-header">
        <h2>Standard Scale Lengths</h2>
        <p>Click a card to explore how scale length affects string tension and tone</p>
      </div>

      <div class="scale-grid">
        <div
          class="scale-card"
          @click="selectScale('fender')"
        >
          <div class="scale-name">
            Fender Scale
          </div>
          <div class="scale-value">
            25.5" (648mm)
          </div>
          <div class="scale-info">
            <div class="scale-trait">
              • Bright, snappy tone
            </div>
            <div class="scale-trait">
              • Higher string tension
            </div>
            <div class="scale-trait">
              • Strat, Tele, Jazzmaster
            </div>
          </div>
        </div>

        <div
          class="scale-card"
          @click="selectScale('gibson')"
        >
          <div class="scale-name">
            Gibson Scale
          </div>
          <div class="scale-value">
            24.75" (629mm)
          </div>
          <div class="scale-info">
            <div class="scale-trait">
              • Warm, fat tone
            </div>
            <div class="scale-trait">
              • Easier bending
            </div>
            <div class="scale-trait">
              • Les Paul, SG, 335
            </div>
          </div>
        </div>

        <div
          class="scale-card"
          @click="selectScale('prs')"
        >
          <div class="scale-name">
            PRS Scale
          </div>
          <div class="scale-value">
            25.0" (635mm)
          </div>
          <div class="scale-info">
            <div class="scale-trait">
              • Balanced compromise
            </div>
            <div class="scale-trait">
              • Medium tension
            </div>
            <div class="scale-trait">
              • PRS core models
            </div>
          </div>
        </div>

        <div
          class="scale-card"
          @click="selectScale('short')"
        >
          <div class="scale-name">
            Short Scale
          </div>
          <div class="scale-value">
            24.0" (610mm)
          </div>
          <div class="scale-info">
            <div class="scale-trait">
              • Easy playability
            </div>
            <div class="scale-trait">
              • Lower tension
            </div>
            <div class="scale-trait">
              • Mustang, Jaguar
            </div>
          </div>
        </div>

        <div
          class="scale-card"
          @click="selectScale('baritone')"
        >
          <div class="scale-name">
            Baritone Scale
          </div>
          <div class="scale-value">
            27.0" (686mm)
          </div>
          <div class="scale-info">
            <div class="scale-trait">
              • Extended low range
            </div>
            <div class="scale-trait">
              • Tight low strings
            </div>
            <div class="scale-trait">
              • Drop A, B tuning
            </div>
          </div>
        </div>

        <div
          class="scale-card"
          @click="selectScale('multiscale')"
        >
          <div class="scale-name">
            Multi-Scale (Fanned)
          </div>
          <div class="scale-value">
            25.5" - 27.0"
          </div>
          <div class="scale-info">
            <div class="scale-trait">
              • Ergonomic fanned frets
            </div>
            <div class="scale-trait">
              • Optimized per string
            </div>
            <div class="scale-trait">
              • Modern innovation
            </div>
          </div>
        </div>
      </div>

      <!-- Why Scale Length Matters -->
      <div class="education-section">
        <div class="edu-title">
          💡 Why Scale Length Matters for Innovation
        </div>
        
        <div class="edu-card">
          <h3>The Physics: Mersenne's Law</h3>
          <p>String tension is determined by a precise mathematical relationship:</p>
          <div class="formula-box">
            <div class="formula">
              T = (μ × (2 × L × f)²) ÷ 4
            </div>
            <div class="formula-legend">
              <div><strong>T</strong> = Tension (lbs)</div>
              <div><strong>μ</strong> = Linear mass density (lb/in)</div>
              <div><strong>L</strong> = Scale length (in)</div>
              <div><strong>f</strong> = Frequency (Hz)</div>
            </div>
          </div>
          <p class="edu-note">
            <strong>Key insight:</strong> Tension increases with the <em>square</em> of scale length. 
            Every 0.75" longer scale = ~6% more tension!
          </p>
        </div>

        <div class="edu-card">
          <h3>Real-World Examples</h3>
          <div class="example-grid">
            <div class="example-item">
              <div class="example-scale">
                Gibson 24.75"
              </div>
              <div class="example-tension">
                14.2 lbs
              </div>
              <div class="example-note">
                High E string (.010")
              </div>
            </div>
            <div class="example-item">
              <div class="example-scale">
                PRS 25.0"
              </div>
              <div class="example-tension">
                14.5 lbs
              </div>
              <div class="example-note">
                +2.1% tension
              </div>
            </div>
            <div class="example-item">
              <div class="example-scale">
                Fender 25.5"
              </div>
              <div class="example-tension">
                15.1 lbs
              </div>
              <div class="example-note">
                +6.3% tension
              </div>
            </div>
          </div>
          <p class="edu-note">
            That 0.75" difference between Gibson and Fender creates noticeable feel and tone differences!
          </p>
        </div>
      </div>
    </div>

    <!-- Tab 2: Tension Calculator -->
    <div
      v-if="activeTab === 'tension'"
      class="tab-content"
    >
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
                v-model.number="customScale"
                type="number"
                step="0.25"
                min="20"
                max="30"
              >
              <select v-model="scaleUnit">
                <option value="in">
                  inches
                </option>
                <option value="mm">
                  mm
                </option>
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
              <div class="string-label">
                {{ string.name }}
              </div>
              <input
                v-model.number="string.gauge"
                type="number"
                step="0.001"
                min="0.008"
                max="0.070"
              >
              <div class="string-freq">
                {{ string.note }} ({{ string.freq }} Hz)
              </div>
              <div
                class="string-tension"
                :class="getTensionClass(calculateTension(idx))"
              >
                {{ calculateTension(idx).toFixed(1) }} lbs
              </div>
            </div>
          </div>

          <div class="preset-gauges">
            <button
              class="btn-gauge"
              @click="applyGaugeSet('light')"
            >
              Light (.009-.042)
            </button>
            <button
              class="btn-gauge"
              @click="applyGaugeSet('regular')"
            >
              Regular (.010-.046)
            </button>
            <button
              class="btn-gauge"
              @click="applyGaugeSet('medium')"
            >
              Medium (.011-.049)
            </button>
            <button
              class="btn-gauge"
              @click="applyGaugeSet('heavy')"
            >
              Heavy (.012-.053)
            </button>
            <button
              class="btn-gauge"
              @click="applyGaugeSet('baritone')"
            >
              Baritone (.013-.062)
            </button>
          </div>
        </div>

        <div class="tension-summary">
          <div class="summary-card">
            <div class="summary-label">
              Total Tension
            </div>
            <div class="summary-value">
              {{ totalTension.toFixed(1) }} lbs
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-label">
              Average per String
            </div>
            <div class="summary-value">
              {{ averageTension.toFixed(1) }} lbs
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-label">
              Tension Range
            </div>
            <div class="summary-value">
              {{ tensionRange.toFixed(1) }} lbs
            </div>
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

    <!-- Tab 3: Intonation Compensation -->
    <div
      v-if="activeTab === 'intonation'"
      class="tab-content"
    >
      <div class="section-header">
        <h2>Intonation Compensation</h2>
        <p>Understanding the "dead zone" and why bridges aren't placed at the exact scale length</p>
      </div>

      <div class="intonation-education">
        <div class="critical-concept">
          <h3>🔴 The Dead Zone Problem</h3>
          <p>
            String stiffness creates a non-vibrating "dead zone" near the saddle. This zone doesn't 
            contribute to pitch but adds effective length to the string, making it sharper than expected.
          </p>
          <p>
            <strong>The B string intonates closest to the design scale length</strong> because its 
            diameter and composition create the smallest dead zone. This is why the B string saddle 
            is used as the reference point for all other strings.
          </p>
        </div>

        <div class="compensation-table">
          <div class="comp-header">
            <div class="comp-title">
              Intonation Compensation Chart
            </div>
            <div class="comp-subtitle">
              For 25.5" scale (Fender) with standard .010-.046 gauges
            </div>
          </div>

          <div class="comp-grid">
            <div class="comp-row comp-header-row">
              <div>String</div>
              <div>Gauge</div>
              <div>Design Length</div>
              <div>Actual Length</div>
              <div>Compensation</div>
            </div>

            <div class="comp-row">
              <div>High E</div>
              <div>.010"</div>
              <div>25.500"</div>
              <div>25.500"</div>
              <div>0.000" (none)</div>
            </div>

            <div class="comp-row highlight-reference">
              <div>B</div>
              <div>.013"</div>
              <div>25.500"</div>
              <div>25.500"</div>
              <div>0.000" (reference)</div>
            </div>

            <div class="comp-row">
              <div>G</div>
              <div>.017"</div>
              <div>25.500"</div>
              <div>25.562"</div>
              <div>+0.062" (~1/16")</div>
            </div>

            <div class="comp-row">
              <div>D</div>
              <div>.026"</div>
              <div>25.500"</div>
              <div>25.625"</div>
              <div>+0.125" (1/8")</div>
            </div>

            <div class="comp-row">
              <div>A</div>
              <div>.036"</div>
              <div>25.500"</div>
              <div>25.687"</div>
              <div>+0.187" (3/16")</div>
            </div>

            <div class="comp-row highlight-max">
              <div>Low E</div>
              <div>.046"</div>
              <div>25.500"</div>
              <div>25.750"</div>
              <div>+0.250" (1/4")</div>
            </div>
          </div>
        </div>

        <div class="bridge-placement">
          <h3>Bridge Placement Formula</h3>
          <div class="placement-box">
            <div class="formula">
              Bridge Center = Scale Length + (Low E Compensation ÷ 2)
            </div>
            <div class="formula-example">
              Example: 25.5" + (0.25" ÷ 2) = <strong>25.625"</strong> from nut to bridge center
            </div>
          </div>
          <div class="placement-note warning">
            <strong>Common Mistake:</strong> Placing the bridge at exactly 25.5" from the nut. 
            This forces all saddles backward, limiting adjustment range and causing intonation issues.
          </div>
          <div class="placement-note success">
            <strong>Correct Approach:</strong> Place bridge center at scale + (max_comp ÷ 2), allowing 
            saddles to move both forward (high E, B) and backward (low E) for perfect intonation.
          </div>
        </div>

        <div class="compensation-factors">
          <h3>5 Physical Factors Affecting Compensation</h3>
          <div class="factor-list">
            <div class="factor-item">
              <strong>1. String Diameter</strong>
              <div>
                Thicker strings have more stiffness, creating larger dead zones. Low E (.046") needs 
                ~4× more compensation than High E (.010").
              </div>
            </div>
            <div class="factor-item">
              <strong>2. String Structure</strong>
              <div>
                Wound strings (G, D, A, Low E) have higher stiffness than plain strings (High E, B) 
                due to the wrap wire adding rigidity.
              </div>
            </div>
            <div class="factor-item">
              <strong>3. Core Wire Composition</strong>
              <div>
                Stainless steel cores are stiffer than nickel or phosphor bronze, requiring more 
                compensation. Material matters!
              </div>
            </div>
            <div class="factor-item">
              <strong>4. String Action Height</strong>
              <div>
                Higher action means more stretch when fretting, pulling the string sharper. Compensate 
                by moving saddles back further.
              </div>
            </div>
            <div class="factor-item">
              <strong>5. Fret Height</strong>
              <div>
                Tall frets (like jumbos) require more stretch to fret cleanly, increasing effective 
                length. Lower frets need less compensation.
              </div>
            </div>
          </div>
        </div>

        <div class="innovation-connection">
          <h3>🚀 Why Multi-Scale Guitars Excel at Intonation</h3>
          <p>
            Multi-scale (fanned fret) guitars optimize scale length independently for each string. 
            Treble strings get shorter scales (less tension, easier bending) while bass strings get 
            longer scales (more tension, better definition).
          </p>
          <p>
            <strong>Bonus:</strong> Longer bass scales reduce the percentage difference in compensation. 
            A 27" Low E needs +0.25" compensation (0.9% of scale) vs 25.5" needing +0.25" (1.0% of scale). 
            Tighter tolerances, better intonation!
          </p>
        </div>
      </div>
    </div>

    <!-- Tab 4: Multi-Scale Innovation -->
    <div
      v-if="activeTab === 'multiscale'"
      class="tab-content"
    >
      <div class="section-header">
        <h2>Multi-Scale (Fanned Fret) Innovation</h2>
        <p>Why modern guitars are moving beyond single scale lengths</p>
      </div>

      <div class="multiscale-education">
        <div class="problem-solution">
          <div class="problem-card">
            <h3>🔴 The Single-Scale Compromise</h3>
            <p>Traditional guitars force all strings to use the same scale length:</p>
            <ul>
              <li><strong>Treble strings:</strong> Higher tension than ideal (harder to bend)</li>
              <li><strong>Bass strings:</strong> Lower tension than ideal (less definition)</li>
              <li><strong>Result:</strong> Every string is a compromise</li>
            </ul>
            <div class="example">
              <strong>Example: Baritone at 25.5" scale</strong>
              <div class="calc-result problem">
                Low B string: 12.8 lbs (too floppy!)
              </div>
            </div>
          </div>

          <div class="solution-card">
            <h3>✅ The Multi-Scale Solution</h3>
            <p>Different scale length for each string, optimized independently:</p>
            <ul>
              <li><strong>Treble E:</strong> 25.5" (comfortable tension, easy bending)</li>
              <li><strong>Bass E:</strong> 27.0" (tight, defined, no flop)</li>
              <li><strong>Middle strings:</strong> Smoothly interpolated</li>
            </ul>
            <div class="example">
              <strong>Same baritone with multi-scale:</strong>
              <div class="calc-result solution">
                Low B string: 14.3 lbs (perfect!)
              </div>
            </div>
          </div>
        </div>

        <div class="multiscale-diagram">
          <h3>Visual: How Fanned Frets Work</h3>
          <div class="fret-visualization">
            <div class="fret-line treble">
              <div class="fret-label">
                Treble Side (High E)
              </div>
              <div class="fret-visual">
                |———————————————————| 25.5" scale
              </div>
              <div class="fret-tension">
                15.1 lbs tension
              </div>
            </div>
            <div class="fret-line bass">
              <div class="fret-label">
                Bass Side (Low E)
              </div>
              <div class="fret-visual">
                |—————————————————————————| 27.0" scale
              </div>
              <div class="fret-tension">
                14.8 lbs tension (with .046" gauge)
              </div>
            </div>
          </div>
          <p class="diagram-note">
            Notice how the bass side is longer. Frets are angled (fanned) to accommodate different 
            scale lengths. The 12th fret is typically placed at the ergonomic "neutral" position.
          </p>
        </div>

        <div class="tension-comparison">
          <h3>Tension Comparison: Single vs Multi-Scale</h3>
          <div class="comparison-table">
            <div class="comparison-header">
              <div>String</div>
              <div>Single 25.5"</div>
              <div>Multi (25.5"-27")</div>
              <div>Improvement</div>
            </div>
            <div class="comparison-row">
              <div>High E (.010")</div>
              <div>15.1 lbs</div>
              <div>15.1 lbs</div>
              <div class="neutral">
                Same
              </div>
            </div>
            <div class="comparison-row">
              <div>B (.013")</div>
              <div>15.2 lbs</div>
              <div>15.4 lbs</div>
              <div class="slight">
                +1.3%
              </div>
            </div>
            <div class="comparison-row">
              <div>G (.017")</div>
              <div>15.0 lbs</div>
              <div>15.6 lbs</div>
              <div class="good">
                +4%
              </div>
            </div>
            <div class="comparison-row">
              <div>D (.026")</div>
              <div>14.9 lbs</div>
              <div>16.0 lbs</div>
              <div class="good">
                +7.4%
              </div>
            </div>
            <div class="comparison-row">
              <div>A (.036")</div>
              <div>14.3 lbs</div>
              <div>15.8 lbs</div>
              <div class="excellent">
                +10.5%
              </div>
            </div>
            <div class="comparison-row">
              <div>Low E (.046")</div>
              <div>13.8 lbs</div>
              <div>15.7 lbs</div>
              <div class="excellent">
                +13.8%
              </div>
            </div>
          </div>
          <p class="comparison-note">
            Multi-scale dramatically improves bass string tension while keeping treble strings comfortable. 
            This is why extended-range guitars (7, 8, 9 strings) almost always use fanned frets.
          </p>
        </div>

        <div class="ergonomic-benefits">
          <h3>Ergonomic Benefits</h3>
          <div class="benefit-grid">
            <div class="benefit-card">
              <div class="benefit-icon">
                🤚
              </div>
              <div class="benefit-title">
                Natural Hand Position
              </div>
              <div class="benefit-text">
                Fanned frets follow the natural angle of your hand/wrist, reducing strain during 
                extended playing sessions.
              </div>
            </div>
            <div class="benefit-card">
              <div class="benefit-icon">
                🎯
              </div>
              <div class="benefit-title">
                Better Intonation
              </div>
              <div class="benefit-text">
                Longer bass scales reduce compensation percentage, making intonation more accurate 
                across the entire fretboard.
              </div>
            </div>
            <div class="benefit-card">
              <div class="benefit-icon">
                🔊
              </div>
              <div class="benefit-title">
                Balanced Tone
              </div>
              <div class="benefit-text">
                Each string has optimal tension for its frequency range, creating a more balanced 
                and articulate sound across all strings.
              </div>
            </div>
            <div class="benefit-card">
              <div class="benefit-icon">
                ⚡
              </div>
              <div class="benefit-title">
                Extended Range
              </div>
              <div class="benefit-text">
                Makes 7, 8, and 9-string guitars playable by ensuring low strings have enough tension 
                for clarity and definition.
              </div>
            </div>
          </div>
        </div>

        <div class="custom-scale-exploration">
          <h3>Custom Scale Exploration</h3>
          <p>
            Want to innovate? Consider a 24.9" hybrid scale: 
            <strong>slightly easier bending than Fender, slightly brighter than Gibson.</strong>
          </p>
          <p>
            Or go extreme: 28" baritone for drop G# tuning, 22" travel guitar for portability. 
            The math is your guide!
          </p>
          <button
            class="btn-explore"
            @click="activeTab = 'tension'"
          >
            Explore Custom Scales in Tension Calculator →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Tab management
const tabs = [
  { id: 'presets', label: 'Scale Presets' },
  { id: 'tension', label: 'Tension Calculator' },
  { id: 'intonation', label: 'Intonation' },
  { id: 'multiscale', label: 'Multi-Scale' }
]

const activeTab = ref('presets')

// Tension calculator state
const customScale = ref(25.5)
const scaleUnit = ref('in')

interface StringData {
  name: string
  note: string
  freq: number
  gauge: number
  linearDensity?: number // lb/in (calculated from gauge)
}

const strings = ref<StringData[]>([
  { name: 'High E', note: 'E4', freq: 329.63, gauge: 0.010 },
  { name: 'B', note: 'B3', freq: 246.94, gauge: 0.013 },
  { name: 'G', note: 'G3', freq: 196.00, gauge: 0.017 },
  { name: 'D', note: 'D3', freq: 146.83, gauge: 0.026 },
  { name: 'A', note: 'A2', freq: 110.00, gauge: 0.036 },
  { name: 'Low E', note: 'E2', freq: 82.41, gauge: 0.046 }
])

// Gauge presets
const gaugePresets: Record<string, number[]> = {
  light: [0.009, 0.011, 0.016, 0.024, 0.032, 0.042],
  regular: [0.010, 0.013, 0.017, 0.026, 0.036, 0.046],
  medium: [0.011, 0.014, 0.018, 0.028, 0.038, 0.049],
  heavy: [0.012, 0.016, 0.020, 0.032, 0.042, 0.053],
  baritone: [0.013, 0.017, 0.026, 0.036, 0.046, 0.062]
}

function applyGaugeSet(preset: string) {
  const gauges = gaugePresets[preset]
  if (gauges) {
    strings.value.forEach((string, idx) => {
      string.gauge = gauges[idx]
    })
  }
}

// Calculate string tension using Mersenne's Law
// T = (μ × (2 × L × f)²) ÷ 4
function calculateTension(stringIndex: number): number {
  const string = strings.value[stringIndex]
  const scaleInches = scaleUnit.value === 'mm' ? customScale.value / 25.4 : customScale.value
  
  // Linear mass density approximation for steel strings (empirical)
  // μ ≈ 0.00001294 × (gauge in inches)² lb/in
  const mu = 0.00001294 * Math.pow(string.gauge, 2)
  
  // Mersenne's Law: T = (μ × (2 × L × f)²) ÷ 4
  const tension = (mu * Math.pow(2 * scaleInches * string.freq, 2)) / 4
  
  return tension
}

function getTensionClass(tension: number): string {
  if (tension < 13) return 'tension-low'
  if (tension > 16) return 'tension-high'
  return 'tension-good'
}

const totalTension = computed(() => {
  return strings.value.reduce((sum, _, idx) => sum + calculateTension(idx), 0)
})

const averageTension = computed(() => {
  return totalTension.value / strings.value.length
})

const tensionRange = computed(() => {
  const tensions = strings.value.map((_, idx) => calculateTension(idx))
  return Math.max(...tensions) - Math.min(...tensions)
})

// Scale selection (for future interactive features)
function selectScale(scaleType: string) {
  const scales: Record<string, number> = {
    fender: 25.5,
    gibson: 24.75,
    prs: 25.0,
    short: 24.0,
    baritone: 27.0,
    multiscale: 26.25 // Average of 25.5-27
  }
  
  customScale.value = scales[scaleType] || 25.5
  scaleUnit.value = 'in'
  activeTab.value = 'tension'
}
</script>

<style scoped>
.scale-designer {
  background: #202124;
  color: #e8eaed;
  min-height: 100vh;
  padding: 24px;
}

/* Header */
.designer-header {
  margin-bottom: 32px;
  text-align: center;
}

.designer-title {
  font-size: 32px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 8px;
}

.designer-subtitle {
  font-size: 16px;
  color: #9aa0a6;
  line-height: 1.5;
  max-width: 800px;
  margin: 0 auto;
}

/* Tab Navigation */
.designer-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 32px;
  border-bottom: 2px solid #3c4043;
  overflow-x: auto;
}

.designer-tab {
  padding: 12px 24px;
  font-size: 15px;
  font-weight: 500;
  color: #9aa0a6;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  white-space: nowrap;
}

.designer-tab:hover {
  color: #e8eaed;
  background: rgba(138, 180, 248, 0.1);
}

.designer-tab.active {
  color: #8ab4f8;
  border-bottom-color: #8ab4f8;
}

/* Section Headers */
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

/* Tab Content */
.tab-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Scale Grid */
.scale-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.scale-card {
  background: #292a2d;
  padding: 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.scale-card:hover {
  border-color: #8ab4f8;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(138, 180, 248, 0.3);
}

.scale-name {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 6px;
}

.scale-value {
  font-size: 16px;
  color: #8ab4f8;
  margin-bottom: 12px;
  font-weight: 500;
}

.scale-info {
  font-size: 13px;
  color: #9aa0a6;
  line-height: 1.6;
}

.scale-trait {
  margin-bottom: 4px;
}

/* Education Section */
.education-section {
  margin-top: 32px;
}

.edu-title {
  font-size: 22px;
  font-weight: 600;
  color: #ffd700;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.edu-card {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 20px;
  border-left: 4px solid #8ab4f8;
}

.edu-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 16px;
}

.edu-card p {
  font-size: 14px;
  line-height: 1.7;
  color: #e8eaed;
  margin-bottom: 12px;
}

.formula-box {
  background: rgba(0, 0, 0, 0.4);
  padding: 20px;
  border-radius: 8px;
  margin: 16px 0;
}

.formula {
  font-family: 'Courier New', monospace;
  font-size: 20px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 16px;
  color: #ffd700;
  letter-spacing: 1px;
}

.formula-legend {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
}

.formula-legend strong {
  color: #8ab4f8;
}

.edu-note {
  background: rgba(138, 180, 248, 0.1);
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  border-left: 3px solid #8ab4f8;
}

.edu-note strong {
  color: #8ab4f8;
}

.example-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin: 16px 0;
}

.example-item {
  background: rgba(0, 0, 0, 0.3);
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.example-scale {
  font-size: 14px;
  font-weight: 500;
  color: #ffd700;
  margin-bottom: 8px;
}

.example-tension {
  font-size: 22px;
  font-weight: bold;
  color: #fff;
  margin-bottom: 4px;
}

.example-note {
  font-size: 12px;
  color: #9aa0a6;
}

/* Tension Calculator */
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

.guide-row.too-loose {
  background: rgba(234, 67, 53, 0.1);
}

.guide-row.good {
  background: rgba(52, 168, 83, 0.1);
}

.guide-row.too-tight {
  background: rgba(251, 188, 5, 0.1);
}

.guide-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.guide-row.too-loose .guide-indicator {
  background: #ff6b6b;
}

.guide-row.good .guide-indicator {
  background: #51cf66;
}

.guide-row.too-tight .guide-indicator {
  background: #ffc107;
}

.guide-text {
  font-size: 13px;
  line-height: 1.5;
  color: #e8eaed;
}

.guide-text strong {
  color: #8ab4f8;
}

/* Intonation Section */
.intonation-education {
  max-width: 1000px;
}

.critical-concept {
  background: linear-gradient(135deg, rgba(234, 67, 53, 0.2) 0%, rgba(234, 67, 53, 0.1) 100%);
  padding: 24px;
  border-radius: 12px;
  border: 2px solid #ea4335;
  margin-bottom: 24px;
}

.critical-concept h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ff6b6b;
  margin-bottom: 12px;
}

.critical-concept p {
  font-size: 14px;
  line-height: 1.7;
  color: #e8eaed;
  margin-bottom: 12px;
}

.critical-concept strong {
  color: #8ab4f8;
}

.compensation-table {
  background: #292a2d;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.comp-header {
  margin-bottom: 16px;
}

.comp-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffd700;
  margin-bottom: 6px;
}

.comp-subtitle {
  font-size: 13px;
  color: #9aa0a6;
  font-style: italic;
}

.comp-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.comp-row {
  display: grid;
  grid-template-columns: 100px 80px 120px 120px 1fr;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 13px;
  align-items: center;
}

.comp-header-row {
  background: rgba(0, 0, 0, 0.3);
  font-weight: 600;
  color: #ffd700;
  font-size: 12px;
}

.highlight-reference {
  background: rgba(138, 180, 248, 0.2);
  border: 2px solid #8ab4f8;
  font-weight: 500;
}

.highlight-max {
  background: rgba(234, 67, 53, 0.2);
  border: 2px solid #ea4335;
  font-weight: 600;
}

.bridge-placement {
  background: linear-gradient(135deg, rgba(52, 168, 83, 0.2) 0%, rgba(52, 168, 83, 0.1) 100%);
  padding: 24px;
  border-radius: 12px;
  border: 2px solid #34a853;
  margin-bottom: 24px;
}

.bridge-placement h3 {
  font-size: 18px;
  font-weight: 600;
  color: #51cf66;
  margin-bottom: 16px;
}

.placement-box {
  background: rgba(0, 0, 0, 0.4);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.formula-example {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #51cf66;
  text-align: center;
  margin-top: 12px;
}

.formula-example strong {
  font-size: 18px;
}

.placement-note {
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.placement-note:last-child {
  margin-bottom: 0;
}

.placement-note.warning {
  background: rgba(234, 67, 53, 0.2);
  border-left: 4px solid #ea4335;
}

.placement-note.warning strong {
  color: #ff6b6b;
}

.placement-note.success {
  background: rgba(52, 168, 83, 0.2);
  border-left: 4px solid #34a853;
}

.placement-note.success strong {
  color: #51cf66;
}

.compensation-factors {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.compensation-factors h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ffd700;
  margin-bottom: 16px;
}

.factor-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.factor-item {
  font-size: 13px;
  line-height: 1.6;
  padding-left: 16px;
  border-left: 3px solid rgba(138, 180, 248, 0.5);
}

.factor-item strong {
  color: #8ab4f8;
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
}

.innovation-connection {
  background: linear-gradient(135deg, rgba(138, 180, 248, 0.2) 0%, rgba(138, 180, 248, 0.1) 100%);
  padding: 24px;
  border-radius: 12px;
  border: 2px solid #8ab4f8;
}

.innovation-connection h3 {
  font-size: 18px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 12px;
}

.innovation-connection p {
  font-size: 14px;
  line-height: 1.7;
  color: #e8eaed;
  margin-bottom: 12px;
}

.innovation-connection p:last-child {
  margin-bottom: 0;
}

.innovation-connection strong {
  color: #8ab4f8;
}

/* Multi-Scale Section */
.multiscale-education {
  max-width: 1000px;
}

.problem-solution {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 32px;
}

.problem-card, .solution-card {
  padding: 24px;
  border-radius: 12px;
}

.problem-card {
  background: linear-gradient(135deg, rgba(234, 67, 53, 0.2) 0%, rgba(234, 67, 53, 0.1) 100%);
  border: 2px solid #ea4335;
}

.solution-card {
  background: linear-gradient(135deg, rgba(52, 168, 83, 0.2) 0%, rgba(52, 168, 83, 0.1) 100%);
  border: 2px solid #34a853;
}

.problem-card h3 {
  color: #ff6b6b;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
}

.solution-card h3 {
  color: #51cf66;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
}

.problem-card p, .solution-card p {
  font-size: 14px;
  line-height: 1.6;
  color: #e8eaed;
  margin-bottom: 12px;
}

.problem-card ul, .solution-card ul {
  margin: 12px 0;
  padding-left: 20px;
}

.problem-card li, .solution-card li {
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.example {
  margin-top: 16px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

.example strong {
  display: block;
  font-size: 13px;
  color: #9aa0a6;
  margin-bottom: 8px;
}

.calc-result {
  font-size: 16px;
  font-weight: 600;
  padding: 8px;
  border-radius: 4px;
  text-align: center;
}

.calc-result.problem {
  background: rgba(234, 67, 53, 0.3);
  color: #ff6b6b;
}

.calc-result.solution {
  background: rgba(52, 168, 83, 0.3);
  color: #51cf66;
}

.multiscale-diagram {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 32px;
}

.multiscale-diagram h3 {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 16px;
}

.fret-visualization {
  background: rgba(0, 0, 0, 0.3);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.fret-line {
  margin-bottom: 20px;
  padding: 12px;
  border-radius: 6px;
}

.fret-line.treble {
  background: rgba(138, 180, 248, 0.2);
}

.fret-line.bass {
  background: rgba(52, 168, 83, 0.2);
}

.fret-label {
  font-size: 14px;
  font-weight: 500;
  color: #ffd700;
  margin-bottom: 6px;
}

.fret-visual {
  font-family: 'Courier New', monospace;
  font-size: 16px;
  margin-bottom: 6px;
  letter-spacing: 2px;
  color: #fff;
}

.fret-tension {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
}

.diagram-note {
  font-size: 13px;
  line-height: 1.6;
  color: #9aa0a6;
  font-style: italic;
}

.tension-comparison {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 32px;
}

.tension-comparison h3 {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 16px;
}

.comparison-table {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.comparison-header {
  display: grid;
  grid-template-columns: 120px 110px 140px 110px;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  font-weight: 600;
  color: #ffd700;
  font-size: 12px;
  border-radius: 6px;
}

.comparison-row {
  display: grid;
  grid-template-columns: 120px 110px 140px 110px;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 13px;
  align-items: center;
}

.comparison-row div:last-child {
  text-align: center;
  font-weight: 600;
  padding: 4px;
  border-radius: 4px;
}

.neutral {
  color: #9aa0a6;
}

.slight {
  background: rgba(138, 180, 248, 0.2);
  color: #8ab4f8;
}

.good {
  background: rgba(52, 168, 83, 0.2);
  color: #51cf66;
}

.excellent {
  background: rgba(52, 168, 83, 0.3);
  color: #51cf66;
  font-weight: bold;
}

.comparison-note {
  font-size: 13px;
  line-height: 1.6;
  color: #e8eaed;
  font-style: italic;
}

.ergonomic-benefits {
  margin-bottom: 32px;
}

.ergonomic-benefits h3 {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 16px;
}

.benefit-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.benefit-card {
  background: #292a2d;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.benefit-card:hover {
  border-color: #8ab4f8;
  transform: translateY(-4px);
}

.benefit-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.benefit-title {
  font-size: 15px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 8px;
}

.benefit-text {
  font-size: 13px;
  line-height: 1.6;
  color: #e8eaed;
}

.custom-scale-exploration {
  background: linear-gradient(135deg, rgba(138, 180, 248, 0.2) 0%, rgba(138, 180, 248, 0.1) 100%);
  padding: 24px;
  border-radius: 12px;
  border: 2px solid #8ab4f8;
  text-align: center;
}

.custom-scale-exploration h3 {
  font-size: 18px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 12px;
}

.custom-scale-exploration p {
  font-size: 14px;
  line-height: 1.7;
  color: #e8eaed;
  margin-bottom: 12px;
}

.custom-scale-exploration strong {
  color: #ffd700;
}

.btn-explore {
  background: linear-gradient(135deg, #1a73e8 0%, #8ab4f8 100%);
  color: #fff;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 8px;
}

.btn-explore:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(138, 180, 248, 0.4);
}

/* Responsive */
@media (max-width: 768px) {
  .designer-tabs {
    overflow-x: auto;
  }

  .scale-grid {
    grid-template-columns: 1fr;
  }

  .example-grid {
    grid-template-columns: 1fr;
  }

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

  .problem-solution {
    grid-template-columns: 1fr;
  }

  .comp-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .comp-row > div {
    padding: 4px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .comp-row > div:last-child {
    border-bottom: none;
  }

  .comparison-header,
  .comparison-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .benefit-grid {
    grid-template-columns: 1fr;
  }
}
</style>
