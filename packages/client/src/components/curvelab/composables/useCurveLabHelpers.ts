/**
 * CurveLab helper functions.
 */
import type { ValidationIssue } from './curveLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CurveLabHelpersReturn {
  formatNumber: (value: number | null | undefined) => string
  severityClass: (level: ValidationIssue['severity']) => string
}

// ============================================================================
// Composable
// ============================================================================

export function useCurveLabHelpers(): CurveLabHelpersReturn {
  function formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined) return '—'
    return Number(value).toFixed(3).replace(/\.000$/, '.0')
  }

  function severityClass(level: ValidationIssue['severity']): string {
    if (level === 'error') return 'text-rose-700'
    if (level === 'warning') return 'text-amber-700'
    return 'text-slate-500'
  }

  return {
    formatNumber,
    severityClass
  }
}
