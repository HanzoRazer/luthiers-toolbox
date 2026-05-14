/**
 * Calibration Residual Utilities
 *
 * Dev Order 23: Create residual preview between estimates and measurements.
 * Dev Order 29: Added estimate provenance annotation.
 * Does NOT calibrate, fit, correct, or predict.
 */

import type { AcousticState } from '@/types/acoustics'
import type { MeasuredResponse } from '@/types/measurements'
import type {
  CalibrationResidual,
  CalibrationResidualPreview,
  ResidualEstimateProvenance,
} from '@/types/calibrationResiduals'

interface CreateResidualPreviewParams {
  id: string
  label: string
  acousticState: AcousticState | null
  measuredResponse: MeasuredResponse | null
}

/**
 * Create a residual for a single metric.
 */
function createResidual(params: {
  id: string
  label: string
  estimated: number | undefined
  measured: number | undefined
  unit: string
}): CalibrationResidual {
  const { id, label, estimated, measured, unit } = params

  if (estimated === undefined && measured === undefined) {
    return {
      id,
      label,
      unit,
      available: false,
      message: 'Neither estimate nor measurement available',
    }
  }

  if (estimated === undefined) {
    return {
      id,
      label,
      measuredValue: measured,
      unit,
      available: false,
      message: 'Estimate unavailable',
    }
  }

  if (measured === undefined) {
    return {
      id,
      label,
      estimatedValue: estimated,
      unit,
      available: false,
      message: 'Measurement unavailable',
    }
  }

  const residual = measured - estimated
  const percentResidual = estimated !== 0 ? (residual / estimated) * 100 : null

  return {
    id,
    label,
    estimatedValue: estimated,
    measuredValue: measured,
    residual,
    percentResidual,
    unit,
    available: true,
  }
}

/**
 * Create a calibration residual preview for one aperture.
 */
export function createCalibrationResidualPreview(
  params: CreateResidualPreviewParams
): CalibrationResidualPreview {
  const { id, label, acousticState, measuredResponse } = params

  const notes: string[] = []
  const residuals: CalibrationResidual[] = []

  // Helmholtz frequency residual
  const helmholtzResidual = createResidual({
    id: `${id}-helmholtz`,
    label: 'Helmholtz Frequency',
    estimated: acousticState?.estimatedHelmholtzHz,
    measured: measuredResponse?.measuredHelmholtzHz,
    unit: 'Hz',
  })
  residuals.push(helmholtzResidual)

  // Q factor residual
  const qResidual = createResidual({
    id: `${id}-q`,
    label: 'Q Factor',
    estimated: acousticState?.qEstimate,
    measured: measuredResponse?.measuredQ,
    unit: '',
  })
  residuals.push(qResidual)

  // Dominant peak residual (no estimated equivalent yet)
  const peakResidual: CalibrationResidual = {
    id: `${id}-peak`,
    label: 'Dominant Peak',
    measuredValue: measuredResponse?.dominantPeakHz,
    unit: 'Hz',
    available: false,
    message: 'No estimated equivalent available yet',
  }
  residuals.push(peakResidual)

  const hasAvailableResiduals = residuals.some((r) => r.available)

  if (!hasAvailableResiduals) {
    notes.push(
      'No residuals available yet. Attach measured response data and acoustic estimates to preview calibration gaps.'
    )
  }

  // Dev Order 29: Attach provenance when residuals are available
  let provenance: ResidualEstimateProvenance | undefined
  if (hasAvailableResiduals && acousticState) {
    provenance = {
      estimateMethod: acousticState.estimateMethod,
      estimateSource: acousticState.source,
      estimateConfidence: acousticState.confidence,
      estimateAssumptions: acousticState.assumptions,
      estimateWarnings: acousticState.warnings ?? [],
    }
  }

  return {
    id,
    label,
    residuals,
    hasAvailableResiduals,
    notes,
    provenance,
  }
}
