<script setup lang="ts">
/**
 * ExperimentalCorrelationPanel — Computed observational correlations
 *
 * Dev Order 68: Displays correlations between topology variants
 * and residual behavior across archives.
 *
 * OBSERVATIONAL ONLY:
 * - Correlation does NOT imply causation
 * - No optimization, recommendation, or validation semantics
 * - Minimum 3 archives per variant for correlation detection
 *
 * Allowed language: correlates with, observed alongside, appears with
 * Forbidden language: causes, improves, optimizes, recommends, proves
 */
import { computed } from 'vue'
import { GateBadge, SectionLabel } from '@/components/shared/workflow'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import type { TopologyVariant } from '@/types/acoustics/topologyVariant'
import type { ExperimentalCorrelation } from '@/types/acoustics/experimentalCorrelation'
import {
  computeCorrelations,
  getAllVariantCorrelationSummaries,
  hasSufficientDataForCorrelations,
  getMinSampleSize,
  formatConfidenceBand,
  getConfidenceBandGate,
} from '@/utils/acoustics/experimentalCorrelation'

const props = defineProps<{
  archives: MeasurementArchiveRecord[]
  topologyVariants: TopologyVariant[]
}>()

const hasSufficientData = computed(() =>
  hasSufficientDataForCorrelations(props.archives)
)

const correlationResult = computed(() =>
  computeCorrelations(props.archives, props.topologyVariants)
)

const variantSummaries = computed(() =>
  getAllVariantCorrelationSummaries(
    correlationResult.value.correlations,
    props.topologyVariants
  )
)

const minSampleSize = getMinSampleSize()

function getVariantTitle(variantId: string): string {
  const variant = props.topologyVariants.find(v => v.variantId === variantId)
  return variant?.title ?? variantId
}

function getCorrelationsForVariant(variantId: string): ExperimentalCorrelation[] {
  return correlationResult.value.correlations.filter(
    c => c.sourceVariantId === variantId
  )
}
</script>

<template>
  <div :class="$style.panel">
    <div :class="$style.header">
      <SectionLabel text="Experimental Correlations" />
      <GateBadge
        :gate="hasSufficientData ? 'green' : 'yellow'"
        :label="hasSufficientData ? `${correlationResult.correlations.length} observed` : 'Insufficient data'"
      />
    </div>

    <p :class="$style.description">
      Observational correlations between topology variants and residual behavior.
      Correlation does not imply causation — patterns are descriptive only.
    </p>

    <!-- Insufficient Data State -->
    <div v-if="!hasSufficientData" :class="$style.insufficientState">
      <p :class="$style.insufficientText">
        Insufficient evidence for correlation detection.
      </p>
      <p :class="$style.insufficientHint">
        At least {{ minSampleSize }} archives referencing the same topology variant
        are required to detect patterns.
      </p>
    </div>

    <!-- Correlation Results -->
    <template v-else>
      <!-- Variant Summaries -->
      <div v-if="variantSummaries.length > 0" :class="$style.summaries">
        <div
          v-for="summary in variantSummaries"
          :key="summary.variantId"
          :class="$style.summaryCard"
        >
          <div :class="$style.summaryHeader">
            <span :class="$style.summaryTitle">{{ summary.variantTitle }}</span>
            <GateBadge
              :gate="getConfidenceBandGate(summary.confidenceBand)"
              :label="formatConfidenceBand(summary.confidenceBand)"
            />
          </div>

          <div :class="$style.summaryMeta">
            <span>{{ summary.correlationCount }} correlation{{ summary.correlationCount !== 1 ? 's' : '' }}</span>
            <span>{{ summary.archiveCount }} archive{{ summary.archiveCount !== 1 ? 's' : '' }}</span>
          </div>

          <div v-if="summary.dominantPattern" :class="$style.dominantPattern">
            Dominant pattern: {{ summary.dominantPattern }}
          </div>

          <!-- Individual Correlations -->
          <div :class="$style.correlationList">
            <div
              v-for="correlation in getCorrelationsForVariant(summary.variantId)"
              :key="correlation.correlationId"
              :class="$style.correlationItem"
            >
              <span :class="$style.correlationNarrative">
                {{ correlation.narrative }}
              </span>
              <span :class="$style.correlationMeta">
                {{ correlation.observedField }} · {{ correlation.sampleCount }} samples
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- No Correlations Found -->
      <div v-else :class="$style.noCorrelations">
        <p>No significant correlations detected in the current dataset.</p>
        <p :class="$style.noCorrelationsHint">
          Correlations require consistent patterns across multiple archives
          referencing the same topology variant.
        </p>
      </div>

      <!-- Insufficient Variants -->
      <div
        v-if="correlationResult.insufficientVariants.length > 0"
        :class="$style.insufficientVariants"
      >
        <span :class="$style.insufficientLabel">Insufficient samples</span>
        <div :class="$style.insufficientList">
          <span
            v-for="variantId in correlationResult.insufficientVariants"
            :key="variantId"
            :class="$style.insufficientVariant"
          >
            {{ getVariantTitle(variantId) }}
          </span>
        </div>
      </div>
    </template>

    <!-- Footer Notice (Dev Order 69 boundary text) -->
    <div :class="$style.notice">
      Correlations are observational patterns only and do not establish causation or design superiority.
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

.insufficientState {
  padding: 1rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  text-align: center;
  margin-bottom: 0.75rem;
}

.insufficientText {
  margin: 0 0 0.25rem 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.insufficientHint {
  margin: 0;
  font-size: 0.6875rem;
  color: #6b7280;
  font-style: italic;
}

.summaries {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.summaryCard {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  padding: 0.75rem;
}

.summaryHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.summaryTitle {
  font-size: 0.875rem;
  font-weight: 500;
  color: #f9fafb;
}

.summaryMeta {
  display: flex;
  gap: 1rem;
  font-size: 0.6875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.dominantPattern {
  font-size: 0.75rem;
  color: #818cf8;
  margin-bottom: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 0.25rem;
  display: inline-block;
}

.correlationList {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #374151;
}

.correlationItem {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding: 0.375rem;
  background: #111827;
  border-radius: 0.25rem;
}

.correlationNarrative {
  font-size: 0.75rem;
  color: #d1d5db;
  line-height: 1.4;
}

.correlationMeta {
  font-size: 0.625rem;
  color: #6b7280;
}

.noCorrelations {
  padding: 1rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  text-align: center;
  margin-bottom: 0.75rem;
}

.noCorrelations p {
  margin: 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.noCorrelationsHint {
  margin-top: 0.25rem !important;
  font-size: 0.6875rem !important;
  color: #6b7280 !important;
  font-style: italic;
}

.insufficientVariants {
  padding: 0.5rem;
  background: rgba(251, 191, 36, 0.08);
  border-radius: 0.25rem;
  margin-bottom: 0.75rem;
}

.insufficientLabel {
  display: block;
  font-size: 0.5625rem;
  color: #fbbf24;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.insufficientList {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.insufficientVariant {
  padding: 0.125rem 0.375rem;
  background: rgba(251, 191, 36, 0.15);
  border-radius: 0.25rem;
  font-size: 0.625rem;
  color: #fbbf24;
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
</style>
