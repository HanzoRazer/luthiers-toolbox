<script setup lang="ts">
/**
 * StartupPlanningPanel.vue - Startup planning tab content
 * Extracted from BusinessCalculator.vue
 */
import { useCssModule } from 'vue'
import type { StartupData, AmortizationEntry } from '../business-calculator/useStartupCalculator'
import AmortizationSection from './AmortizationSection.vue'

const $style = useCssModule()

defineProps<{
  startup: StartupData
  showAmortization: boolean
  totalEquipment: number
  monthlyOverhead: number
  monthlyPayment: number
  totalInterest: number
  totalLoanPayment: number
  amortizationSchedule: AmortizationEntry[]
}>()

const emit = defineEmits<{
  'update:startup': [data: StartupData]
  'update:showAmortization': [show: boolean]
}>()

function formatCurrency(value: number): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function updateField<K extends keyof StartupData>(key: K, value: StartupData[K]) {
  emit('update:startup', { ...arguments[0], [key]: value })
}
</script>

<template>
  <div :class="$style.tabContent">
    <h2>🚀 Startup Planning</h2>

    <div :class="$style.section">
      <h3>Equipment & Tools</h3>
      <div :class="$style.inputRow">
        <label>CNC Router:</label>
        <input
          :value="startup.cncCost"
          type="number"
          step="1000"
          @input="emit('update:startup', { ...startup, cncCost: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
      <div :class="$style.inputRow">
        <label>Hand Tools:</label>
        <input
          :value="startup.handTools"
          type="number"
          step="100"
          @input="emit('update:startup', { ...startup, handTools: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
      <div :class="$style.inputRow">
        <label>Workbenches:</label>
        <input
          :value="startup.workbenches"
          type="number"
          step="100"
          @input="emit('update:startup', { ...startup, workbenches: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
    </div>

    <div :class="$style.section">
      <h3>Facilities</h3>
      <div :class="$style.inputRow">
        <label>Workshop Rent (monthly):</label>
        <input
          :value="startup.rent"
          type="number"
          step="100"
          @input="emit('update:startup', { ...startup, rent: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$/mo</span>
      </div>
      <div :class="$style.inputRow">
        <label>Utilities (monthly):</label>
        <input
          :value="startup.utilities"
          type="number"
          step="50"
          @input="emit('update:startup', { ...startup, utilities: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$/mo</span>
      </div>
    </div>

    <div :class="$style.section">
      <h3>Equipment Financing</h3>
      <div :class="$style.inputRow">
        <label>Loan Amount:</label>
        <input
          :value="startup.loanAmount"
          type="number"
          step="1000"
          @input="emit('update:startup', { ...startup, loanAmount: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">$</span>
      </div>
      <div :class="$style.inputRow">
        <label>Interest Rate (APR):</label>
        <input
          :value="startup.interestRate"
          type="number"
          step="0.1"
          min="0"
          @input="emit('update:startup', { ...startup, interestRate: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">%</span>
      </div>
      <div :class="$style.inputRow">
        <label>Loan Term:</label>
        <input
          :value="startup.loanTermYears"
          type="number"
          step="1"
          min="1"
          @input="emit('update:startup', { ...startup, loanTermYears: +($event.target as HTMLInputElement).value })"
        >
        <span :class="$style.unit">years</span>
      </div>
      <div :class="$style.inputRow">
        <label>Start Date:</label>
        <input
          :value="startup.loanStartDate"
          type="month"
          @input="emit('update:startup', { ...startup, loanStartDate: ($event.target as HTMLInputElement).value })"
        >
      </div>
    </div>

    <div :class="$style.results">
      <h3>Loan Summary</h3>
      <div :class="$style.resultItem">
        <span>Monthly Payment:</span>
        <strong>${{ formatCurrency(monthlyPayment) }}</strong>
      </div>
      <div :class="$style.resultItem">
        <span>Total Interest:</span>
        <strong>${{ formatCurrency(totalInterest) }}</strong>
      </div>
      <div :class="[$style.resultItem, $style.resultItemTotal]">
        <span>Total Payment:</span>
        <strong>${{ formatCurrency(totalLoanPayment) }}</strong>
      </div>
    </div>

    <div
      :class="$style.results"
      style="margin-top: 20px;"
    >
      <h3>Startup Summary</h3>
      <div :class="$style.resultItem">
        <span>Total Equipment:</span>
        <strong>${{ totalEquipment.toLocaleString() }}</strong>
      </div>
      <div :class="$style.resultItem">
        <span>Monthly Overhead:</span>
        <strong>${{ monthlyOverhead.toLocaleString() }}</strong>
      </div>
      <div :class="$style.resultItem">
        <span>Monthly Loan Payment:</span>
        <strong>${{ formatCurrency(monthlyPayment) }}</strong>
      </div>
      <div :class="[$style.resultItem, $style.resultItemTotal]">
        <span>Total Monthly Costs:</span>
        <strong>${{ formatCurrency(monthlyOverhead + monthlyPayment) }}</strong>
      </div>
    </div>

    <AmortizationSection
      v-if="showAmortization"
      :schedule="amortizationSchedule"
      @update:show="emit('update:showAmortization', $event)"
    />
    <button
      v-else
      :class="$style.toggleBtn"
      @click="emit('update:showAmortization', true)"
    >
      ▶ Show Amortization Schedule ({{ amortizationSchedule.length }} payments)
    </button>
  </div>
</template>

<style module src="../business-calculator/BusinessCalculator.module.css" />
