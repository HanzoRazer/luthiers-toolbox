<script setup lang="ts">
/**
 * CashFlowPanel.vue - Cash flow projection tab content
 * Extracted from BusinessCalculator.vue
 */
import { useCssModule } from 'vue'
import type { CashflowData } from '../business-calculator/useCashflowCalculator'

const $style = useCssModule()

defineProps<{
  cashflow: CashflowData
  monthlyRevenue: number
  netIncome: number
}>()

const emit = defineEmits<{
  'update:cashflow': [data: CashflowData]
}>()
</script>

<template>
  <div :class="$style.tabContent">
    <h2>💰 Cash Flow Projection</h2>

    <div :class="$style.section">
      <h3>Monthly Projections</h3>
      <div :class="$style.inputRow">
        <label>Instruments Sold/Month:</label>
        <input
          :value="cashflow.unitsSold"
          type="number"
          step="1"
          min="0"
          @input="emit('update:cashflow', { ...cashflow, unitsSold: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">units</span>
      </div>
      <div :class="$style.inputRow">
        <label>Average Sale Price:</label>
        <input
          :value="cashflow.avgPrice"
          type="number"
          step="100"
          @input="emit('update:cashflow', { ...cashflow, avgPrice: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
      <div :class="$style.inputRow">
        <label>Monthly Fixed Costs:</label>
        <input
          :value="cashflow.fixedCosts"
          type="number"
          step="100"
          @input="emit('update:cashflow', { ...cashflow, fixedCosts: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
    </div>

    <div :class="$style.results">
      <h3>Monthly Cash Flow</h3>
      <div :class="$style.resultItem">
        <span>Revenue:</span>
        <strong>${{ monthlyRevenue.toLocaleString() }}</strong>
      </div>
      <div :class="$style.resultItem">
        <span>Fixed Costs:</span>
        <strong>${{ cashflow.fixedCosts.toLocaleString() }}</strong>
      </div>
      <div
        :class="[
          $style.resultItem,
          netIncome > 0 && $style.resultItemProfit,
          netIncome < 0 && $style.resultItemLoss
        ]"
      >
        <span>Net Income:</span>
        <strong>${{ netIncome.toLocaleString() }}</strong>
      </div>
    </div>
  </div>
</template>

<style module src="../business-calculator/BusinessCalculator.module.css" />
