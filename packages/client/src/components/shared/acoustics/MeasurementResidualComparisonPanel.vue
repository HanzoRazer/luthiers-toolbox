<script setup lang="ts">
/**
 * MeasurementResidualComparisonPanel — Pairwise archive comparison
 *
 * Dev Order 63: Compares two measurement archives and displays residual analysis
 * using existing residual cards. Observational only — no prescriptions or rankings.
 * Dev Order 66: Added topology variant comparison display.
 * Dev Order 67: QA hardening for variant edge cases.
 *
 * Composes:
 *   - Archive selectors (A and B)
 *   - Topology variant comparison indicator
 *   - Residual summary
 *   - ResidualCoherenceCard (existing)
 *   - Observational narrative
 *
 * Ephemeral comparisons — archives are durable, comparisons are transient.
 * Variant comparison is observational only — no scoring, ranking, or recommendations.
 */
import { ref, computed, watch } from 'vue'
import { GateBadge, SectionLabel } from '@/components/shared/workflow'
import ResidualCoherenceCard from './ResidualCoherenceCard.vue'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import type { TopologyVariant } from '@/types/acoustics/topologyVariant'
import type { ResidualCoherenceSummary, ResidualCoherenceLevel } from '@/types/residualCoherence'
import {
  compareArchives,
  interpretResidualMagnitude,
  generateComparisonNarrative,
  formatArchiveTimestamp,
  type ArchiveComparisonResult,
} from '@/utils/acoustics/measurementArchive'
import { checkSharedTopologyVariant } from '@/utils/acoustics/topologyVariant'

const props = defineProps<{
  archives: MeasurementArchiveRecord[]
  topologyVariants?: TopologyVariant[]
}>()

const selectedArchiveIdA = ref<string | null>(null)
const selectedArchiveIdB = ref<string | null>(null)

const archiveA = computed(() =>
  props.archives.find((a) => a.archiveId === selectedArchiveIdA.value) ?? null
)

const archiveB = computed(() =>
  props.archives.find((a) => a.archiveId === selectedArchiveIdB.value) ?? null
)

const canCompare = computed(() => archiveA.value !== null && archiveB.value !== null)

// Dev Order 66: Topology variant comparison
const variantComparison = computed(() => {
  if (!archiveA.value || !archiveB.value) return null

  const refsA = archiveA.value.topologyVariantReferences
  const refsB = archiveB.value.topologyVariantReferences

  const { shared, sharedIds } = checkSharedTopologyVariant(refsA, refsB)

  return {
    shared,
    sharedIds,
    variantIdsA: refsA ?? [],
    variantIdsB: refsB ?? [],
  }
})

function getVariantTitle(variantId: string): string {
  const variant = props.topologyVariants?.find((v) => v.variantId === variantId)
  return variant?.title ?? variantId
}

const comparisonResult = computed<ArchiveComparisonResult | null>(() => {
  if (!archiveA.value || !archiveB.value) return null
  return compareArchives(archiveA.value, archiveB.value)
})

const narrative = computed(() => {
  if (!comparisonResult.value) return null
  return generateComparisonNarrative(comparisonResult.value)
})

// Build coherence summary from comparison result
const coherenceSummary = computed<ResidualCoherenceSummary | null>(() => {
  if (!comparisonResult.value) return null

  const result = comparisonResult.value

  // Determine coherence level based on comparison status and residual magnitudes
  let level: ResidualCoherenceLevel
  let message: string

  if (result.status === 'insufficient') {
    level = 'insufficient'
    message = 'Insufficient comparable data for coherence assessment.'
  } else {
    const magnitudes = result.residuals.map((r) => interpretResidualMagnitude(r.percentDifference))
    const largeCount = magnitudes.filter((m) => m === 'large').length
    const moderateCount = magnitudes.filter((m) => m === 'moderate').length

    if (largeCount > 0) {
      level = 'mixed'
      message = `${largeCount} large divergence${largeCount > 1 ? 's' : ''} detected. Experimental variance may be significant.`
    } else if (moderateCount > 0) {
      level = 'sparse'
      message = `${moderateCount} moderate divergence${moderateCount > 1 ? 's' : ''}. Consider additional measurements for confirmation.`
    } else {
      level = 'coherent'
      message = 'Residual divergence is small across compared properties.'
    }
  }

  // Determine trend direction from primary residual
  const helmholtzResidual = result.residuals.find((r) => r.property === 'measuredHelmholtzHz')
  let trendDirection: string | undefined
  if (helmholtzResidual) {
    if (helmholtzResidual.difference > 0) {
      trendDirection = 'Archive B higher'
    } else if (helmholtzResidual.difference < 0) {
      trendDirection = 'Archive B lower'
    } else {
      trendDirection = 'No divergence'
    }
  }

  return {
    id: `comparison-${result.archiveIdA}-${result.archiveIdB}`,
    label: 'Comparison Coherence',
    level,
    interpretationLevel: result.status,
    trendDirection,
    stabilityLevel: result.residuals.length >= 2 ? 'comparable' : 'limited',
    message,
    caution: 'Comparison is observational only. It does not indicate superiority, calibration, or recommendation.',
    notes: result.notes,
  }
})

function getArchiveLabel(archive: MeasurementArchiveRecord): string {
  return archive.context.referenceLabel ?? archive.context.candidateLabel ?? archive.archiveId
}

function getStatusGate(status: string): 'green' | 'yellow' | 'red' {
  switch (status) {
    case 'comparable':
      return 'green'
    case 'partial':
      return 'yellow'
    default:
      return 'red'
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case 'comparable':
      return 'Comparable'
    case 'partial':
      return 'Partial'
    default:
      return 'Insufficient'
  }
}

function getMagnitudeClass(percentDifference: number | null): string {
  const magnitude = interpretResidualMagnitude(percentDifference)
  switch (magnitude) {
    case 'large':
      return 'magnitudeLarge'
    case 'moderate':
      return 'magnitudeModerate'
    case 'small':
      return 'magnitudeSmall'
    default:
      return ''
  }
}

// Reset selection B if it matches A
watch(selectedArchiveIdA, (newA) => {
  if (newA && newA === selectedArchiveIdB.value) {
    selectedArchiveIdB.value = null
  }
})
</script>

<template>
  <div :class="$style.panel">
    <div :class="$style.header">
      <SectionLabel text="Residual Comparison" />
      <GateBadge
        v-if="comparisonResult"
        :gate="getStatusGate(comparisonResult.status)"
        :label="getStatusLabel(comparisonResult.status)"
      />
    </div>

    <p :class="$style.description">
      Select two archives to compare acoustic residuals. Comparison is observational —
      it describes divergence without prescribing action or ranking outcomes.
    </p>

    <!-- Archive Selectors -->
    <div :class="$style.selectors">
      <div :class="$style.selector">
        <label :class="$style.selectorLabel">Archive A</label>
        <select
          v-model="selectedArchiveIdA"
          :class="$style.select"
          :disabled="archives.length === 0"
        >
          <option :value="null">Select archive...</option>
          <option
            v-for="archive in archives"
            :key="archive.archiveId"
            :value="archive.archiveId"
            :disabled="archive.archiveId === selectedArchiveIdB"
          >
            {{ getArchiveLabel(archive) }} ({{ formatArchiveTimestamp(archive.metadata.createdAtIso) }})
          </option>
        </select>
      </div>

      <div :class="$style.selector">
        <label :class="$style.selectorLabel">Archive B</label>
        <select
          v-model="selectedArchiveIdB"
          :class="$style.select"
          :disabled="archives.length === 0"
        >
          <option :value="null">Select archive...</option>
          <option
            v-for="archive in archives"
            :key="archive.archiveId"
            :value="archive.archiveId"
            :disabled="archive.archiveId === selectedArchiveIdA"
          >
            {{ getArchiveLabel(archive) }} ({{ formatArchiveTimestamp(archive.metadata.createdAtIso) }})
          </option>
        </select>
      </div>
    </div>

    <!-- Dev Order 66: Topology Variant Comparison -->
    <div v-if="variantComparison && canCompare" :class="$style.variantComparison">
      <template v-if="variantComparison.shared">
        <span :class="$style.variantShared">
          Shared topology variant: {{ variantComparison.sharedIds.map(getVariantTitle).join(', ') }}
        </span>
      </template>
      <template v-else-if="variantComparison.variantIdsA.length > 0 || variantComparison.variantIdsB.length > 0">
        <span :class="$style.variantDifferent">Different topology variants observed</span>
        <div :class="$style.variantDetails">
          <div v-if="variantComparison.variantIdsA.length > 0" :class="$style.variantRow">
            <span :class="$style.variantLabel">Archive A:</span>
            <span :class="$style.variantValue">{{ variantComparison.variantIdsA.map(getVariantTitle).join(', ') }}</span>
          </div>
          <div v-else :class="$style.variantRow">
            <span :class="$style.variantLabel">Archive A:</span>
            <span :class="$style.variantNone">No variant referenced</span>
          </div>
          <div v-if="variantComparison.variantIdsB.length > 0" :class="$style.variantRow">
            <span :class="$style.variantLabel">Archive B:</span>
            <span :class="$style.variantValue">{{ variantComparison.variantIdsB.map(getVariantTitle).join(', ') }}</span>
          </div>
          <div v-else :class="$style.variantRow">
            <span :class="$style.variantLabel">Archive B:</span>
            <span :class="$style.variantNone">No variant referenced</span>
          </div>
        </div>
      </template>
      <template v-else>
        <span :class="$style.variantNone">Neither archive references a topology variant</span>
      </template>
    </div>

    <!-- Empty State -->
    <div v-if="archives.length === 0" :class="$style.emptyState">
      <p :class="$style.emptyText">No archives available for comparison.</p>
      <p :class="$style.emptyHint">Import or create measurement archives to enable residual comparison.</p>
    </div>

    <!-- Selection Required -->
    <div v-else-if="!canCompare" :class="$style.selectionRequired">
      <p>Select two archives to compare residuals.</p>
    </div>

    <!-- Comparison Results -->
    <template v-else-if="comparisonResult">
      <!-- Residual Summary Table -->
      <div :class="$style.residualTable">
        <div :class="$style.tableHeader">
          <span :class="$style.tableHeaderCell">Property</span>
          <span :class="$style.tableHeaderCell">Archive A</span>
          <span :class="$style.tableHeaderCell">Archive B</span>
          <span :class="$style.tableHeaderCell">Divergence</span>
        </div>

        <div
          v-for="residual in comparisonResult.residuals"
          :key="residual.property"
          :class="$style.tableRow"
        >
          <span :class="$style.tableCell">{{ residual.label }}</span>
          <span :class="$style.tableCell">
            {{ residual.valueA.toFixed(1) }} {{ residual.unit }}
          </span>
          <span :class="$style.tableCell">
            {{ residual.valueB.toFixed(1) }} {{ residual.unit }}
          </span>
          <span :class="[$style.tableCell, $style[getMagnitudeClass(residual.percentDifference)]]">
            {{ residual.difference >= 0 ? '+' : '' }}{{ residual.difference.toFixed(1) }} {{ residual.unit }}
            <template v-if="residual.percentDifference !== null">
              ({{ residual.percentDifference >= 0 ? '+' : '' }}{{ residual.percentDifference.toFixed(1) }}%)
            </template>
          </span>
        </div>

        <div v-if="comparisonResult.residuals.length === 0" :class="$style.noResiduals">
          No comparable properties found.
        </div>
      </div>

      <!-- Warnings -->
      <div v-if="comparisonResult.warnings.length > 0" :class="$style.warnings">
        <span :class="$style.warningsLabel">Asymmetries</span>
        <ul :class="$style.warningsList">
          <li v-for="(warning, idx) in comparisonResult.warnings" :key="idx">{{ warning }}</li>
        </ul>
      </div>

      <!-- Coherence Card -->
      <ResidualCoherenceCard v-if="coherenceSummary" :summary="coherenceSummary" />

      <!-- Observational Narrative -->
      <div :class="$style.narrative">
        <span :class="$style.narrativeLabel">Observational Summary</span>
        <p :class="$style.narrativeText">{{ narrative }}</p>
      </div>
    </template>

    <!-- Footer Notice -->
    <div :class="$style.notice">
      Residual comparison is ephemeral and observational. Archives are durable;
      comparisons are not persisted or archived.
    </div>
  </div>
</template>

<style module>
.panel {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  padding: 1rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #30363d;
}

.description {
  margin: 0 0 0.75rem 0;
  font-size: 0.75rem;
  color: #8b949e;
  line-height: 1.5;
}

.selectors {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.selector {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.selectorLabel {
  font-size: 0.625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.select {
  padding: 0.5rem;
  background: #1f2937;
  color: #d1d5db;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  cursor: pointer;
}

.select:focus {
  outline: none;
  border-color: #6366f1;
}

.select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.emptyState,
.selectionRequired {
  padding: 1rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  text-align: center;
  margin-bottom: 0.75rem;
}

.emptyText {
  margin: 0 0 0.25rem 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.emptyHint {
  margin: 0;
  font-size: 0.6875rem;
  color: #6b7280;
  font-style: italic;
}

.selectionRequired p {
  margin: 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.residualTable {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  margin-bottom: 0.75rem;
  overflow: hidden;
}

.tableHeader {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1.5fr;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #111827;
  border-bottom: 1px solid #374151;
}

.tableHeaderCell {
  font-size: 0.625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tableRow {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1.5fr;
  gap: 0.5rem;
  padding: 0.5rem;
  border-bottom: 1px solid #30363d;
}

.tableRow:last-child {
  border-bottom: none;
}

.tableCell {
  font-size: 0.75rem;
  color: #d1d5db;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.magnitudeSmall {
  color: #10b981;
}

.magnitudeModerate {
  color: #fbbf24;
}

.magnitudeLarge {
  color: #ef4444;
}

.noResiduals {
  padding: 1rem;
  text-align: center;
  font-size: 0.75rem;
  color: #6b7280;
}

.warnings {
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: rgba(251, 191, 36, 0.08);
  border-radius: 0.25rem;
}

.warningsLabel {
  display: block;
  font-size: 0.5625rem;
  color: #fbbf24;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.warningsList {
  margin: 0;
  padding-left: 1rem;
  font-size: 0.6875rem;
  color: #fbbf24;
}

.warningsList li {
  margin-bottom: 0.125rem;
}

.narrative {
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 0.25rem;
}

.narrativeLabel {
  display: block;
  font-size: 0.5625rem;
  color: #a5b4fc;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.narrativeText {
  margin: 0;
  font-size: 0.75rem;
  color: #d1d5db;
  line-height: 1.5;
}

.notice {
  margin-top: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  font-size: 0.625rem;
  color: #6b7280;
  text-align: center;
}

/* Dev Order 66: Topology variant comparison */
.variantComparison {
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 0.25rem;
}

.variantShared {
  font-size: 0.75rem;
  color: #10b981;
}

.variantDifferent {
  display: block;
  font-size: 0.75rem;
  color: #fbbf24;
  margin-bottom: 0.5rem;
}

.variantDetails {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.variantRow {
  display: flex;
  gap: 0.5rem;
  font-size: 0.6875rem;
}

.variantLabel {
  color: #6b7280;
  min-width: 4.5rem;
}

.variantValue {
  color: #d1d5db;
}

.variantNone {
  color: #6b7280;
  font-style: italic;
}
</style>
