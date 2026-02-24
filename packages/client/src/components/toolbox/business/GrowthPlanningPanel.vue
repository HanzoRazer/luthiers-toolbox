<script setup lang="ts">
/**
 * GrowthPlanningPanel.vue - Growth planning tab content
 * Extracted from BusinessCalculator.vue
 */
import { useCssModule } from 'vue'
import type { GrowthData } from '../business-calculator/useGrowthCalculator'

const $style = useCssModule()

defineProps<{
  growth: GrowthData
  currentMonthlyHours: number
  targetMonthlyHours: number
  growthInsight: string
}>()

const emit = defineEmits<{
  'update:growth': [data: GrowthData]
}>()
</script>

<template>
  <div :class="$style.tabContent">
    <h2>📈 Growth Planning</h2>

    <div :class="$style.section">
      <h3>Scaling Scenarios</h3>
      <div :class="$style.inputRow">
        <label>Current Monthly Output:</label>
        <input
          :value="growth.currentOutput"
          type="number"
          step="1"
          @input="emit('update:growth', { ...growth, currentOutput: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">instruments</span>
      </div>
      <div :class="$style.inputRow">
        <label>Target Monthly Output:</label>
        <input
          :value="growth.targetOutput"
          type="number"
          step="1"
          @input="emit('update:growth', { ...growth, targetOutput: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">instruments</span>
      </div>
      <div :class="$style.inputRow">
        <label>Hours per Instrument:</label>
        <input
          :value="growth.hoursPerUnit"
          type="number"
          step="1"
          @input="emit('update:growth', { ...growth, hoursPerUnit: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">hrs</span>
      </div>
    </div>

    <div :class="$style.results">
      <h3>Growth Analysis</h3>
      <div :class="$style.resultItem">
        <span>Current Monthly Hours:</span>
        <strong>{{ currentMonthlyHours }} hrs</strong>
      </div>
      <div :class="$style.resultItem">
        <span>Target Monthly Hours:</span>
        <strong>{{ targetMonthlyHours }} hrs</strong>
      </div>
      <div :class="$style.insight">
        {{ growthInsight }}
      </div>
    </div>
  </div>
</template>

<style module src="../business-calculator/BusinessCalculator.module.css" />
