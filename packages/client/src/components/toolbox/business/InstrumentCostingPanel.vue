<script setup lang="ts">
/**
 * InstrumentCostingPanel.vue - Instrument cost calculator tab content
 * Extracted from BusinessCalculator.vue
 */
import { useCssModule } from 'vue'
import type { CostingData } from '../business-calculator/useCostingCalculator'

const $style = useCssModule()

defineProps<{
  costing: CostingData
  totalMaterials: number
  totalHours: number
  totalLabor: number
  overheadAllocation: number
  totalCost: number
}>()

const emit = defineEmits<{
  'update:costing': [data: CostingData]
}>()
</script>

<template>
  <div :class="$style.tabContent">
    <h2>🎸 Instrument Cost Calculator</h2>

    <div :class="$style.section">
      <h3>Materials</h3>
      <div :class="$style.inputRow">
        <label>Wood (body, neck):</label>
        <input
          :value="costing.wood"
          type="number"
          step="10"
          @input="emit('update:costing', { ...costing, wood: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
      <div :class="$style.inputRow">
        <label>Hardware (tuners, bridge, etc):</label>
        <input
          :value="costing.hardware"
          type="number"
          step="10"
          @input="emit('update:costing', { ...costing, hardware: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
      <div :class="$style.inputRow">
        <label>Electronics (pickups, pots):</label>
        <input
          :value="costing.electronics"
          type="number"
          step="10"
          @input="emit('update:costing', { ...costing, electronics: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
      <div :class="$style.inputRow">
        <label>Finishing (paint, lacquer):</label>
        <input
          :value="costing.finishing"
          type="number"
          step="5"
          @input="emit('update:costing', { ...costing, finishing: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
    </div>

    <div :class="$style.section">
      <h3>Labor</h3>
      <div :class="$style.inputRow">
        <label>Your Hourly Rate:</label>
        <input
          :value="costing.hourlyRate"
          type="number"
          step="5"
          @input="emit('update:costing', { ...costing, hourlyRate: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$/hr</span>
      </div>
      <div :class="$style.inputRow">
        <label>Build Hours:</label>
        <input
          :value="costing.buildHours"
          type="number"
          step="1"
          @input="emit('update:costing', { ...costing, buildHours: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">hrs</span>
      </div>
      <div :class="$style.inputRow">
        <label>Finishing Hours:</label>
        <input
          :value="costing.finishHours"
          type="number"
          step="1"
          @input="emit('update:costing', { ...costing, finishHours: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">hrs</span>
      </div>
      <div :class="$style.inputRow">
        <label>Setup Hours:</label>
        <input
          :value="costing.setupHours"
          type="number"
          step="0.5"
          @input="emit('update:costing', { ...costing, setupHours: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">hrs</span>
      </div>
    </div>

    <div :class="$style.results">
      <h3>Cost Breakdown</h3>
      <div :class="$style.resultItem">
        <span>Total Materials:</span>
        <strong>${{ totalMaterials.toFixed(2) }}</strong>
      </div>
      <div :class="$style.resultItem">
        <span>Total Labor ({{ totalHours }}hrs):</span>
        <strong>${{ totalLabor.toFixed(2) }}</strong>
      </div>
      <div :class="$style.resultItem">
        <span>Overhead Allocation:</span>
        <strong>${{ overheadAllocation.toFixed(2) }}</strong>
      </div>
      <div :class="[$style.resultItem, $style.resultItemTotal]">
        <span>Total Cost:</span>
        <strong>${{ totalCost.toFixed(2) }}</strong>
      </div>
      <div :class="$style.insight">
        💡 Add profit margin: 30% → ${{ (totalCost * 1.3).toFixed(2) }} | 50% → ${{ (totalCost * 1.5).toFixed(2) }}
      </div>
    </div>
  </div>
</template>

<style module src="../business-calculator/BusinessCalculator.module.css" />
