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
    <FinishTypesPanel
      v-if="activeTab === 'types'"
      :styles="styles"
      @select="selectFinish"
    />

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
        <LaborInputSection
          :styles="styles"
          v-model:hourly-rate="hourlyRate"
          v-model:instrument-type="instrumentType"
          v-model:finish-type="laborFinishType"
        />

        <LaborResultsSection
          :styles="styles"
          :hourly-rate="hourlyRate"
          :prep-hours="prepHours"
          :application-hours="applicationHours"
          :sanding-hours="sandingHours"
          :buffing-hours="buffingHours"
          :total-hours="totalHours"
          :total-labor-cost="totalLaborCost"
        />
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

        <BurstPreviewCanvas
          :styles="styles"
          :center-color="centerColor"
          :mid-color="midColor"
          :edge-color="edgeColor"
          :burst-type="burstType"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import styles from './FinishingDesigner.module.css'
import FinishTypesPanel from './finishing/FinishTypesPanel.vue'
import LaborInputSection from './finishing/LaborInputSection.vue'
import LaborResultsSection from './finishing/LaborResultsSection.vue'
import BurstPreviewCanvas from './finishing/BurstPreviewCanvas.vue'

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
