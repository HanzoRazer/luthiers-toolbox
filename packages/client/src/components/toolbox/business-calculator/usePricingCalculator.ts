/**
 * Composable for pricing strategy calculations.
 *
 * Uses TARGET GROSS MARGIN formula:
 *   price = cost / (1 - targetMargin / 100)
 *
 * Example: $1000 cost @ 30% target margin = $1428.57 price
 *   Actual margin: ($1428.57 - $1000) / $1428.57 = 30%
 *
 * This differs from MARKUP formula which would give:
 *   $1000 * 1.30 = $1300 (only 23.08% actual margin)
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface PricingData {
  buildCost: number
  targetGrossMargin: number
}

export interface PricingCalculatorState {
  pricing: Ref<PricingData>
  sellingPrice: ComputedRef<number>
  profit: ComputedRef<number>
  actualMarginPct: ComputedRef<number>
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
    targetGrossMargin: 50
  })

  const sellingPrice = computed(() => {
    const margin = pricing.value.targetGrossMargin
    if (margin >= 100) return Infinity
    if (margin < 0) return pricing.value.buildCost
    return Math.round((pricing.value.buildCost / (1 - margin / 100)) * 100) / 100
  })

  const profit = computed(() =>
    sellingPrice.value - pricing.value.buildCost
  )

  const actualMarginPct = computed(() => {
    if (sellingPrice.value <= 0) return 0
    return Math.round(((sellingPrice.value - pricing.value.buildCost) / sellingPrice.value) * 10000) / 100
  })

  const breakEvenUnits = computed(() =>
    Math.ceil(firstYearCost.value / profit.value)
  )

  return {
    pricing,
    sellingPrice,
    profit,
    actualMarginPct,
    breakEvenUnits
  }
}
