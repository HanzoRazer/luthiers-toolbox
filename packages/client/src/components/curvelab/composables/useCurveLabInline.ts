/**
 * CurveLab inline geometry report composable.
 */
import type { Ref, ComputedRef } from 'vue'
import { fetchCurveReport } from '@/api/curvelab'
import type {
  CurveBiarcEntity,
  CurvePoint,
  CurvePreflightResponse,
  CurveUnits
} from './curveLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CurveLabInlineReturn {
  runInlineReport: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useCurveLabInline(
  inlinePoints: ComputedRef<CurvePoint[]>,
  hasInlineGeometry: ComputedRef<boolean>,
  units: CurveUnits,
  tolerance: Ref<number>,
  layer: Ref<string>,
  biarcEntities: CurveBiarcEntity[] | null,
  inlineBusy: Ref<boolean>,
  inlineResponse: Ref<CurvePreflightResponse | null>,
  inlineError: Ref<string | null>
): CurveLabInlineReturn {
  async function runInlineReport(): Promise<void> {
    if (!hasInlineGeometry.value) return

    inlineBusy.value = true
    inlineError.value = null

    try {
      const res = await fetchCurveReport({
        points: inlinePoints.value,
        units,
        tolerance_mm: tolerance.value,
        layer: layer.value,
        biarc_entities: biarcEntities?.length ? (biarcEntities as any) : undefined
      })
      inlineResponse.value = res
    } catch (err: any) {
      inlineError.value = err?.message || 'Failed to run curve report'
    } finally {
      inlineBusy.value = false
    }
  }

  return {
    runInlineReport
  }
}
