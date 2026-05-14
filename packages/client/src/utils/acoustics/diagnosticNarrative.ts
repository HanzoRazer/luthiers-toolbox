/**
 * Diagnostic Narrative Summary Utility
 *
 * Dev Order 34: Generates deterministic human-readable summaries
 * from residual interpretation, trend, stability, and coherence layers.
 *
 * Rule-based templates only — does NOT calibrate, validate, optimize, or predict.
 */

import type { ResidualInterpretationSummary } from '@/types/residualInterpretation'
import type { ResidualTrendSummary } from '@/types/residualTrend'
import type { ResidualStabilitySummary } from '@/types/residualStability'
import type { ResidualCoherenceSummary } from '@/types/residualCoherence'
import type { DiagnosticNarrativeTone, DiagnosticNarrativeSummary } from '@/types/diagnosticNarrative'

const PROVENANCE_REMINDER =
  'All estimates remain low-confidence first-order approximations and are not calibrated predictions.'

const CAUTION_TEXT =
  'Diagnostic narratives summarize existing observational layers only. They do not calibrate, validate, correct, or optimize the model.'

export function generateDiagnosticNarrative(params: {
  id: string
  label: string
  interpretation: ResidualInterpretationSummary
  trend: ResidualTrendSummary
  stability: ResidualStabilitySummary
  coherence: ResidualCoherenceSummary
}): DiagnosticNarrativeSummary {
  const { id, label, trend, stability, coherence } = params

  const tone: DiagnosticNarrativeTone = coherence.level

  switch (tone) {
    case 'insufficient':
      return {
        id,
        label,
        tone,
        narrative:
          'Insufficient paired residual observations are available to summarize diagnostic behavior.',
        supportingObservations: [
          'No estimate/measurement residual pairs available',
          'Residual interpretation unavailable',
        ],
        caution: CAUTION_TEXT,
        provenanceReminder: PROVENANCE_REMINDER,
      }

    case 'sparse':
      return {
        id,
        label,
        tone,
        narrative:
          'Residual observations remain sparse under current assumptions. Additional paired measurements are required before broader diagnostic patterns can be assessed.',
        supportingObservations: [
          'Only one paired residual available',
          'Trend information remains limited',
        ],
        caution: CAUTION_TEXT,
        provenanceReminder: PROVENANCE_REMINDER,
      }

    case 'coherent':
      return buildCoherentNarrative(id, label, trend, stability)

    case 'mixed':
      return buildMixedNarrative(id, label, trend, stability)
  }
}

function buildCoherentNarrative(
  id: string,
  label: string,
  trend: ResidualTrendSummary,
  stability: ResidualStabilitySummary
): DiagnosticNarrativeSummary {
  const observations: string[] = [
    'Residual directions are consistent',
    'No large residuals observed',
    'Residual pattern classified as stable',
  ]

  // Add trend-specific observation
  if (trend.direction === 'estimate_low') {
    observations.push('Measurements are generally higher than estimates')
  } else if (trend.direction === 'estimate_high') {
    observations.push('Measurements are generally lower than estimates')
  }

  return {
    id,
    label,
    tone: 'coherent',
    narrative:
      'Residual observations appear internally coherent under current assumptions, though all estimates remain low-confidence first-order approximations.',
    supportingObservations: observations,
    caution: CAUTION_TEXT,
    provenanceReminder: PROVENANCE_REMINDER,
  }
}

function buildMixedNarrative(
  id: string,
  label: string,
  trend: ResidualTrendSummary,
  stability: ResidualStabilitySummary
): DiagnosticNarrativeSummary {
  const observations: string[] = []

  // Add observations for whichever mixed conditions are true
  if (trend.direction === 'mixed') {
    observations.push('Residual directions are mixed')
  }

  if (stability.largeResidualCount > 0) {
    observations.push('Large residuals detected')
  }

  if (stability.level === 'volatile') {
    observations.push('Residual pattern classified as volatile')
  }

  // Ensure at least one observation if mixed for other reasons
  if (observations.length === 0) {
    observations.push('Residual pattern appears inconsistent')
  }

  return {
    id,
    label,
    tone: 'mixed',
    narrative:
      'Residual observations appear mixed or divergent under current assumptions and may reflect incompatible assumptions, measurement variation, or limits of the first-order estimate model.',
    supportingObservations: observations,
    caution: CAUTION_TEXT,
    provenanceReminder: PROVENANCE_REMINDER,
  }
}

export function getNarrativeToneLabel(tone: DiagnosticNarrativeTone): string {
  switch (tone) {
    case 'insufficient':
      return 'Insufficient Narrative'
    case 'sparse':
      return 'Sparse Narrative'
    case 'coherent':
      return 'Coherent Narrative'
    case 'mixed':
      return 'Mixed Narrative'
  }
}

export function getNarrativeGateColor(tone: DiagnosticNarrativeTone): 'green' | 'yellow' | 'red' {
  switch (tone) {
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
