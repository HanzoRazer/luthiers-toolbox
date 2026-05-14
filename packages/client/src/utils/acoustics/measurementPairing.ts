/**
 * Measurement Pairing Utilities
 *
 * Dev Order 25: Evaluate estimate/measurement pairing status.
 * Shows which metrics are ready for residual preview.
 * Does NOT calibrate or predict.
 */

import type { AcousticState } from '@/types/acoustics'
import type { MeasuredResponse } from '@/types/measurements'
import type {
  PairingStatus,
  MeasurementPairingMetric,
  MeasurementPairingStatus,
} from '@/types/measurementPairing'

interface EvaluatePairingParams {
  id: string
  label: string
  acousticState: AcousticState | null
  measuredResponse: MeasuredResponse | null
}

/**
 * Determine pairing status for a single metric.
 */
function getPairingStatus(
  estimateValue: number | undefined,
  measurementValue: number | undefined
): PairingStatus {
  const hasEstimate = estimateValue !== undefined
  const hasMeasurement = measurementValue !== undefined

  if (hasEstimate && hasMeasurement) return 'paired'
  if (hasEstimate && !hasMeasurement) return 'estimate_only'
  if (!hasEstimate && hasMeasurement) return 'measurement_only'
  return 'missing'
}

/**
 * Evaluate measurement pairing status for an aperture.
 */
export function evaluateMeasurementPairing(
  params: EvaluatePairingParams
): MeasurementPairingStatus {
  const { id, label, acousticState, measuredResponse } = params

  const metrics: MeasurementPairingMetric[] = []

  // Helmholtz frequency pairing
  const helmholtzEstimate = acousticState?.estimatedHelmholtzHz
  const helmholtzMeasured = measuredResponse?.measuredHelmholtzHz
  metrics.push({
    id: `${id}-helmholtz`,
    label: 'Helmholtz Frequency',
    estimateLabel: 'estimatedHelmholtzHz',
    measurementLabel: 'measuredHelmholtzHz',
    status: getPairingStatus(helmholtzEstimate, helmholtzMeasured),
    estimateValue: helmholtzEstimate,
    measurementValue: helmholtzMeasured,
    unit: 'Hz',
  })

  // Q factor pairing
  const qEstimate = acousticState?.qEstimate
  const qMeasured = measuredResponse?.measuredQ
  metrics.push({
    id: `${id}-q`,
    label: 'Q Factor',
    estimateLabel: 'qEstimate',
    measurementLabel: 'measuredQ',
    status: getPairingStatus(qEstimate, qMeasured),
    estimateValue: qEstimate,
    measurementValue: qMeasured,
    unit: '',
  })

  // Calculate summary counts
  let pairedCount = 0
  let availableCount = 0
  let missingCount = 0

  for (const metric of metrics) {
    switch (metric.status) {
      case 'paired':
        pairedCount++
        availableCount++
        break
      case 'estimate_only':
      case 'measurement_only':
        availableCount++
        break
      case 'missing':
        missingCount++
        break
    }
  }

  return {
    id,
    label,
    metrics,
    pairedCount,
    availableCount,
    missingCount,
    readyForResidualPreview: pairedCount > 0,
  }
}
