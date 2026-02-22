/**
 * CurveLab file validation and auto-fix composable.
 */
import type { Ref, ComputedRef } from 'vue'
import { autoFixDxf, validateDxf } from '@/api/curvelab'
import type { AutoFixOption, ValidationReport } from './curveLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CurveLabFileReturn {
  runFileValidation: () => Promise<void>
  runAutoFix: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useCurveLabFile(
  filename: string,
  hasDxf: ComputedRef<boolean>,
  workingDxf: Ref<string | null>,
  selectedFixes: Ref<AutoFixOption[]>,
  fileBusy: Ref<boolean>,
  fileResponse: Ref<ValidationReport | null>,
  fileError: Ref<string | null>,
  autoFixBusy: Ref<boolean>,
  fixedDownload: Ref<string | null>,
  emit: (event: 'auto-fix', payload: any) => void
): CurveLabFileReturn {
  async function runFileValidation(): Promise<void> {
    if (!hasDxf.value || !workingDxf.value) return

    fileBusy.value = true
    fileError.value = null

    try {
      const res = await validateDxf(workingDxf.value, filename)
      fileResponse.value = res
    } catch (err: any) {
      fileError.value = err?.message || 'Failed to validate DXF'
    } finally {
      fileBusy.value = false
    }
  }

  async function runAutoFix(): Promise<void> {
    if (!hasDxf.value || !workingDxf.value || !selectedFixes.value.length) return

    autoFixBusy.value = true
    fileError.value = null

    try {
      const res = await autoFixDxf({
        dxf_base64: workingDxf.value,
        filename,
        fixes: selectedFixes.value
      })
      fixedDownload.value = res.fixed_dxf_base64
      fileResponse.value = res.validation_report
      workingDxf.value = res.fixed_dxf_base64
      emit('auto-fix', res)
    } catch (err: any) {
      fileError.value = err?.message || 'Auto-fix failed'
    } finally {
      autoFixBusy.value = false
    }
  }

  return {
    runFileValidation,
    runAutoFix
  }
}
