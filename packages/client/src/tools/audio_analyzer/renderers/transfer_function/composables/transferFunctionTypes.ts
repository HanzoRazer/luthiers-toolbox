/**
 * TransferFunctionRenderer types.
 */

export interface TransferFunctionPoint {
  freq: number
  mag: number      // Linear magnitude
  phase: number    // Degrees
}

export interface ParsedODSMetadata {
  analysisType?: string
  nModes?: number
  freqMin?: number
  freqMax?: number
}

export interface ParsedODS {
  points: TransferFunctionPoint[]
  metadata?: ParsedODSMetadata
}

export interface PeakInfo {
  freq: number
  mag: number
}
