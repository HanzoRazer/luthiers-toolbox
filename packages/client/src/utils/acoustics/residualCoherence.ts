/**
 * Residual Coherence Summary Utility
 *
 * Dev Order 33: Synthesizes interpretation, trend, and stability
 * into a consolidated observational coherence summary.
 *
 * Descriptive only — does NOT calibrate, validate, fit, or correct the model.
 */

import type { ResidualInterpretationSummary } from '@/types/residualInterpretation'
import type { ResidualTrendSummary } from '@/types/residualTrend'
import type { ResidualStabilitySummary } from '@/types/residualStability'
import type { ResidualCoherenceLevel, ResidualCoherenceSummary } from '@/types/residualCoherence'

export function summarizeResidualCoherence(params: {
  id: string
  label: string
  interpretation: ResidualInterpretationSummary
  trend: ResidualTrendSummary
  stability: ResidualStabilitySummary
}): ResidualCoherenceSummary {
  const { id, label, interpretation, trend, stability } = params

  const baseNotes = [
    'Residual coherence summarizes observational diagnostic layers only.',
    'It does not calibrate, validate, or correct the model.',
  ]

  // Check insufficient first
  if (stability.level === 'insufficient') {
    return {
      id,
      label,
      level: 'insufficient',
      interpretationLevel: interpretation.overallLevel,
      trendDirection: trend.direction,
      stabilityLevel: stability.level,
      message: 'Insufficient paired residuals are available for coherence assessment.',
      caution: 'Attach measurements to enable coherence evaluation.',
      notes: baseNotes,
    }
  }

  // Check sparse
  if (stability.level === 'sparse') {
    return {
      id,
      label,
      level: 'sparse',
      interpretationLevel: interpretation.overallLevel,
      trendDirection: trend.direction,
      stabilityLevel: stability.level,
      message: 'Residual observations remain sparse under current assumptions.',
      caution: 'Additional measurements may clarify coherence patterns.',
      notes: baseNotes,
    }
  }

  // Check mixed conditions: volatile stability, mixed trend, or large residuals
  const isVolatile = stability.level === 'volatile'
  const isMixedTrend = trend.direction === 'mixed'
  const hasLargeResiduals = stability.largeResidualCount > 0

  if (isVolatile || isMixedTrend || hasLargeResiduals) {
    return {
      id,
      label,
      level: 'mixed',
      interpretationLevel: interpretation.overallLevel,
      trendDirection: trend.direction,
      stabilityLevel: stability.level,
      message: 'Residual behavior appears divergent or inconsistent under current assumptions.',
      caution: 'Mixed coherence does not indicate model failure — it describes observed variability.',
      notes: baseNotes,
    }
  }

  // Default to coherent: stable + non-mixed trend + no large residuals
  return {
    id,
    label,
    level: 'coherent',
    interpretationLevel: interpretation.overallLevel,
    trendDirection: trend.direction,
    stabilityLevel: stability.level,
    message: 'Residual behavior appears internally consistent under current assumptions.',
    caution: 'Coherent residual behavior does not imply calibrated accuracy.',
    notes: baseNotes,
  }
}

export function getCoherenceLevelLabel(level: ResidualCoherenceLevel): string {
  switch (level) {
    case 'insufficient':
      return 'Insufficient'
    case 'sparse':
      return 'Sparse'
    case 'coherent':
      return 'Coherent Pattern'
    case 'mixed':
      return 'Mixed Pattern'
  }
}

export function getCoherenceGateColor(level: ResidualCoherenceLevel): 'green' | 'yellow' | 'red' {
  switch (level) {
    case 'insufficient':
      return 'yellow'
    case 'sparse':
      return 'yellow'
    case 'coherent':
      return 'green'
    case 'mixed':
      return 'red'
  }
}
