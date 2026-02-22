/**
 * Composable for pricing strategy calculations.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface PricingData {
  buildCost: number
  margin: number
}

export interface PricingCalculatorState {
  pricing: Ref<PricingData>
  sellingPrice: ComputedRef<number>
  profit: ComputedRef<number>
  breakEvenUnits: ComputedRef<number>
}

// ============================================================================
// Composable
// ============================================================================

export function usePricingCalculator(
  firstYearCost: ComputedRef<number>
): PricingCalculatorState {
  const pricing = ref<PricingData>({
    buildCost: 3500,
    margin: 50
  })

  const sellingPrice = computed(() =>
    pricing.value.buildCost * (1 + pricing.value.margin / 100)
  )

  const profit = computed(() =>
    sellingPrice.value - pricing.value.buildCost
  )

  const breakEvenUnits = computed(() =>
    Math.ceil(firstYearCost.value / profit.value)
  )

  return {
    pricing,
    sellingPrice,
    profit,
    breakEvenUnits
  }
}
