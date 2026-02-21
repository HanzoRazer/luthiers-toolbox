<template>
  <div :class="styles.finishingDesigner">
    <!-- Header -->
    <div :class="styles.designerHeader">
      <h1 :class="styles.designerTitle">
        🎨 Finishing Designer
      </h1>
      <p :class="styles.designerSubtitle">
        Plan finishes, track labor hours, and understand the true value of your craftsmanship
      </p>
    </div>

    <!-- Tab Navigation -->
    <div :class="styles.designerTabs">
      <div
        v-for="tab in tabs"
        :key="tab.id"
        :class="[styles.designerTab, { [styles.designerTabActive]: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </div>
    </div>

    <!-- Tab 1: Finish Types & Planning -->
    <div
      v-if="activeTab === 'types'"
      :class="styles.tabContent"
    >
      <div :class="styles.sectionHeader">
        <h2>Finish Types</h2>
        <p>Select a finishing technique and explore its requirements</p>
      </div>

      <div :class="styles.finishGrid">
        <div
          :class="styles.finishCard"
          @click="selectFinish('varnish')"
        >
          <div :class="styles.finishName">
            Simple Varnish
          </div>
          <div :class="styles.finishTime">
            8-12 hours labor
          </div>
          <div :class="styles.finishInfo">
            <div>• Easiest for beginners</div>
            <div>• 3-5 coats</div>
            <div>• Wipe-on or brush application</div>
            <div>• Good durability</div>
          </div>
        </div>

        <div
          :class="styles.finishCard"
          @click="selectFinish('french')"
        >
          <div :class="styles.finishName">
            French Polish (Shellac)
          </div>
          <div :class="styles.finishTime">
            20-40 hours labor
          </div>
          <div :class="styles.finishInfo">
            <div>• Traditional hand-rubbed</div>
            <div>• 50-100+ applications</div>
            <div>• Requires skill and patience</div>
            <div>• Beautiful thin finish</div>
          </div>
        </div>

        <div
          :class="styles.finishCard"
          @click="selectFinish('nitro')"
        >
          <div :class="styles.finishName">
            Nitrocellulose Lacquer
          </div>
          <div :class="styles.finishTime">
            15-25 hours labor
          </div>
          <div :class="styles.finishInfo">
            <div>• Classic guitar finish</div>
            <div>• 6-12 coats + sanding</div>
            <div>• Spray gun required</div>
            <div>• Vintage tone reputation</div>
          </div>
        </div>

        <div
          :class="styles.finishCard"
          @click="selectFinish('poly')"
        >
          <div :class="styles.finishName">
            Polyurethane
          </div>
          <div :class="styles.finishTime">
            10-18 hours labor
          </div>
          <div :class="styles.finishInfo">
            <div>• Modern durable finish</div>
            <div>• 3-6 coats</div>
            <div>• Spray or wipe-on</div>
            <div>• Thick protective layer</div>
          </div>
        </div>

        <div
          :class="styles.finishCard"
          @click="selectFinish('oil')"
        >
          <div :class="styles.finishName">
            Oil Finish (Tung/Linseed)
          </div>
          <div :class="styles.finishTime">
            12-20 hours labor
          </div>
          <div :class="styles.finishInfo">
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
      :class="styles.tabContent"
    >
      <div :class="styles.sectionHeader">
        <h2>Finishing Workflow: {{ finishTypes[selectedFinish]?.name || 'Select a finish type' }}</h2>
        <p>Step-by-step process with labor time estimates</p>
      </div>

      <div
        v-if="selectedFinish"
        :class="styles.workflowSection"
      >
        <div
          v-for="(step, idx) in finishTypes[selectedFinish].steps"
          :key="idx"
          :class="styles.workflowStep"
        >
          <div :class="styles.stepNumber">
            {{ idx + 1 }}
          </div>
          <div :class="styles.stepContent">
            <div :class="styles.stepTitle">
              {{ step.title }}
            </div>
            <div :class="styles.stepDesc">
              {{ step.description }}
            </div>
            <div :class="styles.stepTime">
              <strong>Time:</strong> {{ step.time }} |
              <strong>Cure:</strong> {{ step.cure }}
            </div>
          </div>
        </div>

        <div :class="styles.workflowSummary">
          <h3>Total Labor Estimate</h3>
          <div :class="styles.summaryGrid">
            <div :class="styles.summaryItem">
              <div :class="styles.summaryLabel">
                Active Work Time
              </div>
              <div :class="styles.summaryValue">
                {{ finishTypes[selectedFinish].totalLabor }}
              </div>
            </div>
            <div :class="styles.summaryItem">
              <div :class="styles.summaryLabel">
                Cure/Wait Time
              </div>
              <div :class="styles.summaryValue">
                {{ finishTypes[selectedFinish].totalCure }}
              </div>
            </div>
            <div :class="styles.summaryItem">
              <div :class="styles.summaryLabel">
                Calendar Days
              </div>
              <div :class="styles.summaryValue">
                {{ finishTypes[selectedFinish].calendarDays }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        :class="styles.emptyState"
      >
        Select a finish type from the Finish Types tab to see the workflow
      </div>
    </div>

    <!-- Tab 3: Labor & Cost -->
    <div
      v-if="activeTab === 'labor'"
      :class="styles.tabContent"
    >
      <div :class="styles.sectionHeader">
        <h2>Labor Value Calculator</h2>
        <p>Understand what your time and skill are worth</p>
      </div>

      <div :class="styles.laborCalculator">
        <div :class="styles.inputSection">
          <h3>Your Labor Rate</h3>
          <div :class="styles.inputGroup">
            <label>Hourly Rate ($/hr)</label>
            <input
              v-model.number="hourlyRate"
              type="number"
              step="5"
              min="10"
              max="200"
            >
          </div>
          <div :class="styles.ratePresets">
            <button
              :class="styles.btnPreset"
              @click="hourlyRate = 25"
            >
              Hobbyist ($25)
            </button>
            <button
              :class="styles.btnPreset"
              @click="hourlyRate = 50"
            >
              Semi-Pro ($50)
            </button>
            <button
              :class="styles.btnPreset"
              @click="hourlyRate = 75"
            >
              Professional ($75)
            </button>
            <button
              :class="styles.btnPreset"
              @click="hourlyRate = 100"
            >
              Master ($100)
            </button>
          </div>

          <h3>Project Size</h3>
          <div :class="styles.inputGroup">
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

          <div :class="styles.inputGroup">
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

        <div :class="styles.resultsSection">
          <h3>Labor Cost Breakdown</h3>
          <div :class="styles.costBreakdown">
            <div :class="styles.costRow">
              <span>Surface Preparation</span>
              <span :class="styles.costHours">{{ prepHours }} hrs</span>
              <span :class="styles.costValue">${{ (prepHours * hourlyRate).toFixed(2) }}</span>
            </div>
            <div :class="styles.costRow">
              <span>Finish Application</span>
              <span :class="styles.costHours">{{ applicationHours }} hrs</span>
              <span :class="styles.costValue">${{ (applicationHours * hourlyRate).toFixed(2) }}</span>
            </div>
            <div :class="styles.costRow">
              <span>Sanding Between Coats</span>
              <span :class="styles.costHours">{{ sandingHours }} hrs</span>
              <span :class="styles.costValue">${{ (sandingHours * hourlyRate).toFixed(2) }}</span>
            </div>
            <div :class="styles.costRow">
              <span>Final Buffing/Polishing</span>
              <span :class="styles.costHours">{{ buffingHours }} hrs</span>
              <span :class="styles.costValue">${{ (buffingHours * hourlyRate).toFixed(2) }}</span>
            </div>
            <div :class="styles.costRowTotal">
              <span><strong>Total Labor</strong></span>
              <span :class="styles.costHours"><strong>{{ totalHours }} hrs</strong></span>
              <span :class="styles.costValue"><strong>${{ totalLaborCost.toFixed(2) }}</strong></span>
            </div>
          </div>

          <div :class="styles.insightBox">
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
      :class="styles.tabContent"
    >
      <div :class="styles.sectionHeader">
        <h2>Sunburst Pattern Designer</h2>
        <p>Plan color bursts and export for robotic application</p>
      </div>

      <div :class="styles.burstDesigner">
        <div :class="styles.burstControls">
          <h3>Burst Type</h3>
          <div :class="styles.burstTypeSelector">
            <div
              v-for="type in burstTypes"
              :key="type.id"
              :class="[styles.burstTypeCard, { [styles.burstTypeCardActive]: burstType === type.id }]"
              @click="burstType = type.id"
            >
              {{ type.name }}
            </div>
          </div>

          <h3>Colors</h3>
          <div :class="styles.colorInputs">
            <div :class="styles.colorInput">
              <label>Center Color</label>
              <input
                v-model="centerColor"
                type="color"
              >
              <span>{{ centerColor }}</span>
            </div>
            <div
              v-if="burstType !== 'solid'"
              :class="styles.colorInput"
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
              :class="styles.colorInput"
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
          <div :class="styles.paramInputs">
            <div :class="styles.paramInput">
              <label>Fade Start (mm from center)</label>
              <input
                v-model.number="fadeStart"
                type="number"
                step="5"
                min="0"
                max="150"
              >
            </div>
            <div :class="styles.paramInput">
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
          <div :class="styles.burstPresets">
            <button
              :class="styles.btnBurst"
              @click="applyBurstPreset('tobacco')"
            >
              Tobacco Sunburst
            </button>
            <button
              :class="styles.btnBurst"
              @click="applyBurstPreset('cherry')"
            >
              Cherry Sunburst
            </button>
            <button
              :class="styles.btnBurst"
              @click="applyBurstPreset('honeyburst')"
            >
              Honeyburst
            </button>
            <button
              :class="styles.btnBurst"
              @click="applyBurstPreset('lemondrop')"
            >
              Lemon Drop
            </button>
          </div>

          <button
            :class="styles.btnExport"
            @click="exportBurstCSV"
          >
            Export CSV for Robotic Spray
          </button>
        </div>

        <div :class="styles.burstPreview">
          <h3>Preview</h3>
          <div :class="styles.previewCanvas">
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
          <p :class="styles.previewNote">
            Simplified preview - actual burst will blend more smoothly
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import styles from './FinishingDesigner.module.css'

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
