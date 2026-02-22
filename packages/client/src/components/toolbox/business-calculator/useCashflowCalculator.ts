/**
 * Composable for cash flow projection calculations.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface CashflowData {
  unitsSold: number
  avgPrice: number
  fixedCosts: number
}

export interface CashflowCalculatorState {
  cashflow: Ref<CashflowData>
  monthlyRevenue: ComputedRef<number>
  netIncome: ComputedRef<number>
}

// ============================================================================
// Composable
// ============================================================================

export function useCashflowCalculator(): CashflowCalculatorState {
  const cashflow = ref<CashflowData>({
    unitsSold: 4,
    avgPrice: 5000,
    fixedCosts: 1200
  })

  const monthlyRevenue = computed(() =>
    cashflow.value.unitsSold * cashflow.value.avgPrice
  )

  const netIncome = computed(() =>
    monthlyRevenue.value - cashflow.value.fixedCosts
  )

  return {
    cashflow,
    monthlyRevenue,
    netIncome
  }
}
