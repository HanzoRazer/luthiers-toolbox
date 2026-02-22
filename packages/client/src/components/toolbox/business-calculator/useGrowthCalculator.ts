/**
 * Composable for growth planning calculations.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface GrowthData {
  currentOutput: number
  targetOutput: number
  hoursPerUnit: number
}

export interface GrowthCalculatorState {
  growth: Ref<GrowthData>
  currentMonthlyHours: ComputedRef<number>
  targetMonthlyHours: ComputedRef<number>
  growthInsight: ComputedRef<string>
}

// ============================================================================
// Constants
// ============================================================================

const WORKABLE_HOURS_PER_MONTH = 160 // 40 hrs/week

// ============================================================================
// Composable
// ============================================================================

export function useGrowthCalculator(): GrowthCalculatorState {
  const growth = ref<GrowthData>({
    currentOutput: 4,
    targetOutput: 8,
    hoursPerUnit: 60
  })

  const currentMonthlyHours = computed(() =>
    growth.value.currentOutput * growth.value.hoursPerUnit
  )

  const targetMonthlyHours = computed(() =>
    growth.value.targetOutput * growth.value.hoursPerUnit
  )

  const growthInsight = computed(() => {
    if (targetMonthlyHours.value <= WORKABLE_HOURS_PER_MONTH) {
      return `✅ Achievable solo (${targetMonthlyHours.value}hrs < ${WORKABLE_HOURS_PER_MONTH}hrs/month)`
    } else {
      const additionalPeople = Math.ceil(
        (targetMonthlyHours.value - WORKABLE_HOURS_PER_MONTH) / WORKABLE_HOURS_PER_MONTH
      )
      return `⚠️ Need to hire ${additionalPeople} person(s) or reduce hours per unit`
    }
  })

  return {
    growth,
    currentMonthlyHours,
    targetMonthlyHours,
    growthInsight
  }
}
