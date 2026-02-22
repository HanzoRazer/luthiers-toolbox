/**
 * CurveLab types for composables.
 */
import type {
  AutoFixOption,
  CurveBiarcEntity,
  CurvePoint,
  CurvePreflightResponse,
  CurveUnits,
  ValidationIssue,
  ValidationReport
} from '@/types/curvelab'

// Re-export for convenience
export type {
  AutoFixOption,
  CurveBiarcEntity,
  CurvePoint,
  CurvePreflightResponse,
  CurveUnits,
  ValidationIssue,
  ValidationReport
}

// ============================================================================
// Fix Option Definition
// ============================================================================

export interface FixOptionDef {
  id: AutoFixOption
  label: string
  helper: string
}

// ============================================================================
// Props Interface
// ============================================================================

export interface CurveLabProps {
  open: boolean
  points: Array<[number, number]>
  units: CurveUnits
  layer: string
  biarcEntities: CurveBiarcEntity[] | null
  dxfBase64: string | null
  filename: string
}
