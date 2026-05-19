/**
 * Measurement Pairing Types
 *
 * Dev Order 25: Pairing status for estimate/measurement pairs.
 * Shows which metrics have both estimate and measurement available.
 * Does NOT calibrate or predict.
 */

/**
 * Status of a single estimate/measurement pair.
 */
export type PairingStatus =
  | 'paired'
  | 'estimate_only'
  | 'measurement_only'
  | 'missing'

/**
 * Individual metric pairing information.
 */
export interface MeasurementPairingMetric {
  id: string
  label: string
  estimateLabel: string
  measurementLabel: string
  status: PairingStatus
  estimateValue?: number
  measurementValue?: number
  unit?: string
}

/**
 * Full pairing status for one aperture.
 */
export interface MeasurementPairingStatus {
  id: string
  label: string
  metrics: MeasurementPairingMetric[]
  pairedCount: number
  availableCount: number
  missingCount: number
  readyForResidualPreview: boolean
}
