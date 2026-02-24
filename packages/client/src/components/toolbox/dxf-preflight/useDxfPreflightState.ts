/**
 * State management for DXF Preflight Validator.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { ValidationReport, FixOptions } from './types'

export interface DxfPreflightState {
  selectedFile: Ref<File | null>
  fileInput: Ref<HTMLInputElement | null>
  validating: Ref<boolean>
  report: Ref<ValidationReport | null>
  error: Ref<string | null>
  fixes: Ref<FixOptions>
  fixedDxf: Ref<string | null>
  appliedFixes: Ref<string[]>
  autoFixing: Ref<boolean>
  hasFixableIssues: ComputedRef<boolean>
  hasOpenPolylines: ComputedRef<boolean>
  hasSelectedFixes: ComputedRef<boolean>
}

export function useDxfPreflightState(): DxfPreflightState {
  const selectedFile = ref<File | null>(null)
  const fileInput = ref<HTMLInputElement | null>(null)
  const validating = ref(false)
  const report = ref<ValidationReport | null>(null)
  const error = ref<string | null>(null)

  const fixes = ref<FixOptions>({
    convert_to_r12: false,
    close_open_polylines: false,
    set_units_mm: false,
    explode_splines: false
  })

  const fixedDxf = ref<string | null>(null)
  const appliedFixes = ref<string[]>([])
  const autoFixing = ref(false)

  const hasFixableIssues = computed(() => {
    if (!report.value) return false
    return report.value.issues.some(i => i.fix_available)
  })

  const hasOpenPolylines = computed(() => {
    if (!report.value) return false
    return report.value.issues.some(i => i.message.includes('Open'))
  })

  const hasSelectedFixes = computed(() => {
    return fixes.value.convert_to_r12 || fixes.value.close_open_polylines ||
           fixes.value.set_units_mm || fixes.value.explode_splines
  })

  return {
    selectedFile,
    fileInput,
    validating,
    report,
    error,
    fixes,
    fixedDxf,
    appliedFixes,
    autoFixing,
    hasFixableIssues,
    hasOpenPolylines,
    hasSelectedFixes
  }
}
