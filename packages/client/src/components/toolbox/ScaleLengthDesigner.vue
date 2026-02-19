<template>
  <div class="scale-designer">
    <!-- Header -->
    <div class="designer-header">
      <h1 class="designer-title">🎸 Scale Length Designer</h1>
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

    <!-- Tab Content -->
    <ScalePresetsTab
      v-if="activeTab === 'presets'"
      @select="selectScale"
    />

    <TensionCalculatorTab
      v-if="activeTab === 'tension'"
      :custom-scale="customScale"
      :scale-unit="scaleUnit"
      :strings="strings"
      :total-tension="totalTension"
      :average-tension="averageTension"
      :tension-range="tensionRange"
      :get-tension="getTension"
      :get-tension-class="getTensionClassCss"
      @update:custom-scale="customScale = $event"
      @update:scale-unit="scaleUnit = $event"
      @update-gauge="updateGauge"
      @apply-gauge-set="applyGaugeSet"
    />

    <IntonationTab v-if="activeTab === 'intonation'" />

    <MultiScaleTab
      v-if="activeTab === 'multiscale'"
      @go-to-tension="activeTab = 'tension'"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useScaleLengthCalculator } from './composables/useScaleLengthCalculator'
import {
  ScalePresetsTab,
  TensionCalculatorTab,
  IntonationTab,
  MultiScaleTab
} from './scale-length'

// Tab management
const tabs = [
  { id: 'presets', label: 'Scale Presets' },
  { id: 'tension', label: 'Tension Calculator' },
  { id: 'intonation', label: 'Intonation' },
  { id: 'multiscale', label: 'Multi-Scale' }
]

const activeTab = ref('presets')

// Tension calculator (from composable)
const {
  customScale,
  scaleUnit,
  strings,
  totalTension,
  averageTension,
  tensionRange,
  getTension,
  getTensionClass,
  applyGaugeSet,
  applyScalePreset
} = useScaleLengthCalculator()

// Map getTensionClass return to CSS class names
function getTensionClassCss(tension: number): string {
  const level = getTensionClass(tension)
  return `tension-${level}`
}

// Update a single string gauge
function updateGauge(idx: number, value: number) {
  if (strings.value[idx]) {
    strings.value[idx].gauge = value
  }
}

// Scale selection - switch tab after selecting
function selectScale(scaleType: string) {
  applyScalePreset(scaleType)
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

/* Responsive */
@media (max-width: 768px) {
  .designer-tabs {
    overflow-x: auto;
  }
}
</style>
