/**
 * Calibration Readiness Utilities
 *
 * Dev Order 22: Evaluate whether data is sufficient for future calibration.
 * This does NOT perform calibration — it only checks readiness.
 */

import type { ApertureGeometryLike } from '@/types/acoustics'
import type { MeasuredResponse } from '@/types/measurements'
import type {
  CalibrationReadiness,
  CalibrationReadinessGate,
  CalibrationReadinessDiagnostic,
} from '@/types/calibration'

interface EvaluateParams {
  referenceGeometry?: ApertureGeometryLike | null
  candidateGeometry?: ApertureGeometryLike | null
  referenceMeasured?: MeasuredResponse | null
  candidateMeasured?: MeasuredResponse | null
}

/**
 * Evaluate whether current comparison data is sufficient for future calibration.
 */
export function evaluateCalibrationReadiness(params: EvaluateParams): CalibrationReadiness {
  const { referenceGeometry, candidateGeometry, referenceMeasured, candidateMeasured } = params

  const diagnostics: CalibrationReadinessDiagnostic[] = []
  const missingFields: string[] = []
  const warnings: string[] = []

  // Check geometry presence
  const hasRefGeo = !!referenceGeometry
  const hasCandGeo = !!candidateGeometry

  if (!hasRefGeo) {
    diagnostics.push({
      id: 'missing-ref-geometry',
      gate: 'red',
      message: 'Reference aperture geometry is missing.',
      recommendedAction: 'Compute reference aperture geometry first.',
    })
    missingFields.push('Reference geometry')
  }

  if (!hasCandGeo) {
    diagnostics.push({
      id: 'missing-cand-geometry',
      gate: 'red',
      message: 'Candidate aperture geometry is missing.',
      recommendedAction: 'Compute candidate aperture geometry first.',
    })
    missingFields.push('Candidate geometry')
  }

  // Check measured response presence
  const refHelmholtz = referenceMeasured?.measuredHelmholtzHz
  const refQ = referenceMeasured?.measuredQ
  const refPeak = referenceMeasured?.dominantPeakHz

  const candHelmholtz = candidateMeasured?.measuredHelmholtzHz
  const candQ = candidateMeasured?.measuredQ
  const candPeak = candidateMeasured?.dominantPeakHz

  const hasRefHelmholtz = refHelmholtz !== undefined
  const hasRefQ = refQ !== undefined
  const hasRefPeak = refPeak !== undefined
  const hasCandHelmholtz = candHelmholtz !== undefined
  const hasCandQ = candQ !== undefined
  const hasCandPeak = candPeak !== undefined

  const hasAnyRefMeasured = hasRefHelmholtz || hasRefQ || hasRefPeak
  const hasAnyCandMeasured = hasCandHelmholtz || hasCandQ || hasCandPeak

  // Check comparable metrics
  const hasComparableHelmholtz = hasRefHelmholtz && hasCandHelmholtz
  const hasComparableQ = hasRefQ && hasCandQ
  const hasComparablePeak = hasRefPeak && hasCandPeak
  const hasAnyComparable = hasComparableHelmholtz || hasComparableQ || hasComparablePeak

  // RED: No measurements at all
  if (!hasAnyRefMeasured && !hasAnyCandMeasured) {
    diagnostics.push({
      id: 'no-measurements',
      gate: 'red',
      message: 'No measured response data attached to either aperture.',
      recommendedAction: 'Enter measured Helmholtz and Q values for both apertures.',
    })
    missingFields.push('Reference measured response')
    missingFields.push('Candidate measured response')
  }

  // RED: No comparable metric
  if ((hasAnyRefMeasured || hasAnyCandMeasured) && !hasAnyComparable) {
    diagnostics.push({
      id: 'no-comparable-metric',
      gate: 'red',
      message: 'No comparable measured metric exists between reference and candidate.',
      recommendedAction: 'Enter the same measurement type for both apertures.',
    })
  }

  // YELLOW: One-sided measurements
  if (hasAnyRefMeasured && !hasAnyCandMeasured) {
    diagnostics.push({
      id: 'ref-only-measured',
      gate: 'yellow',
      message: 'Only reference has measured data.',
      recommendedAction: 'Enter measurements for the candidate aperture.',
    })
    warnings.push('Candidate measurements missing')
  }

  if (hasAnyCandMeasured && !hasAnyRefMeasured) {
    diagnostics.push({
      id: 'cand-only-measured',
      gate: 'yellow',
      message: 'Only candidate has measured data.',
      recommendedAction: 'Enter measurements for the reference aperture.',
    })
    warnings.push('Reference measurements missing')
  }

  // YELLOW: Helmholtz without Q or vice versa
  if (hasComparableHelmholtz && !hasComparableQ) {
    diagnostics.push({
      id: 'helmholtz-no-q',
      gate: 'yellow',
      message: 'Helmholtz frequency is comparable but Q factor is missing.',
      recommendedAction: 'Enter Q factor for both apertures.',
    })
    warnings.push('Q factor missing for full calibration')
    if (!hasRefQ) missingFields.push('Reference Q factor')
    if (!hasCandQ) missingFields.push('Candidate Q factor')
  }

  if (hasComparableQ && !hasComparableHelmholtz) {
    diagnostics.push({
      id: 'q-no-helmholtz',
      gate: 'yellow',
      message: 'Q factor is comparable but Helmholtz frequency is missing.',
      recommendedAction: 'Enter Helmholtz frequency for both apertures.',
    })
    warnings.push('Helmholtz frequency missing for full calibration')
    if (!hasRefHelmholtz) missingFields.push('Reference Helmholtz')
    if (!hasCandHelmholtz) missingFields.push('Candidate Helmholtz')
  }

  // YELLOW: Only dominant peak
  if (hasComparablePeak && !hasComparableHelmholtz && !hasComparableQ) {
    diagnostics.push({
      id: 'peak-only',
      gate: 'yellow',
      message: 'Only dominant peak frequency is comparable.',
      recommendedAction: 'Enter Helmholtz and Q for richer calibration data.',
    })
    warnings.push('Only peak frequency available')
  }

  // YELLOW: Manual source
  const refSource = referenceMeasured?.source
  const candSource = candidateMeasured?.source

  if (hasAnyComparable && (refSource === 'manual' || candSource === 'manual')) {
    diagnostics.push({
      id: 'manual-source',
      gate: 'yellow',
      message: 'Measurement source is manual entry.',
      recommendedAction: 'Manual measurements are valid but less traceable than imported data.',
    })
    warnings.push('Manual entry measurements')
  }

  // YELLOW: Unknown method
  const refMethod = referenceMeasured?.method
  const candMethod = candidateMeasured?.method

  if (hasAnyComparable && (refMethod === 'unknown' || candMethod === 'unknown')) {
    diagnostics.push({
      id: 'unknown-method',
      gate: 'yellow',
      message: 'Measurement method is unknown.',
      recommendedAction: 'Specify measurement method for better provenance.',
    })
    warnings.push('Unknown measurement method')
  }

  // Determine overall gate
  let overallGate: CalibrationReadinessGate = 'green'

  const hasRed = diagnostics.some((d) => d.gate === 'red')
  const hasYellow = diagnostics.some((d) => d.gate === 'yellow')

  if (hasRed) {
    overallGate = 'red'
  } else if (hasYellow) {
    overallGate = 'yellow'
  }

  // Ready for calibration only if green
  const readyForCalibration = overallGate === 'green'

  return {
    overallGate,
    diagnostics,
    readyForCalibration,
    missingFields,
    warnings,
  }
}
