<template>
  <div :class="$style.calculator">
    <div :class="$style.header">
      <h1>💼 Business Calculator</h1>
      <p>Advanced financial planning for lutherie business</p>
    </div>

    <!-- Tab Navigation -->
    <div :class="$style.tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="[$style.tabBtn, activeTab === tab.id && $style.tabBtnActive]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab 1: Startup Planning -->
    <div
      v-if="activeTab === 'startup'"
      :class="$style.tabContent"
    >
      <h2>🚀 Startup Planning</h2>

      <div :class="$style.section">
        <h3>Equipment & Tools</h3>
        <div :class="$style.inputRow">
          <label>CNC Router:</label>
          <input
            v-model.number="startup.cncCost"
            type="number"
            step="1000"
          >
          <span :class="$style.unit">$</span>
        </div>
        <div :class="$style.inputRow">
          <label>Hand Tools:</label>
          <input
            v-model.number="startup.handTools"
            type="number"
            step="100"
          >
          <span :class="$style.unit">$</span>
        </div>
        <div :class="$style.inputRow">
          <label>Workbenches:</label>
          <input
            v-model.number="startup.workbenches"
            type="number"
            step="100"
          >
          <span :class="$style.unit">$</span>
        </div>
      </div>

      <div :class="$style.section">
        <h3>Facilities</h3>
        <div :class="$style.inputRow">
          <label>Workshop Rent (monthly):</label>
          <input
            v-model.number="startup.rent"
            type="number"
            step="100"
          >
          <span :class="$style.unit">$/mo</span>
        </div>
        <div :class="$style.inputRow">
          <label>Utilities (monthly):</label>
          <input
            v-model.number="startup.utilities"
            type="number"
            step="50"
          >
          <span :class="$style.unit">$/mo</span>
        </div>
      </div>

      <div :class="$style.section">
        <h3>Equipment Financing</h3>
        <div :class="$style.inputRow">
          <label>Loan Amount:</label>
          <input
            v-model.number="startup.loanAmount"
            type="number"
            step="1000"
          >
          <span :class="$style.unit">$</span>
        </div>
        <div :class="$style.inputRow">
          <label>Interest Rate (APR):</label>
          <input
            v-model.number="startup.interestRate"
            type="number"
            step="0.1"
            min="0"
          >
          <span :class="$style.unit">%</span>
        </div>
        <div :class="$style.inputRow">
          <label>Loan Term:</label>
          <input
            v-model.number="startup.loanTermYears"
            type="number"
            step="1"
            min="1"
          >
          <span :class="$style.unit">years</span>
        </div>
        <div :class="$style.inputRow">
          <label>Start Date:</label>
          <input
            v-model="startup.loanStartDate"
            type="month"
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
        @update:show="showAmortization = $event"
      />
      <button
        v-else
        :class="$style.toggleBtn"
        @click="showAmortization = true"
      >
        ▶ Show Amortization Schedule ({{ amortizationSchedule.length }} payments)
      </button>
    </div>

    <!-- Tab 2: Instrument Costing -->
    <div
      v-if="activeTab === 'costing'"
      :class="$style.tabContent"
    >
      <h2>🎸 Instrument Cost Calculator</h2>

      <div :class="$style.section">
        <h3>Materials</h3>
        <div :class="$style.inputRow">
          <label>Wood (body, neck):</label>
          <input
            v-model.number="costing.wood"
            type="number"
            step="10"
          >
          <span :class="$style.unit">$</span>
        </div>
        <div :class="$style.inputRow">
          <label>Hardware (tuners, bridge, etc):</label>
          <input
            v-model.number="costing.hardware"
            type="number"
            step="10"
          >
          <span :class="$style.unit">$</span>
        </div>
        <div :class="$style.inputRow">
          <label>Electronics (pickups, pots):</label>
          <input
            v-model.number="costing.electronics"
            type="number"
            step="10"
          >
          <span :class="$style.unit">$</span>
        </div>
        <div :class="$style.inputRow">
          <label>Finishing (paint, lacquer):</label>
          <input
            v-model.number="costing.finishing"
            type="number"
            step="5"
          >
          <span :class="$style.unit">$</span>
        </div>
      </div>

      <div :class="$style.section">
        <h3>Labor</h3>
        <div :class="$style.inputRow">
          <label>Your Hourly Rate:</label>
          <input
            v-model.number="costing.hourlyRate"
            type="number"
            step="5"
          >
          <span :class="$style.unit">$/hr</span>
        </div>
        <div :class="$style.inputRow">
          <label>Build Hours:</label>
          <input
            v-model.number="costing.buildHours"
            type="number"
            step="1"
          >
          <span :class="$style.unit">hrs</span>
        </div>
        <div :class="$style.inputRow">
          <label>Finishing Hours:</label>
          <input
            v-model.number="costing.finishHours"
            type="number"
            step="1"
          >
          <span :class="$style.unit">hrs</span>
        </div>
        <div :class="$style.inputRow">
          <label>Setup Hours:</label>
          <input
            v-model.number="costing.setupHours"
            type="number"
            step="0.5"
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

    <!-- Tab 3: Pricing Strategy -->
    <PricingStrategyPanel
      v-if="activeTab === 'pricing'"
      v-model:build-cost="pricing.buildCost"
      v-model:margin="pricing.margin"
      :selling-price="sellingPrice"
      :profit="profit"
      :break-even-units="breakEvenUnits"
    />

    <!-- Tab 4: Cash Flow -->
    <div
      v-if="activeTab === 'cashflow'"
      :class="$style.tabContent"
    >
      <h2>💰 Cash Flow Projection</h2>

      <div :class="$style.section">
        <h3>Monthly Projections</h3>
        <div :class="$style.inputRow">
          <label>Instruments Sold/Month:</label>
          <input
            v-model.number="cashflow.unitsSold"
            type="number"
            step="1"
            min="0"
          >
          <span :class="$style.unit">units</span>
        </div>
        <div :class="$style.inputRow">
          <label>Average Sale Price:</label>
          <input
            v-model.number="cashflow.avgPrice"
            type="number"
            step="100"
          >
          <span :class="$style.unit">$</span>
        </div>
        <div :class="$style.inputRow">
          <label>Monthly Fixed Costs:</label>
          <input
            v-model.number="cashflow.fixedCosts"
            type="number"
            step="100"
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

    <!-- Tab 5: Growth Planning -->
    <div
      v-if="activeTab === 'growth'"
      :class="$style.tabContent"
    >
      <h2>📈 Growth Planning</h2>

      <div :class="$style.section">
        <h3>Scaling Scenarios</h3>
        <div :class="$style.inputRow">
          <label>Current Monthly Output:</label>
          <input
            v-model.number="growth.currentOutput"
            type="number"
            step="1"
          >
          <span :class="$style.unit">instruments</span>
        </div>
        <div :class="$style.inputRow">
          <label>Target Monthly Output:</label>
          <input
            v-model.number="growth.targetOutput"
            type="number"
            step="1"
          >
          <span :class="$style.unit">instruments</span>
        </div>
        <div :class="$style.inputRow">
          <label>Hours per Instrument:</label>
          <input
            v-model.number="growth.hoursPerUnit"
            type="number"
            step="1"
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
  </div>
</template>

<script setup lang="ts">
import { ref, useCssModule } from 'vue'
import AmortizationSection from './business/AmortizationSection.vue'
import PricingStrategyPanel from './business/PricingStrategyPanel.vue'
import {
  useStartupCalculator,
  useCostingCalculator,
  usePricingCalculator,
  useCashflowCalculator,
  useGrowthCalculator
} from './business-calculator'

// =============================================================================
// CSS Module
// =============================================================================

const $style = useCssModule()

// =============================================================================
// Tab State
// =============================================================================

const tabs = [
  { id: 'startup', label: '🚀 Startup' },
  { id: 'costing', label: '🎸 Costing' },
  { id: 'pricing', label: '🏷️ Pricing' },
  { id: 'cashflow', label: '💰 Cash Flow' },
  { id: 'growth', label: '📈 Growth' }
]

const activeTab = ref('startup')

// =============================================================================
// Composables
// =============================================================================

const {
  startup,
  showAmortization,
  totalEquipment,
  monthlyOverhead,
  firstYearCost,
  monthlyPayment,
  totalLoanPayment,
  totalInterest,
  amortizationSchedule
} = useStartupCalculator()

const {
  costing,
  totalMaterials,
  totalHours,
  totalLabor,
  overheadAllocation,
  totalCost
} = useCostingCalculator(monthlyOverhead)

const {
  pricing,
  sellingPrice,
  profit,
  breakEvenUnits
} = usePricingCalculator(firstYearCost)

const {
  cashflow,
  monthlyRevenue,
  netIncome
} = useCashflowCalculator()

const {
  growth,
  currentMonthlyHours,
  targetMonthlyHours,
  growthInsight
} = useGrowthCalculator()

// =============================================================================
// Helpers
// =============================================================================

function formatCurrency(value: number): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}
</script>

<style module src="./business-calculator/BusinessCalculator.module.css" />
