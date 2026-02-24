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
    <StartupPlanningPanel
      v-if="activeTab === 'startup'"
      :startup="startup"
      :show-amortization="showAmortization"
      :total-equipment="totalEquipment"
      :monthly-overhead="monthlyOverhead"
      :monthly-payment="monthlyPayment"
      :total-interest="totalInterest"
      :total-loan-payment="totalLoanPayment"
      :amortization-schedule="amortizationSchedule"
      @update:startup="startup = $event"
      @update:show-amortization="showAmortization = $event"
    />

    <!-- Tab 2: Instrument Costing -->
    <InstrumentCostingPanel
      v-if="activeTab === 'costing'"
      :costing="costing"
      :total-materials="totalMaterials"
      :total-hours="totalHours"
      :total-labor="totalLabor"
      :overhead-allocation="overheadAllocation"
      :total-cost="totalCost"
      @update:costing="costing = $event"
    />

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
    <CashFlowPanel
      v-if="activeTab === 'cashflow'"
      :cashflow="cashflow"
      :monthly-revenue="monthlyRevenue"
      :net-income="netIncome"
      @update:cashflow="cashflow = $event"
    />

    <!-- Tab 5: Growth Planning -->
    <GrowthPlanningPanel
      v-if="activeTab === 'growth'"
      :growth="growth"
      :current-monthly-hours="currentMonthlyHours"
      :target-monthly-hours="targetMonthlyHours"
      :growth-insight="growthInsight"
      @update:growth="growth = $event"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * BusinessCalculator.vue - Business planning calculator for lutherie
 *
 * REFACTORED: Tab panels extracted for decomposition:
 * - StartupPlanningPanel: Equipment, facilities, financing
 * - InstrumentCostingPanel: Materials and labor costing
 * - PricingStrategyPanel: Pricing and break-even analysis
 * - CashFlowPanel: Cash flow projections
 * - GrowthPlanningPanel: Scaling scenarios
 */
import { ref, useCssModule } from 'vue'
import CashFlowPanel from './business/CashFlowPanel.vue'
import GrowthPlanningPanel from './business/GrowthPlanningPanel.vue'
import InstrumentCostingPanel from './business/InstrumentCostingPanel.vue'
import PricingStrategyPanel from './business/PricingStrategyPanel.vue'
import StartupPlanningPanel from './business/StartupPlanningPanel.vue'
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
</script>

<style module src="./business-calculator/BusinessCalculator.module.css" />
