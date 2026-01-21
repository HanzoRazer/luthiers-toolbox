<template>
  <div class="finishing-designer">
    <!-- Header -->
    <div class="designer-header">
      <h1 class="designer-title">
        🎨 Finishing Designer
      </h1>
      <p class="designer-subtitle">
        Plan finishes, track labor hours, and understand the true value of your craftsmanship
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

    <!-- Tab 1: Finish Types & Planning -->
    <div
      v-if="activeTab === 'types'"
      class="tab-content"
    >
      <div class="section-header">
        <h2>Finish Types</h2>
        <p>Select a finishing technique and explore its requirements</p>
      </div>

      <div class="finish-grid">
        <div
          class="finish-card"
          @click="selectFinish('varnish')"
        >
          <div class="finish-name">
            Simple Varnish
          </div>
          <div class="finish-time">
            8-12 hours labor
          </div>
          <div class="finish-info">
            <div>• Easiest for beginners</div>
            <div>• 3-5 coats</div>
            <div>• Wipe-on or brush application</div>
            <div>• Good durability</div>
          </div>
        </div>

        <div
          class="finish-card"
          @click="selectFinish('french')"
        >
          <div class="finish-name">
            French Polish (Shellac)
          </div>
          <div class="finish-time">
            20-40 hours labor
          </div>
          <div class="finish-info">
            <div>• Traditional hand-rubbed</div>
            <div>• 50-100+ applications</div>
            <div>• Requires skill and patience</div>
            <div>• Beautiful thin finish</div>
          </div>
        </div>

        <div
          class="finish-card"
          @click="selectFinish('nitro')"
        >
          <div class="finish-name">
            Nitrocellulose Lacquer
          </div>
          <div class="finish-time">
            15-25 hours labor
          </div>
          <div class="finish-info">
            <div>• Classic guitar finish</div>
            <div>• 6-12 coats + sanding</div>
            <div>• Spray gun required</div>
            <div>• Vintage tone reputation</div>
          </div>
        </div>

        <div
          class="finish-card"
          @click="selectFinish('poly')"
        >
          <div class="finish-name">
            Polyurethane
          </div>
          <div class="finish-time">
            10-18 hours labor
          </div>
          <div class="finish-info">
            <div>• Modern durable finish</div>
            <div>• 3-6 coats</div>
            <div>• Spray or wipe-on</div>
            <div>• Thick protective layer</div>
          </div>
        </div>

        <div
          class="finish-card"
          @click="selectFinish('oil')"
        >
          <div class="finish-name">
            Oil Finish (Tung/Linseed)
          </div>
          <div class="finish-time">
            12-20 hours labor
          </div>
          <div class="finish-info">
            <div>• Natural "in-the-wood" finish</div>
            <div>• 5-8 coats + buffing</div>
            <div>• Hand application</div>
            <div>• Easy to repair</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: Process Workflow -->
    <div
      v-if="activeTab === 'workflow'"
      class="tab-content"
    >
      <div class="section-header">
        <h2>Finishing Workflow: {{ finishTypes[selectedFinish]?.name || 'Select a finish type' }}</h2>
        <p>Step-by-step process with labor time estimates</p>
      </div>

      <div
        v-if="selectedFinish"
        class="workflow-section"
      >
        <div
          v-for="(step, idx) in finishTypes[selectedFinish].steps"
          :key="idx"
          class="workflow-step"
        >
          <div class="step-number">
            {{ idx + 1 }}
          </div>
          <div class="step-content">
            <div class="step-title">
              {{ step.title }}
            </div>
            <div class="step-desc">
              {{ step.description }}
            </div>
            <div class="step-time">
              <strong>Time:</strong> {{ step.time }} | 
              <strong>Cure:</strong> {{ step.cure }}
            </div>
          </div>
        </div>

        <div class="workflow-summary">
          <h3>Total Labor Estimate</h3>
          <div class="summary-grid">
            <div class="summary-item">
              <div class="summary-label">
                Active Work Time
              </div>
              <div class="summary-value">
                {{ finishTypes[selectedFinish].totalLabor }}
              </div>
            </div>
            <div class="summary-item">
              <div class="summary-label">
                Cure/Wait Time
              </div>
              <div class="summary-value">
                {{ finishTypes[selectedFinish].totalCure }}
              </div>
            </div>
            <div class="summary-item">
              <div class="summary-label">
                Calendar Days
              </div>
              <div class="summary-value">
                {{ finishTypes[selectedFinish].calendarDays }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="empty-state"
      >
        Select a finish type from the Finish Types tab to see the workflow
      </div>
    </div>

    <!-- Tab 3: Labor & Cost -->
    <div
      v-if="activeTab === 'labor'"
      class="tab-content"
    >
      <div class="section-header">
        <h2>Labor Value Calculator</h2>
        <p>Understand what your time and skill are worth</p>
      </div>

      <div class="labor-calculator">
        <div class="input-section">
          <h3>Your Labor Rate</h3>
          <div class="input-group">
            <label>Hourly Rate ($/hr)</label>
            <input
              v-model.number="hourlyRate"
              type="number"
              step="5"
              min="10"
              max="200"
            >
          </div>
          <div class="rate-presets">
            <button
              class="btn-preset"
              @click="hourlyRate = 25"
            >
              Hobbyist ($25)
            </button>
            <button
              class="btn-preset"
              @click="hourlyRate = 50"
            >
              Semi-Pro ($50)
            </button>
            <button
              class="btn-preset"
              @click="hourlyRate = 75"
            >
              Professional ($75)
            </button>
            <button
              class="btn-preset"
              @click="hourlyRate = 100"
            >
              Master ($100)
            </button>
          </div>

          <h3>Project Size</h3>
          <div class="input-group">
            <label>Instrument Type</label>
            <select v-model="instrumentType">
              <option value="full-body">
                Full Body Electric (Strat/Les Paul)
              </option>
              <option value="neck">
                Neck Only
              </option>
              <option value="acoustic">
                Acoustic Guitar
              </option>
              <option value="classical">
                Classical Guitar
              </option>
              <option value="bass">
                Bass Guitar
              </option>
              <option value="violin">
                Violin
              </option>
            </select>
          </div>

          <div class="input-group">
            <label>Finish Type</label>
            <select v-model="laborFinishType">
              <option value="varnish">
                Simple Varnish
              </option>
              <option value="french">
                French Polish
              </option>
              <option value="nitro">
                Nitrocellulose
              </option>
              <option value="poly">
                Polyurethane
              </option>
              <option value="oil">
                Oil Finish
              </option>
            </select>
          </div>
        </div>

        <div class="results-section">
          <h3>Labor Cost Breakdown</h3>
          <div class="cost-breakdown">
            <div class="cost-row">
              <span>Surface Preparation</span>
              <span class="cost-hours">{{ prepHours }} hrs</span>
              <span class="cost-value">${{ (prepHours * hourlyRate).toFixed(2) }}</span>
            </div>
            <div class="cost-row">
              <span>Finish Application</span>
              <span class="cost-hours">{{ applicationHours }} hrs</span>
              <span class="cost-value">${{ (applicationHours * hourlyRate).toFixed(2) }}</span>
            </div>
            <div class="cost-row">
              <span>Sanding Between Coats</span>
              <span class="cost-hours">{{ sandingHours }} hrs</span>
              <span class="cost-value">${{ (sandingHours * hourlyRate).toFixed(2) }}</span>
            </div>
            <div class="cost-row">
              <span>Final Buffing/Polishing</span>
              <span class="cost-hours">{{ buffingHours }} hrs</span>
              <span class="cost-value">${{ (buffingHours * hourlyRate).toFixed(2) }}</span>
            </div>
            <div class="cost-row total">
              <span><strong>Total Labor</strong></span>
              <span class="cost-hours"><strong>{{ totalHours }} hrs</strong></span>
              <span class="cost-value"><strong>${{ totalLaborCost.toFixed(2) }}</strong></span>
            </div>
          </div>

          <div class="insight-box">
            <h4>💡 Pricing Insight</h4>
            <p>
              At ${{ hourlyRate }}/hr, your finishing labor adds <strong>${{ totalLaborCost.toFixed(2) }}</strong> 
              to the instrument cost. This doesn't include materials (~$30-150) or overhead.
            </p>
            <p>
              Many builders undercharge by 30-50% by not tracking finishing time accurately. 
              This calculator helps you price realistically.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 4: Burst Patterns -->
    <div
      v-if="activeTab === 'burst'"
      class="tab-content"
    >
      <div class="section-header">
        <h2>Sunburst Pattern Designer</h2>
        <p>Plan color bursts and export for robotic application</p>
      </div>

      <div class="burst-designer">
        <div class="burst-controls">
          <h3>Burst Type</h3>
          <div class="burst-type-selector">
            <div 
              v-for="type in burstTypes" 
              :key="type.id"
              class="burst-type-card"
              :class="{ active: burstType === type.id }"
              @click="burstType = type.id"
            >
              {{ type.name }}
            </div>
          </div>

          <h3>Colors</h3>
          <div class="color-inputs">
            <div class="color-input">
              <label>Center Color</label>
              <input
                v-model="centerColor"
                type="color"
              >
              <span>{{ centerColor }}</span>
            </div>
            <div
              v-if="burstType !== 'solid'"
              class="color-input"
            >
              <label>Mid Color (optional)</label>
              <input
                v-model="midColor"
                type="color"
              >
              <span>{{ midColor }}</span>
            </div>
            <div
              v-if="burstType !== 'solid'"
              class="color-input"
            >
              <label>Edge Color</label>
              <input
                v-model="edgeColor"
                type="color"
              >
              <span>{{ edgeColor }}</span>
            </div>
          </div>

          <h3>Burst Parameters</h3>
          <div class="param-inputs">
            <div class="param-input">
              <label>Fade Start (mm from center)</label>
              <input
                v-model.number="fadeStart"
                type="number"
                step="5"
                min="0"
                max="150"
              >
            </div>
            <div class="param-input">
              <label>Fade End (mm from center)</label>
              <input
                v-model.number="fadeEnd"
                type="number"
                step="5"
                min="0"
                max="200"
              >
            </div>
          </div>

          <h3>Classic Presets</h3>
          <div class="burst-presets">
            <button
              class="btn-burst"
              @click="applyBurstPreset('tobacco')"
            >
              Tobacco Sunburst
            </button>
            <button
              class="btn-burst"
              @click="applyBurstPreset('cherry')"
            >
              Cherry Sunburst
            </button>
            <button
              class="btn-burst"
              @click="applyBurstPreset('honeyburst')"
            >
              Honeyburst
            </button>
            <button
              class="btn-burst"
              @click="applyBurstPreset('lemondrop')"
            >
              Lemon Drop
            </button>
          </div>

          <button
            class="btn-export"
            @click="exportBurstCSV"
          >
            Export CSV for Robotic Spray
          </button>
        </div>

        <div class="burst-preview">
          <h3>Preview</h3>
          <div class="preview-canvas">
            <svg
              width="300"
              height="400"
              viewBox="0 0 300 400"
            >
              <!-- Body outline -->
              <ellipse
                cx="150"
                cy="200"
                rx="140"
                ry="180"
                fill="none"
                stroke="#333"
                stroke-width="2"
              />
              
              <!-- Burst gradient (simplified visual) -->
              <defs>
                <radialGradient
                  :id="'burst-gradient'"
                  cx="50%"
                  cy="40%"
                >
                  <stop
                    offset="0%"
                    :stop-color="centerColor"
                  />
                  <stop
                    v-if="midColor && burstType !== 'solid'"
                    offset="50%"
                    :stop-color="midColor"
                  />
                  <stop
                    offset="100%"
                    :stop-color="edgeColor"
                  />
                </radialGradient>
              </defs>
              <ellipse
                cx="150"
                cy="160"
                rx="140"
                ry="180"
                :fill="`url(#burst-gradient)`"
                opacity="0.8"
              />
            </svg>
          </div>
          <p class="preview-note">
            Simplified preview - actual burst will blend more smoothly
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Tab management
const tabs = [
  { id: 'types', label: 'Finish Types' },
  { id: 'workflow', label: 'Process Workflow' },
  { id: 'labor', label: 'Labor & Cost' },
  { id: 'burst', label: 'Burst Patterns' }
]

const activeTab = ref('types')
const selectedFinish = ref<string>('')

// Finish type data
interface WorkflowStep {
  title: string
  description: string
  time: string
  cure: string
}

interface FinishType {
  name: string
  totalLabor: string
  totalCure: string
  calendarDays: string
  steps: WorkflowStep[]
}

const finishTypes: Record<string, FinishType> = {
  varnish: {
    name: 'Simple Varnish',
    totalLabor: '8-12 hours',
    totalCure: '3-5 days',
    calendarDays: '5-7 days',
    steps: [
      { title: 'Surface Prep', description: 'Sand to 220 grit, raise grain with water, final sand to 320', time: '2-3 hrs', cure: 'N/A' },
      { title: 'Seal Coat', description: 'Thin varnish (50/50 with mineral spirits), wipe-on application', time: '1 hr', cure: '24 hrs' },
      { title: 'Build Coats (3-4)', description: 'Full-strength varnish, wipe or brush, light sand between coats', time: '4-5 hrs', cure: '24-48 hrs each' },
      { title: 'Final Rubout', description: 'Wet sand with 1000-2000 grit, compound, polish', time: '2-3 hrs', cure: 'N/A' }
    ]
  },
  french: {
    name: 'French Polish (Shellac)',
    totalLabor: '20-40 hours',
    totalCure: '1-2 weeks',
    calendarDays: '14-21 days',
    steps: [
      { title: 'Pore Filling', description: 'Fill open grain with pumice/shellac paste, level sand', time: '3-5 hrs', cure: '24 hrs' },
      { title: 'Bodying Sessions (10-20)', description: 'Pad application in circular motion, build thin layers', time: '10-20 hrs', cure: '12-24 hrs between' },
      { title: 'Spiriting Off', description: 'Remove pad marks with alcohol on clean pad', time: '2-3 hrs', cure: '48 hrs' },
      { title: 'Final Burnish', description: 'Fine abrasive and oil to achieve gloss', time: '3-5 hrs', cure: '1 week' }
    ]
  },
  nitro: {
    name: 'Nitrocellulose Lacquer',
    totalLabor: '15-25 hours',
    totalCure: '2-4 weeks',
    calendarDays: '21-30 days',
    steps: [
      { title: 'Grain Filling', description: 'Apply grain filler (if mahogany), sand level', time: '2-3 hrs', cure: '24 hrs' },
      { title: 'Sanding Sealer (2-3 coats)', description: 'Spray sealer coats, sand to 320 between', time: '3-4 hrs', cure: '12 hrs each' },
      { title: 'Color Coats (3-5)', description: 'Spray color or stain, build slowly', time: '3-5 hrs', cure: '12-24 hrs each' },
      { title: 'Clear Topcoats (6-10)', description: 'Spray clear lacquer, sand with 400-600 between', time: '5-8 hrs', cure: '12 hrs each' },
      { title: 'Level & Polish', description: 'Wet sand 1000-2000, compound, polish to gloss', time: '3-5 hrs', cure: '2 weeks cure' }
    ]
  },
  poly: {
    name: 'Polyurethane',
    totalLabor: '10-18 hours',
    totalCure: '1-2 weeks',
    calendarDays: '10-14 days',
    steps: [
      { title: 'Surface Prep', description: 'Sand to 220, vacuum clean, wipe with mineral spirits', time: '2-3 hrs', cure: 'N/A' },
      { title: 'Seal Coat', description: 'Thin poly (50/50), spray or wipe-on', time: '1-2 hrs', cure: '24 hrs' },
      { title: 'Build Coats (3-5)', description: 'Full-strength poly, light sand with 320 between', time: '4-6 hrs', cure: '24-48 hrs each' },
      { title: 'Final Finish', description: 'Wet sand 600-1000, rub out with compound', time: '3-5 hrs', cure: '1 week' }
    ]
  },
  oil: {
    name: 'Oil Finish',
    totalLabor: '12-20 hours',
    totalCure: '2-3 weeks',
    calendarDays: '14-21 days',
    steps: [
      { title: 'Pore Prep', description: 'Sand to 320, optional grain filler', time: '2-3 hrs', cure: '24 hrs' },
      { title: 'Initial Flood Coats (2-3)', description: 'Apply generous oil, let soak 10-15 min, wipe excess', time: '3-4 hrs', cure: '24 hrs each' },
      { title: 'Build Coats (3-5)', description: 'Thinner coats, wet sand with 600-1000 between', time: '4-6 hrs', cure: '24-48 hrs each' },
      { title: 'Burnishing', description: 'Final thin coat, buff with cloth to warm sheen', time: '2-3 hrs', cure: '1 week' },
      { title: 'Wax/Buff', description: 'Optional paste wax, final buff', time: '1-2 hrs', cure: '1 week' }
    ]
  }
}

function selectFinish(type: string) {
  selectedFinish.value = type
  activeTab.value = 'workflow'
}

// Labor calculator
const hourlyRate = ref(50)
const instrumentType = ref('full-body')
const laborFinishType = ref('nitro')

const laborMultipliers: Record<string, { prep: number, app: number, sand: number, buff: number }> = {
  varnish: { prep: 2, app: 1, sand: 4, buff: 2 },
  french: { prep: 3, app: 15, sand: 2, buff: 3 },
  nitro: { prep: 2, app: 5, sand: 6, buff: 3 },
  poly: { prep: 2, app: 4, sand: 3, buff: 3 },
  oil: { prep: 2, app: 5, sand: 4, buff: 2 }
}

const instrumentMultipliers: Record<string, number> = {
  'full-body': 1.0,
  'neck': 0.3,
  'acoustic': 1.5,
  'classical': 1.3,
  'bass': 1.1,
  'violin': 0.6
}

const prepHours = computed(() => {
  const base = laborMultipliers[laborFinishType.value]?.prep || 2
  return +(base * instrumentMultipliers[instrumentType.value]).toFixed(1)
})

const applicationHours = computed(() => {
  const base = laborMultipliers[laborFinishType.value]?.app || 3
  return +(base * instrumentMultipliers[instrumentType.value]).toFixed(1)
})

const sandingHours = computed(() => {
  const base = laborMultipliers[laborFinishType.value]?.sand || 4
  return +(base * instrumentMultipliers[instrumentType.value]).toFixed(1)
})

const buffingHours = computed(() => {
  const base = laborMultipliers[laborFinishType.value]?.buff || 2
  return +(base * instrumentMultipliers[instrumentType.value]).toFixed(1)
})

const totalHours = computed(() => {
  return prepHours.value + applicationHours.value + sandingHours.value + buffingHours.value
})

const totalLaborCost = computed(() => {
  return totalHours.value * hourlyRate.value
})

// Burst pattern designer
const burstType = ref('2-color')
const centerColor = ref('#f4e4c1')
const midColor = ref('#d4a574')
const edgeColor = ref('#8b4513')
const fadeStart = ref(50)
const fadeEnd = ref(120)

const burstTypes = [
  { id: 'solid', name: 'Solid Color' },
  { id: '2-color', name: '2-Color Burst' },
  { id: '3-color', name: '3-Color Burst' }
]

function applyBurstPreset(preset: string) {
  const presets: Record<string, { center: string, mid: string, edge: string }> = {
    tobacco: { center: '#f4e4c1', mid: '#d4a574', edge: '#5c2e0a' },
    cherry: { center: '#ffe4b5', mid: '#dc143c', edge: '#8b0000' },
    honeyburst: { center: '#fff8dc', mid: '#ffa500', edge: '#d2691e' },
    lemondrop: { center: '#fffacd', mid: '#ffd700', edge: '#b8860b' }
  }
  
  const colors = presets[preset]
  if (colors) {
    centerColor.value = colors.center
    midColor.value = colors.mid
    edgeColor.value = colors.edge
    burstType.value = '3-color'
  }
}

function exportBurstCSV() {
  // Generate CSV with spray pattern coordinates
  const csv = [
    'x,y,color,intensity',
    `0,0,${centerColor.value},100`,
    `${fadeStart.value},0,${midColor.value},80`,
    `${fadeEnd.value},0,${edgeColor.value},60`
  ].join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'burst_pattern.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.finishing-designer {
  background: #202124;
  color: #e8eaed;
  min-height: 100vh;
  padding: 24px;
}

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
}

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

.tab-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.finish-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.finish-card {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.finish-card:hover {
  border-color: #8ab4f8;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(138, 180, 248, 0.3);
}

.finish-name {
  font-size: 20px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 8px;
}

.finish-time {
  font-size: 14px;
  color: #8ab4f8;
  margin-bottom: 16px;
  font-weight: 500;
}

.finish-info {
  font-size: 13px;
  color: #9aa0a6;
  line-height: 1.8;
}

.workflow-section {
  max-width: 900px;
}

.workflow-step {
  display: flex;
  gap: 20px;
  background: #292a2d;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 16px;
}

.step-number {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #1a73e8, #8ab4f8);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 18px;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 8px;
}

.step-desc {
  font-size: 14px;
  color: #9aa0a6;
  margin-bottom: 8px;
  line-height: 1.6;
}

.step-time {
  font-size: 13px;
  color: #8ab4f8;
}

.workflow-summary {
  background: linear-gradient(135deg, rgba(26, 115, 232, 0.2), rgba(138, 180, 248, 0.1));
  padding: 24px;
  border-radius: 12px;
  margin-top: 24px;
  border: 2px solid #8ab4f8;
}

.workflow-summary h3 {
  font-size: 20px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 13px;
  color: #9aa0a6;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #e8eaed;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #9aa0a6;
  font-size: 16px;
}

.labor-calculator {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  max-width: 1200px;
}

.input-section, .results-section {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
}

.input-section h3, .results-section h3 {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 16px;
}

.input-group {
  margin-bottom: 20px;
}

.input-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #e8eaed;
  margin-bottom: 8px;
}

.input-group input, .input-group select {
  width: 100%;
  background: #3c4043;
  border: 1px solid #5f6368;
  color: #e8eaed;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 15px;
}

.rate-presets {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.btn-preset {
  background: #3c4043;
  border: 1px solid #5f6368;
  color: #e8eaed;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-preset:hover {
  background: #8ab4f8;
  color: #202124;
  border-color: #8ab4f8;
}

.cost-breakdown {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  overflow: hidden;
}

.cost-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 14px;
}

.cost-row:last-child {
  border-bottom: none;
}

.cost-row.total {
  background: rgba(138, 180, 248, 0.2);
  font-size: 16px;
}

.cost-hours {
  color: #8ab4f8;
  text-align: right;
}

.cost-value {
  color: #51cf66;
  text-align: right;
  font-weight: 600;
}

.insight-box {
  background: linear-gradient(135deg, rgba(26, 115, 232, 0.2), rgba(138, 180, 248, 0.1));
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
  border-left: 4px solid #8ab4f8;
}

.insight-box h4 {
  font-size: 16px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 12px;
}

.insight-box p {
  font-size: 14px;
  line-height: 1.6;
  color: #e8eaed;
  margin-bottom: 12px;
}

.insight-box p:last-child {
  margin-bottom: 0;
}

.burst-designer {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  max-width: 1200px;
}

.burst-controls h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e8eaed;
  margin: 20px 0 12px 0;
}

.burst-controls h3:first-child {
  margin-top: 0;
}

.burst-type-selector {
  display: flex;
  gap: 12px;
}

.burst-type-card {
  flex: 1;
  background: #3c4043;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
  font-size: 14px;
}

.burst-type-card:hover {
  background: #4a4d50;
}

.burst-type-card.active {
  background: #8ab4f8;
  color: #202124;
  border-color: #8ab4f8;
  font-weight: 600;
}

.color-inputs, .param-inputs {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.color-input, .param-input {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-input label, .param-input label {
  flex: 1;
  font-size: 14px;
  color: #e8eaed;
}

.color-input input[type="color"] {
  width: 60px;
  height: 40px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.color-input span {
  font-family: monospace;
  font-size: 13px;
  color: #9aa0a6;
}

.param-input input {
  width: 120px;
  background: #3c4043;
  border: 1px solid #5f6368;
  color: #e8eaed;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
}

.burst-presets {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.btn-burst {
  background: #3c4043;
  border: 1px solid #5f6368;
  color: #e8eaed;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-burst:hover {
  background: #8ab4f8;
  color: #202124;
  border-color: #8ab4f8;
}

.btn-export {
  background: linear-gradient(135deg, #1a73e8, #8ab4f8);
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 20px;
  width: 100%;
}

.btn-export:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(138, 180, 248, 0.4);
}

.burst-preview {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
}

.burst-preview h3 {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 16px;
}

.preview-canvas {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  justify-content: center;
}

.preview-note {
  font-size: 12px;
  color: #9aa0a6;
  text-align: center;
  margin-top: 12px;
  font-style: italic;
}

@media (max-width: 1024px) {
  .labor-calculator, .burst-designer {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .designer-tabs {
    overflow-x: auto;
  }

  .finish-grid {
    grid-template-columns: 1fr;
  }

  .burst-presets {
    grid-template-columns: 1fr;
  }
}
</style>
