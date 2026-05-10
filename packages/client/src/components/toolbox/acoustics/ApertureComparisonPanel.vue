<script setup lang="ts">
/**
 * ApertureComparisonPanel — Compare aperture geometries side-by-side
 *
 * Dev Order 12: Comparison panel for normalized aperture geometry comparison.
 *
 * Reference: round or oval (standard aperture API)
 * Candidate: dual_spiral (combined Carlos Jumbo defaults)
 *
 * Uses normalized ApertureGeometry contract for cross-type comparison.
 */
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { GateBadge, SectionLabel, PrerequisiteNotice } from '@/components/shared/workflow'
import { ApertureResultCard, type ApertureGeometry } from '@/components/shared/aperture'
import { AcousticStateCard, MeasuredResponseCard } from '@/components/shared/acoustics'
import { createGeometryAcousticState, createEmptyMeasuredResponse } from '@/utils/acoustics'
import type { AcousticState } from '@/types/acoustics'
import type { MeasuredResponse } from '@/types/measurements'

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
const referenceAcousticState = computed<AcousticState | null>(() =>
  referenceGeometry.value
    ? createGeometryAcousticState({
        id: 'reference',
        label: 'Reference Aperture',
        apertureGeometry: referenceGeometry.value,
      })
    : null
)

const candidateAcousticState = computed<AcousticState | null>(() =>
  candidateGeometry.value
    ? createGeometryAcousticState({
        id: 'candidate',
        label: 'Candidate Aperture',
        apertureGeometry: candidateGeometry.value,
      })
    : null
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

    <!-- Acoustic State Display (Dev Order 15, extracted Dev Order 16) -->
    <section :class="$style.acousticStateSection">
      <SectionLabel text="Acoustic State" />
      <div :class="$style.acousticStateGrid">
        <AcousticStateCard v-if="referenceAcousticState" :state="referenceAcousticState" />
        <AcousticStateCard v-if="candidateAcousticState" :state="candidateAcousticState" />
      </div>
    </section>

    <!-- Measured Response Display (Dev Order 19, editable Dev Order 20) -->
    <section :class="$style.measuredResponseSection">
      <SectionLabel text="Measured Response" />
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

    <!-- Future Acoustic Intelligence -->
    <section :class="$style.futurePlaceholder">
      <SectionLabel text="Future Acoustic Intelligence" />
      <div :class="$style.futureContent">
        <GateBadge gate="yellow" label="Planned" />
        <ul>
          <li>Helmholtz frequency estimates</li>
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

.measuredResponseGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.75rem;
}
</style>
