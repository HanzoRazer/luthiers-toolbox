<script setup lang="ts">
/**
 * ApertureComparisonPanel — Compare aperture geometries side-by-side
 *
 * Dev Order 12: Comparison panel for normalized aperture geometry comparison.
 * Dev Order 60: Added measurement archive integration for experimental workflow.
 *
 * Reference: round or oval (standard aperture API)
 * Candidate: dual_spiral (combined Carlos Jumbo defaults)
 *
 * Uses normalized ApertureGeometry contract for cross-type comparison.
 */
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { GateBadge, SectionLabel, PrerequisiteNotice } from '@/components/shared/workflow'
import { ApertureResultCard, type ApertureGeometry } from '@/components/shared/aperture'
import {
  AcousticStateCard,
  MeasuredResponseCard,
  MeasuredResponseDeltaCard,
  CalibrationReadinessCard,
  CalibrationResidualCard,
  MeasurementPairingStatusCard,
  HelmholtzEstimateCard,
  EstimateAssumptionSummaryCard,
  ResidualInterpretationCard,
  ResidualTrendCard,
  ResidualStabilityCard,
  ResidualCoherenceCard,
  DiagnosticNarrativeCard,
  SnapshotExchangeSection,
  MeasurementArchiveExchangeSection,
} from '@/components/shared/acoustics'
import {
  createGeometryAcousticState,
  createEmptyMeasuredResponse,
  evaluateCalibrationReadiness,
  createCalibrationResidualPreview,
  updateGeometryPreservingEstimates,
  evaluateMeasurementPairing,
  createEstimateAssumptionSummary,
  interpretResidualPreview,
  summarizeResidualTrend,
  classifyResidualStability,
  summarizeResidualCoherence,
  generateDiagnosticNarrative,
  createDiagnosticSnapshot,
  normalizeDiagnosticSnapshotForExport,
  createDiagnosticSnapshotExportMetadata,
  tryCreateArchiveFromDiagnosticContext,
  createGeometrySummary,
} from '@/utils/acoustics'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import type { AcousticState } from '@/types/acoustics'
import type { MeasuredResponse } from '@/types/measurements'
import type { HelmholtzEstimateResult } from '@/types/helmholtz'

// Types
type ReferenceType = 'round' | 'oval'

interface BodyStyleOption {
  value: string
  label: string
  diameter: number
}

interface StandardResponse {
  diameter_mm: number
  area_mm2?: number
  perimeter_mm?: number
  pa_ratio_mm_inv?: number
  gate: string
  notes: string[]
  soundhole_type: string
}

interface SpiralGeometryResponse {
  aperture_geometry: ApertureGeometry
  area_mm2: number
  perimeter_mm: number
  pa_ratio_mm_inv: number
}

interface DualSpiralResponse {
  upper: SpiralGeometryResponse
  lower: SpiralGeometryResponse
  total_area_mm2: number
}

// State
const referenceType = ref<ReferenceType>('round')
const bodyStyle = ref('dreadnought')
const bodyLengthMm = ref(508)
const customDiameterMm = ref<number | null>(null)
const useCustomDiameter = ref(false)
const ovalWidthMm = ref(80)
const ovalHeightMm = ref(110)

// API state
const API_BASE = '/api/instrument'
const bodyStyles = ref<BodyStyleOption[]>([])

const referenceLoading = ref(false)
const referenceError = ref('')
const referenceGeometry = ref<ApertureGeometry | null>(null)
const referenceGate = ref<'green' | 'yellow' | 'red'>('green')
const referenceNotes = ref<string[]>([])

const candidateLoading = ref(false)
const candidateError = ref('')
const candidateGeometry = ref<ApertureGeometry | null>(null)

// Reference type options
const referenceTypeOptions: { value: ReferenceType; label: string }[] = [
  { value: 'round', label: 'Round' },
  { value: 'oval', label: 'Oval' },
]

// Fetch body styles on mount
async function fetchBodyStyles() {
  try {
    const res = await fetch(`${API_BASE}/soundhole/body-styles`)
    if (!res.ok) throw new Error('Failed to fetch body styles')
    const data = await res.json()

    bodyStyles.value = data.body_styles.map((style: string) => ({
      value: style,
      label: style.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
      diameter: data.standard_diameters_mm?.[style] ?? 95,
    }))
  } catch (e) {
    console.error('Failed to fetch body styles:', e)
    bodyStyles.value = [
      { value: 'dreadnought', label: 'Dreadnought', diameter: 100 },
      { value: 'om_000', label: 'OM/000', diameter: 98 },
      { value: 'parlor', label: 'Parlor', diameter: 85 },
      { value: 'classical', label: 'Classical', diameter: 85 },
    ]
  }
}

// Compute reference geometry (standard aperture)
async function computeReference() {
  referenceLoading.value = true
  referenceError.value = ''

  try {
    const payload: Record<string, unknown> = {
      body_style: bodyStyle.value,
      body_length_mm: bodyLengthMm.value,
      soundhole_type: referenceType.value,
    }

    if (referenceType.value === 'round' && useCustomDiameter.value && customDiameterMm.value) {
      payload.custom_diameter_mm = customDiameterMm.value
    }
    if (referenceType.value === 'oval') {
      payload.custom_diameter_mm = ovalWidthMm.value
    }

    const res = await fetch(`${API_BASE}/soundhole`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'API error')
    }

    const data: StandardResponse = await res.json()

    // Convert to ApertureGeometry
    const area = data.area_mm2 ?? Math.PI * (data.diameter_mm / 2) ** 2
    const perimeter = data.perimeter_mm ?? Math.PI * data.diameter_mm

    referenceGeometry.value = {
      aperture_type: data.soundhole_type,
      area_mm2: area,
      perimeter_mm: perimeter,
      equivalent_diameter_mm: data.diameter_mm,
      pa_ratio_mm_inv: data.pa_ratio_mm_inv ?? perimeter / area,
      characteristic_width_mm: referenceType.value === 'oval' ? ovalWidthMm.value : null,
      path_length_mm: null,
    }

    referenceGate.value = data.gate === 'GREEN' ? 'green' : data.gate === 'YELLOW' ? 'yellow' : 'red'
    referenceNotes.value = data.notes
  } catch (e) {
    referenceError.value = e instanceof Error ? e.message : 'Unknown error'
    referenceGeometry.value = null
  } finally {
    referenceLoading.value = false
  }
}

// Compute candidate geometry (dual spiral combined)
async function computeCandidate() {
  candidateLoading.value = true
  candidateError.value = ''

  try {
    // Get Carlos Jumbo defaults
    const defaultRes = await fetch(`${API_BASE}/soundhole/spiral/default`)
    if (!defaultRes.ok) throw new Error('Failed to fetch spiral defaults')
    const defaultSpec = await defaultRes.json()

    // Compute geometry
    const geoRes = await fetch(`${API_BASE}/soundhole/spiral/geometry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(defaultSpec),
    })

    if (!geoRes.ok) {
      const errData = await geoRes.json()
      throw new Error(errData.detail || 'API error')
    }

    const data: DualSpiralResponse = await geoRes.json()

    // Combine upper + lower into single ApertureGeometry
    const upperGeo = data.upper.aperture_geometry
    const lowerGeo = data.lower.aperture_geometry

    const combinedArea = upperGeo.area_mm2 + lowerGeo.area_mm2
    const combinedPerimeter = upperGeo.perimeter_mm + lowerGeo.perimeter_mm
    const combinedPaRatio = combinedPerimeter / combinedArea
    const combinedEquivDiameter = 2 * Math.sqrt(combinedArea / Math.PI)
    const combinedPathLength =
      (upperGeo.path_length_mm ?? 0) + (lowerGeo.path_length_mm ?? 0)
    const avgCharWidth =
      ((upperGeo.characteristic_width_mm ?? 0) + (lowerGeo.characteristic_width_mm ?? 0)) / 2

    candidateGeometry.value = {
      aperture_type: 'dual_spiral',
      area_mm2: combinedArea,
      perimeter_mm: combinedPerimeter,
      equivalent_diameter_mm: combinedEquivDiameter,
      pa_ratio_mm_inv: combinedPaRatio,
      characteristic_width_mm: avgCharWidth || null,
      path_length_mm: combinedPathLength || null,
    }
  } catch (e) {
    candidateError.value = e instanceof Error ? e.message : 'Unknown error'
    candidateGeometry.value = null
  } finally {
    candidateLoading.value = false
  }
}

// Delta calculations
interface DeltaRow {
  metric: string
  reference: string
  candidate: string
  delta: string
}

const deltaTable = computed<DeltaRow[]>(() => {
  const ref = referenceGeometry.value
  const cand = candidateGeometry.value

  if (!ref || !cand) return []

  function formatDelta(refVal: number | null | undefined, candVal: number | null | undefined, decimals = 1): string {
    if (refVal == null || candVal == null) return '-'
    const diff = candVal - refVal
    const pct = refVal !== 0 ? (diff / refVal) * 100 : 0
    const sign = diff >= 0 ? '+' : ''
    return `${sign}${diff.toFixed(decimals)} (${sign}${pct.toFixed(1)}%)`
  }

  function formatVal(val: number | null | undefined, decimals = 1): string {
    if (val == null) return '-'
    return val.toFixed(decimals)
  }

  return [
    {
      metric: 'Area (mm²)',
      reference: formatVal(ref.area_mm2, 1),
      candidate: formatVal(cand.area_mm2, 1),
      delta: formatDelta(ref.area_mm2, cand.area_mm2, 1),
    },
    {
      metric: 'Perimeter (mm)',
      reference: formatVal(ref.perimeter_mm, 1),
      candidate: formatVal(cand.perimeter_mm, 1),
      delta: formatDelta(ref.perimeter_mm, cand.perimeter_mm, 1),
    },
    {
      metric: 'P:A Ratio (mm⁻¹)',
      reference: formatVal(ref.pa_ratio_mm_inv, 4),
      candidate: formatVal(cand.pa_ratio_mm_inv, 4),
      delta: formatDelta(ref.pa_ratio_mm_inv, cand.pa_ratio_mm_inv, 4),
    },
    {
      metric: 'Equiv. Diameter (mm)',
      reference: formatVal(ref.equivalent_diameter_mm, 1),
      candidate: formatVal(cand.equivalent_diameter_mm, 1),
      delta: formatDelta(ref.equivalent_diameter_mm, cand.equivalent_diameter_mm, 1),
    },
    {
      metric: 'Path Length (mm)',
      reference: formatVal(ref.path_length_mm, 1),
      candidate: formatVal(cand.path_length_mm, 1),
      delta: formatDelta(ref.path_length_mm, cand.path_length_mm, 1),
    },
    {
      metric: 'Char. Width (mm)',
      reference: formatVal(ref.characteristic_width_mm, 1),
      candidate: formatVal(cand.characteristic_width_mm, 1),
      delta: formatDelta(ref.characteristic_width_mm, cand.characteristic_width_mm, 1),
    },
  ]
})

// Acoustic state computations (Dev Order 15)
// Acoustic state (Dev Order 15, editable Dev Order 24)
const referenceAcousticState = ref<AcousticState | null>(null)
const candidateAcousticState = ref<AcousticState | null>(null)

function updateReferenceAcousticState(updated: AcousticState) {
  referenceAcousticState.value = updated
}

function updateCandidateAcousticState(updated: AcousticState) {
  candidateAcousticState.value = updated
}

// Watch geometry changes and update acoustic state (preserving manual estimates)
watch(
  referenceGeometry,
  (newGeo) => {
    if (!newGeo) {
      referenceAcousticState.value = null
      return
    }
    const newGeoState = createGeometryAcousticState({
      id: 'reference',
      label: 'Reference Aperture',
      apertureGeometry: newGeo,
    })
    if (referenceAcousticState.value) {
      referenceAcousticState.value = updateGeometryPreservingEstimates(
        referenceAcousticState.value,
        newGeoState
      )
    } else {
      referenceAcousticState.value = newGeoState
    }
  },
  { immediate: true }
)

watch(
  candidateGeometry,
  (newGeo) => {
    if (!newGeo) {
      candidateAcousticState.value = null
      return
    }
    const newGeoState = createGeometryAcousticState({
      id: 'candidate',
      label: 'Candidate Aperture',
      apertureGeometry: newGeo,
    })
    if (candidateAcousticState.value) {
      candidateAcousticState.value = updateGeometryPreservingEstimates(
        candidateAcousticState.value,
        newGeoState
      )
    } else {
      candidateAcousticState.value = newGeoState
    }
  },
  { immediate: true }
)

// Measured response state (Dev Order 19, editable Dev Order 20)
const referenceMeasuredResponse = ref<MeasuredResponse>(
  createEmptyMeasuredResponse({
    id: 'reference-measurement',
    label: 'Reference Measured Response',
    attachedTo: 'reference',
  })
)

const candidateMeasuredResponse = ref<MeasuredResponse>(
  createEmptyMeasuredResponse({
    id: 'candidate-measurement',
    label: 'Candidate Measured Response',
    attachedTo: 'candidate',
  })
)

function updateReferenceMeasurement(updated: MeasuredResponse) {
  referenceMeasuredResponse.value = updated
}

function updateCandidateMeasurement(updated: MeasuredResponse) {
  candidateMeasuredResponse.value = updated
}

// Helmholtz estimate handlers (Dev Order 27)
function attachReferenceHelmholtzEstimate(
  result: HelmholtzEstimateResult,
  volumeLiters: number,
  effectiveLengthMm: number
) {
  if (!referenceAcousticState.value) return
  referenceAcousticState.value = {
    ...referenceAcousticState.value,
    estimatedHelmholtzHz: result.estimatedHelmholtzHz,
    bodyVolumeLiters: volumeLiters,
    estimatedEffectiveLengthMm: effectiveLengthMm,
    speedOfSoundMps: result.inputUsed.speedOfSoundMps,
    estimateMethod: result.method,
    source: 'geometry_estimate',
    confidence: 'low',
    assumptions: [
      ...referenceAcousticState.value.assumptions.filter(
        (a) => !a.startsWith('First-order Helmholtz')
      ),
      'First-order Helmholtz estimate attached from geometry assumptions',
      ...result.assumptions,
    ],
    warnings: [
      ...(referenceAcousticState.value.warnings ?? []).filter(
        (w) => !w.includes('calibration')
      ),
      ...result.warnings,
    ],
  }
}

function attachCandidateHelmholtzEstimate(
  result: HelmholtzEstimateResult,
  volumeLiters: number,
  effectiveLengthMm: number
) {
  if (!candidateAcousticState.value) return
  candidateAcousticState.value = {
    ...candidateAcousticState.value,
    estimatedHelmholtzHz: result.estimatedHelmholtzHz,
    bodyVolumeLiters: volumeLiters,
    estimatedEffectiveLengthMm: effectiveLengthMm,
    speedOfSoundMps: result.inputUsed.speedOfSoundMps,
    estimateMethod: result.method,
    source: 'geometry_estimate',
    confidence: 'low',
    assumptions: [
      ...candidateAcousticState.value.assumptions.filter(
        (a) => !a.startsWith('First-order Helmholtz')
      ),
      'First-order Helmholtz estimate attached from geometry assumptions',
      ...result.assumptions,
    ],
    warnings: [
      ...(candidateAcousticState.value.warnings ?? []).filter(
        (w) => !w.includes('calibration')
      ),
      ...result.warnings,
    ],
  }
}

// Calibration readiness (Dev Order 22)
const calibrationReadiness = computed(() =>
  evaluateCalibrationReadiness({
    referenceGeometry: referenceGeometry.value,
    candidateGeometry: candidateGeometry.value,
    referenceMeasured: referenceMeasuredResponse.value,
    candidateMeasured: candidateMeasuredResponse.value,
  })
)

// Measurement pairing status (Dev Order 25)
const referencePairingStatus = computed(() =>
  evaluateMeasurementPairing({
    id: 'reference-pairing',
    label: 'Reference Pairing Status',
    acousticState: referenceAcousticState.value,
    measuredResponse: referenceMeasuredResponse.value,
  })
)

const candidatePairingStatus = computed(() =>
  evaluateMeasurementPairing({
    id: 'candidate-pairing',
    label: 'Candidate Pairing Status',
    acousticState: candidateAcousticState.value,
    measuredResponse: candidateMeasuredResponse.value,
  })
)

// Calibration residual preview (Dev Order 23)
const referenceResidualPreview = computed(() =>
  createCalibrationResidualPreview({
    id: 'reference-residuals',
    label: 'Reference Residual Preview',
    acousticState: referenceAcousticState.value,
    measuredResponse: referenceMeasuredResponse.value,
  })
)

const candidateResidualPreview = computed(() =>
  createCalibrationResidualPreview({
    id: 'candidate-residuals',
    label: 'Candidate Residual Preview',
    acousticState: candidateAcousticState.value,
    measuredResponse: candidateMeasuredResponse.value,
  })
)

// Estimate assumption summaries (Dev Order 28)
const referenceEstimateSummary = computed(() =>
  createEstimateAssumptionSummary({
    id: 'reference-estimate-summary',
    label: 'Reference Estimate Assumptions',
    acousticState: referenceAcousticState.value,
  })
)

const candidateEstimateSummary = computed(() =>
  createEstimateAssumptionSummary({
    id: 'candidate-estimate-summary',
    label: 'Candidate Estimate Assumptions',
    acousticState: candidateAcousticState.value,
  })
)

// Residual interpretation (Dev Order 30)
const referenceResidualInterpretation = computed(() =>
  interpretResidualPreview({
    id: 'reference-residual-interpretation',
    label: 'Reference Residual Interpretation',
    preview: referenceResidualPreview.value,
  })
)

const candidateResidualInterpretation = computed(() =>
  interpretResidualPreview({
    id: 'candidate-residual-interpretation',
    label: 'Candidate Residual Interpretation',
    preview: candidateResidualPreview.value,
  })
)

// Residual trend (Dev Order 31)
const referenceResidualTrend = computed(() =>
  summarizeResidualTrend({
    id: 'reference-residual-trend',
    label: 'Reference Residual Trend',
    preview: referenceResidualPreview.value,
  })
)

const candidateResidualTrend = computed(() =>
  summarizeResidualTrend({
    id: 'candidate-residual-trend',
    label: 'Candidate Residual Trend',
    preview: candidateResidualPreview.value,
  })
)

// Residual stability (Dev Order 32)
const referenceResidualStability = computed(() =>
  classifyResidualStability({
    id: 'reference-residual-stability',
    label: 'Reference Residual Stability',
    interpretation: referenceResidualInterpretation.value,
    trend: referenceResidualTrend.value,
  })
)

const candidateResidualStability = computed(() =>
  classifyResidualStability({
    id: 'candidate-residual-stability',
    label: 'Candidate Residual Stability',
    interpretation: candidateResidualInterpretation.value,
    trend: candidateResidualTrend.value,
  })
)

// Residual coherence summary (Dev Order 33)
const referenceResidualCoherence = computed(() =>
  summarizeResidualCoherence({
    id: 'reference-residual-coherence',
    label: 'Reference Residual Coherence',
    interpretation: referenceResidualInterpretation.value,
    trend: referenceResidualTrend.value,
    stability: referenceResidualStability.value,
  })
)

const candidateResidualCoherence = computed(() =>
  summarizeResidualCoherence({
    id: 'candidate-residual-coherence',
    label: 'Candidate Residual Coherence',
    interpretation: candidateResidualInterpretation.value,
    trend: candidateResidualTrend.value,
    stability: candidateResidualStability.value,
  })
)

// Diagnostic narrative summary (Dev Order 34)
const referenceDiagnosticNarrative = computed(() =>
  generateDiagnosticNarrative({
    id: 'reference-diagnostic-narrative',
    label: 'Reference Diagnostic Narrative',
    interpretation: referenceResidualInterpretation.value,
    trend: referenceResidualTrend.value,
    stability: referenceResidualStability.value,
    coherence: referenceResidualCoherence.value,
  })
)

const candidateDiagnosticNarrative = computed(() =>
  generateDiagnosticNarrative({
    id: 'candidate-diagnostic-narrative',
    label: 'Candidate Diagnostic Narrative',
    interpretation: candidateResidualInterpretation.value,
    trend: candidateResidualTrend.value,
    stability: candidateResidualStability.value,
    coherence: candidateResidualCoherence.value,
  })
)

// Diagnostic session snapshot (Dev Order 36, normalized Dev Order 37)
const diagnosticSnapshot = computed(() =>
  normalizeDiagnosticSnapshotForExport(
    createDiagnosticSnapshot({
      id: 'current-diagnostic-session',
      referenceNarrative: referenceDiagnosticNarrative.value,
      candidateNarrative: candidateDiagnosticNarrative.value,
      calibrationReadiness: calibrationReadiness.value,
      referenceCoherence: referenceResidualCoherence.value,
      candidateCoherence: candidateResidualCoherence.value,
    })
  )
)

// Export metadata (Dev Order 41)
const diagnosticSnapshotExportMetadata = computed(() =>
  createDiagnosticSnapshotExportMetadata()
)

// Measurement archive state (Dev Order 60, hardened Dev Order 61)
const currentMeasurementArchive = ref<MeasurementArchiveRecord | null>(null)
const archiveError = ref<string | null>(null)

const canArchiveMeasurement = computed(() => {
  const refHasData =
    referenceMeasuredResponse.value.measuredHelmholtzHz !== undefined ||
    referenceMeasuredResponse.value.measuredQ !== undefined ||
    referenceMeasuredResponse.value.dominantPeakHz !== undefined

  const candHasData =
    candidateMeasuredResponse.value.measuredHelmholtzHz !== undefined ||
    candidateMeasuredResponse.value.measuredQ !== undefined ||
    candidateMeasuredResponse.value.dominantPeakHz !== undefined

  return refHasData || candHasData
})

function archiveCurrentMeasurement() {
  archiveError.value = null

  const refGeoSummary = referenceGeometry.value
    ? createGeometrySummary(
        referenceGeometry.value.aperture_type,
        referenceGeometry.value.area_mm2,
        referenceGeometry.value.equivalent_diameter_mm ?? undefined,
        referenceGeometry.value.pa_ratio_mm_inv ?? undefined
      )
    : undefined

  const candGeoSummary = candidateGeometry.value
    ? createGeometrySummary(
        candidateGeometry.value.aperture_type,
        candidateGeometry.value.area_mm2,
        candidateGeometry.value.equivalent_diameter_mm ?? undefined,
        candidateGeometry.value.pa_ratio_mm_inv ?? undefined
      )
    : undefined

  const result = tryCreateArchiveFromDiagnosticContext({
    referenceLabel: 'Reference Aperture',
    candidateLabel: 'Candidate Aperture',
    referenceMeasured: referenceMeasuredResponse.value,
    candidateMeasured: candidateMeasuredResponse.value,
    referenceGeometry: refGeoSummary,
    candidateGeometry: candGeoSummary,
    referenceCoherence: referenceResidualCoherence.value,
    candidateCoherence: candidateResidualCoherence.value,
    referenceNarrative: referenceDiagnosticNarrative.value,
    candidateNarrative: candidateDiagnosticNarrative.value,
    linkedSnapshot: diagnosticSnapshot.value,
    tags: ['aperture-comparison', referenceType.value, 'dual_spiral'],
  })

  if (result.success && result.archive) {
    currentMeasurementArchive.value = result.archive
  } else {
    archiveError.value = result.error ?? 'Failed to create archive'
  }
}

function handleArchiveExported(archive: MeasurementArchiveRecord) {
  console.log('Archive exported:', archive.archiveId)
}

// Watch for reference parameter changes
watch(
  [referenceType, bodyStyle, bodyLengthMm, customDiameterMm, useCustomDiameter, ovalWidthMm, ovalHeightMm],
  () => {
    computeReference()
  },
  { deep: true }
)

onMounted(() => {
  fetchBodyStyles()
  computeReference()
  computeCandidate()
})
</script>

<template>
  <div :class="$style.panel">
    <!-- Header -->
    <div :class="$style.header">
      <SectionLabel text="Aperture Comparison" />
      <p :class="$style.subtitle">
        Compare conventional and spiral aperture geometries using normalized metrics.
      </p>
    </div>

    <!-- Side-by-side selectors -->
    <div :class="$style.selectorGrid">
      <!-- Reference Aperture (Left) -->
      <section :class="$style.selectorCard">
        <div :class="$style.selectorHeader">
          <SectionLabel text="Reference Aperture" />
          <GateBadge gate="green" label="Conventional" />
        </div>

        <div :class="$style.formGrid">
          <div :class="$style.field">
            <label :class="$style.label">Type</label>
            <select v-model="referenceType" :class="$style.select">
              <option v-for="opt in referenceTypeOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>

          <div :class="$style.field">
            <label :class="$style.label">Body Style</label>
            <select v-model="bodyStyle" :class="$style.select">
              <option v-for="opt in bodyStyles" :key="opt.value" :value="opt.value">
                {{ opt.label }} ({{ opt.diameter }}mm)
              </option>
            </select>
          </div>

          <div :class="$style.field">
            <label :class="$style.label">Body Length (mm)</label>
            <input
              v-model.number="bodyLengthMm"
              type="number"
              :class="$style.input"
              min="300"
              max="700"
              step="1"
            />
          </div>

          <template v-if="referenceType === 'round'">
            <div :class="$style.field">
              <label :class="$style.checkboxLabel">
                <input v-model="useCustomDiameter" type="checkbox" />
                Custom Diameter
              </label>
            </div>
            <div v-if="useCustomDiameter" :class="$style.field">
              <label :class="$style.label">Diameter (mm)</label>
              <input
                v-model.number="customDiameterMm"
                type="number"
                :class="$style.input"
                min="50"
                max="150"
                step="0.5"
              />
            </div>
          </template>

          <template v-if="referenceType === 'oval'">
            <div :class="$style.field">
              <label :class="$style.label">Width (mm)</label>
              <input v-model.number="ovalWidthMm" type="number" :class="$style.input" min="50" max="150" />
            </div>
            <div :class="$style.field">
              <label :class="$style.label">Height (mm)</label>
              <input v-model.number="ovalHeightMm" type="number" :class="$style.input" min="70" max="200" />
            </div>
          </template>
        </div>
      </section>

      <!-- Candidate Aperture (Right) -->
      <section :class="$style.selectorCard">
        <div :class="$style.selectorHeader">
          <SectionLabel text="Candidate Aperture" />
          <GateBadge gate="yellow" label="Dual Spiral" />
        </div>

        <div :class="$style.candidateInfo">
          <p>Carlos Jumbo dual-spiral (Williams 2019)</p>
          <ul>
            <li>Upper + lower logarithmic spiral apertures</li>
            <li>Combined geometry for acoustic comparison</li>
            <li>High P:A ratio design for acoustic efficiency</li>
          </ul>
        </div>

        <PrerequisiteNotice
          message="Spiral parameters use Carlos Jumbo defaults. Manual spiral editing is available in the dedicated Spiral tab."
        />
      </section>
    </div>

    <!-- Result Cards -->
    <div :class="$style.resultsGrid">
      <ApertureResultCard
        title="Reference Geometry"
        :geometry="referenceGeometry"
        :gate="referenceGate"
        :notes="referenceNotes"
        :loading="referenceLoading"
        :error="referenceError"
      />
      <ApertureResultCard
        title="Candidate Geometry"
        :geometry="candidateGeometry"
        gate="yellow"
        :notes="[]"
        :loading="candidateLoading"
        :error="candidateError"
      />
    </div>

    <!-- Comparison Table -->
    <section :class="$style.comparisonSection">
      <SectionLabel text="Comparison Delta" />
      <table :class="$style.deltaTable">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Reference</th>
            <th>Candidate</th>
            <th>Delta</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in deltaTable" :key="row.metric">
            <td>{{ row.metric }}</td>
            <td>{{ row.reference }}</td>
            <td>{{ row.candidate }}</td>
            <td :class="$style.deltaCell">{{ row.delta }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Acoustic State Display (Dev Order 15, extracted Dev Order 16, editable Dev Order 24) -->
    <section :class="$style.acousticStateSection">
      <SectionLabel text="Acoustic State" />
      <div :class="$style.acousticStateGrid">
        <AcousticStateCard
          v-if="referenceAcousticState"
          :state="referenceAcousticState"
          editable
          @update:state="updateReferenceAcousticState"
        />
        <AcousticStateCard
          v-if="candidateAcousticState"
          :state="candidateAcousticState"
          editable
          @update:state="updateCandidateAcousticState"
        />
      </div>
    </section>

    <!-- First-Order Helmholtz Estimate (Dev Order 27) -->
    <section :class="$style.helmholtzEstimateSection">
      <SectionLabel text="First-Order Helmholtz Estimate" />
      <div :class="$style.helmholtzEstimateGrid">
        <HelmholtzEstimateCard
          label="Reference Helmholtz Estimate"
          :aperture-geometry="referenceGeometry"
          :acoustic-state="referenceAcousticState"
          @attach-estimate="attachReferenceHelmholtzEstimate"
        />
        <HelmholtzEstimateCard
          label="Candidate Helmholtz Estimate"
          :aperture-geometry="candidateGeometry"
          :acoustic-state="candidateAcousticState"
          @attach-estimate="attachCandidateHelmholtzEstimate"
        />
      </div>
    </section>

    <!-- Estimate Assumption Summary (Dev Order 28) -->
    <section :class="$style.estimateSummarySection">
      <SectionLabel text="Estimate Assumption Summary" />
      <div :class="$style.estimateSummaryGrid">
        <EstimateAssumptionSummaryCard :summary="referenceEstimateSummary" />
        <EstimateAssumptionSummaryCard :summary="candidateEstimateSummary" />
      </div>
    </section>

    <!-- Measured Response Display (Dev Order 19, editable Dev Order 20) -->
    <section :class="$style.measuredResponseSection">
      <div :class="$style.measuredResponseHeader">
        <SectionLabel text="Measured Response" />
        <div :class="$style.archiveControls">
          <button
            :class="[$style.archiveButton, !canArchiveMeasurement && $style.archiveButtonDisabled]"
            :disabled="!canArchiveMeasurement"
            :title="canArchiveMeasurement ? 'Archive current measurements' : 'Enter measurement data to enable archiving'"
            @click="archiveCurrentMeasurement"
          >
            Archive Measurement
          </button>
          <span v-if="archiveError" :class="$style.archiveError">{{ archiveError }}</span>
        </div>
      </div>
      <div :class="$style.measuredResponseGrid">
        <MeasuredResponseCard
          :response="referenceMeasuredResponse"
          @update:response="updateReferenceMeasurement"
        />
        <MeasuredResponseCard
          :response="candidateMeasuredResponse"
          @update:response="updateCandidateMeasurement"
        />
      </div>
    </section>

    <!-- Measured Response Delta (Dev Order 21) -->
    <MeasuredResponseDeltaCard
      :reference="referenceMeasuredResponse"
      :candidate="candidateMeasuredResponse"
    />

    <!-- Measurement Pairing Status (Dev Order 25) -->
    <div :class="$style.pairingGrid">
      <MeasurementPairingStatusCard :status="referencePairingStatus" />
      <MeasurementPairingStatusCard :status="candidatePairingStatus" />
    </div>

    <!-- Calibration Readiness (Dev Order 22) -->
    <CalibrationReadinessCard :readiness="calibrationReadiness" />

    <!-- Calibration Residual Preview (Dev Order 23) -->
    <div :class="$style.residualGrid">
      <CalibrationResidualCard :preview="referenceResidualPreview" />
      <CalibrationResidualCard :preview="candidateResidualPreview" />
    </div>

    <!-- Residual Interpretation (Dev Order 30) -->
    <div :class="$style.interpretationGrid">
      <ResidualInterpretationCard :summary="referenceResidualInterpretation" />
      <ResidualInterpretationCard :summary="candidateResidualInterpretation" />
    </div>

    <!-- Residual Trend (Dev Order 31) -->
    <div :class="$style.trendGrid">
      <ResidualTrendCard :summary="referenceResidualTrend" />
      <ResidualTrendCard :summary="candidateResidualTrend" />
    </div>

    <!-- Residual Stability (Dev Order 32) -->
    <div :class="$style.stabilityGrid">
      <ResidualStabilityCard :summary="referenceResidualStability" />
      <ResidualStabilityCard :summary="candidateResidualStability" />
    </div>

    <!-- Residual Coherence (Dev Order 33) -->
    <div :class="$style.coherenceGrid">
      <ResidualCoherenceCard :summary="referenceResidualCoherence" />
      <ResidualCoherenceCard :summary="candidateResidualCoherence" />
    </div>

    <!-- Diagnostic Narrative (Dev Order 34) -->
    <div :class="$style.narrativeGrid">
      <DiagnosticNarrativeCard :summary="referenceDiagnosticNarrative" />
      <DiagnosticNarrativeCard :summary="candidateDiagnosticNarrative" />
    </div>

    <!-- Snapshot Exchange Section (Dev Order 42) -->
    <SnapshotExchangeSection
      :snapshot="diagnosticSnapshot"
      :export-metadata="diagnosticSnapshotExportMetadata"
    />

    <!-- Measurement Archive Exchange Section (Dev Order 60) -->
    <MeasurementArchiveExchangeSection
      :archive="currentMeasurementArchive"
      :linked-snapshot-id="diagnosticSnapshot.id"
      @exported="handleArchiveExported"
    />

    <!-- Future Acoustic Intelligence -->
    <section :class="$style.futurePlaceholder">
      <SectionLabel text="Future Acoustic Intelligence" />
      <div :class="$style.futureContent">
        <GateBadge gate="yellow" label="Planned" />
        <ul>
          <li :class="$style.implemented">Helmholtz frequency estimates (Dev Order 27)</li>
          <li>Effective neck length comparison</li>
          <li>Q / sustain estimates</li>
          <li>Two-cavity coupling analysis</li>
          <li>Tornavoz compensation modeling</li>
        </ul>
      </div>
    </section>
  </div>
</template>

<style module>
.panel {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.header {
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #9ca3af;
  font-size: 0.875rem;
  margin: 0.25rem 0 0 0;
}

.selectorGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.selectorCard {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.selectorHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #374151;
}

.formGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.label {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.checkboxLabel {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: #f9fafb;
  cursor: pointer;
}

.checkboxLabel input {
  accent-color: #6366f1;
}

.select,
.input {
  padding: 0.5rem 0.75rem;
  background: #111827;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  color: #f9fafb;
  font-size: 0.875rem;
}

.select:focus,
.input:focus {
  outline: none;
  border-color: #6366f1;
}

.candidateInfo {
  padding: 0.75rem;
  background: #111827;
  border-radius: 0.375rem;
  margin-bottom: 0.75rem;
}

.candidateInfo p {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 500;
  color: #f9fafb;
}

.candidateInfo ul {
  margin: 0;
  padding-left: 1.25rem;
}

.candidateInfo li {
  font-size: 0.75rem;
  color: #9ca3af;
  line-height: 1.5;
}

.resultsGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.comparisonSection {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.deltaTable {
  width: 100%;
  margin-top: 0.75rem;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.deltaTable th,
.deltaTable td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #374151;
}

.deltaTable th {
  font-size: 0.6875rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #111827;
}

.deltaTable td {
  color: #f9fafb;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.deltaCell {
  color: #60a5fa;
}

.futurePlaceholder {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.futureContent {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.futureContent ul {
  margin: 0;
  padding-left: 1.25rem;
}

.futureContent li {
  font-size: 0.8125rem;
  color: #6b7280;
  line-height: 1.75;
}

/* Acoustic State Display (Dev Order 15, extracted Dev Order 16) */
.acousticStateSection {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.acousticStateGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.75rem;
}

/* Measured Response Display (Dev Order 19) */
.measuredResponseSection {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.measuredResponseHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.archiveButton {
  padding: 0.375rem 0.75rem;
  background: #374151;
  color: #f9fafb;
  border: 1px solid #4b5563;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.archiveButton:hover {
  background: #4b5563;
}

.archiveButton:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.5);
}

.archiveButtonDisabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.archiveButtonDisabled:hover {
  background: #374151;
}

.archiveControls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.archiveError {
  font-size: 0.6875rem;
  color: #ef4444;
}

.measuredResponseGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* Measurement Pairing Status (Dev Order 25) */
.pairingGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* Calibration Residual Preview (Dev Order 23) */
.residualGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* First-Order Helmholtz Estimate (Dev Order 27) */
.helmholtzEstimateSection {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.helmholtzEstimateGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.75rem;
}

.implemented {
  color: #10b981;
  text-decoration: line-through;
}

/* Estimate Assumption Summary (Dev Order 28) */
.estimateSummarySection {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.estimateSummaryGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.75rem;
}

/* Residual Interpretation (Dev Order 30) */
.interpretationGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* Residual Trend (Dev Order 31) */
.trendGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* Residual Stability (Dev Order 32) */
.stabilityGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* Residual Coherence (Dev Order 33) */
.coherenceGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* Diagnostic Narrative (Dev Order 34) */
.narrativeGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
</style>
