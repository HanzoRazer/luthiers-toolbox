<script setup lang="ts">
/**
 * DiagnosticSnapshotCard — Diagnostic session snapshot summary
 *
 * Dev Order 36: Displays structured observational diagnostic snapshot.
 * Dev Order 37: Export preparation — schema versioning, export readiness display.
 * Dev Order 38: JSON export — client-side snapshot download.
 * Does NOT persist to backend, calibrate, or predict.
 */
import { computed } from 'vue'
import { GateBadge } from '@/components/shared/workflow'
import type { DiagnosticSnapshot } from '@/types/diagnosticSnapshot'
import {
  countAvailableSections,
  getSnapshotGateColor,
} from '@/utils/acoustics/diagnosticSnapshot'
import {
  canExportDiagnosticSnapshot,
  downloadDiagnosticSnapshotJson,
} from '@/utils/acoustics/diagnosticSnapshotExport'

const props = defineProps<{
  snapshot: DiagnosticSnapshot
}>()

const availableCount = computed(() => countAvailableSections(props.snapshot))
const totalCount = computed(() => props.snapshot.sections.length)

const isSparseSnapshot = computed(() => {
  if (totalCount.value === 0) return true
  return availableCount.value < totalCount.value / 2
})

const formattedTimestamp = computed(() => {
  const date = new Date(props.snapshot.createdAtIso)
  return date.toLocaleString()
})

const canExport = computed(() => canExportDiagnosticSnapshot(props.snapshot))

function handleDownload() {
  if (!canExport.value) return
  try {
    downloadDiagnosticSnapshotJson(props.snapshot)
  } catch (error) {
    console.error('Failed to download snapshot:', error)
  }
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">Diagnostic Session Snapshot</span>
      <GateBadge
        :gate="getSnapshotGateColor(snapshot.readinessLevel)"
        :label="snapshot.readinessLevel ?? 'Unknown'"
      />
    </div>

    <!-- Schema Metadata -->
    <div :class="$style.schemaInfo">
      <div :class="$style.schemaItem">
        <span :class="$style.schemaLabel">Schema</span>
        <span :class="$style.schemaValue">{{ snapshot.schemaVersion }}</span>
      </div>
      <div :class="$style.schemaItem">
        <span :class="$style.schemaLabel">Kind</span>
        <span :class="$style.schemaValue">{{ snapshot.kind }}</span>
      </div>
      <div :class="$style.schemaItem">
        <span :class="$style.schemaLabel">Export Ready</span>
        <span :class="[$style.schemaValue, snapshot.exportReady ? $style.exportReady : $style.exportNotReady]">
          {{ snapshot.exportReady ? 'Yes' : 'No' }}
        </span>
      </div>
    </div>

    <!-- Metadata -->
    <div :class="$style.metadata">
      <div :class="$style.metaItem">
        <span :class="$style.metaLabel">Timestamp</span>
        <span :class="$style.metaValue">{{ formattedTimestamp }}</span>
      </div>
      <div :class="$style.metaItem">
        <span :class="$style.metaLabel">Sections</span>
        <span :class="$style.metaValue">{{ availableCount }} / {{ totalCount }} available</span>
      </div>
    </div>

    <!-- Narrative Summary -->
    <div v-if="snapshot.narrativeSummary" :class="$style.narrativeSummary">
      <span :class="$style.summaryLabel">Narrative Summary</span>
      <span :class="$style.summaryValue">{{ snapshot.narrativeSummary }}</span>
    </div>

    <!-- Sparse State Message -->
    <div v-if="isSparseSnapshot" :class="$style.sparseNotice">
      <span :class="$style.sparseTitle">Minimal observational snapshot available.</span>
      <span :class="$style.sparseHint">
        Additional measurements and estimates may expand diagnostic coverage.
      </span>
    </div>

    <!-- Sections -->
    <div :class="$style.sections">
      <div
        v-for="section in snapshot.sections"
        :key="section.label"
        :class="[$style.section, !section.available && $style.sectionUnavailable]"
      >
        <div :class="$style.sectionHeader">
          <span :class="$style.sectionLabel">{{ section.label }}</span>
          <span :class="[$style.sectionStatus, section.available ? $style.available : $style.unavailable]">
            {{ section.available ? 'Available' : 'Pending' }}
          </span>
        </div>
        <p :class="$style.sectionSummary">{{ section.summary }}</p>
      </div>
    </div>

    <!-- Provenance Reminder -->
    <div :class="$style.provenance">
      {{ snapshot.provenanceReminder }}
    </div>

    <!-- Export Action -->
    <div :class="$style.exportAction">
      <button
        :class="[$style.exportButton, !canExport && $style.exportButtonDisabled]"
        :disabled="!canExport"
        @click="handleDownload"
      >
        Download JSON Snapshot
      </button>
      <span v-if="!canExport" :class="$style.exportDisabledText">
        Snapshot is not export-ready.
      </span>
    </div>

    <!-- Export Notice -->
    <div :class="$style.exportNotice">
      JSON export preserves observational diagnostic state only. It does not export calibrated
      predictions or recommendations.
    </div>

    <!-- Observational Notice -->
    <div :class="$style.notice">
      Diagnostic snapshots preserve observational diagnostic state only. They do not represent
      calibrated prediction or validated acoustic performance.
    </div>
  </div>
</template>

<style module>
.card {
  background: #111827;
  border: 1px solid #374151;
  border-left: 3px solid #6366f1;
  border-radius: 0.375rem;
  padding: 1rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #374151;
}

.label {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f9fafb;
}

.schemaInfo {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(55, 65, 81, 0.5);
  border-radius: 0.25rem;
}

.schemaItem {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.125rem;
}

.schemaLabel {
  font-size: 0.5625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.schemaValue {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #d1d5db;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.exportReady {
  color: #10b981;
}

.exportNotReady {
  color: #ef4444;
}

.metadata {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: #1f2937;
  border-radius: 0.25rem;
}

.metaItem {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.metaLabel {
  font-size: 0.625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metaValue {
  font-size: 0.75rem;
  font-weight: 500;
  color: #f9fafb;
}

.narrativeSummary {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 0.25rem;
  border-left: 3px solid #6366f1;
}

.summaryLabel {
  font-size: 0.625rem;
  color: #a5b4fc;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summaryValue {
  font-size: 0.8125rem;
  color: #e5e7eb;
}

.sparseNotice {
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 0.25rem;
  border-left: 3px solid #6366f1;
}

.sparseTitle {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  color: #a5b4fc;
  margin-bottom: 0.375rem;
}

.sparseHint {
  display: block;
  font-size: 0.6875rem;
  color: #818cf8;
}

.sections {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.section {
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
}

.sectionUnavailable {
  opacity: 0.6;
}

.sectionHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.sectionLabel {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #d1d5db;
}

.sectionStatus {
  font-size: 0.5625rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.125rem 0.25rem;
  border-radius: 0.125rem;
}

.available {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.unavailable {
  color: #6b7280;
  background: rgba(107, 114, 128, 0.1);
}

.sectionSummary {
  margin: 0;
  font-size: 0.625rem;
  color: #9ca3af;
  line-height: 1.4;
}

.provenance {
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #a5b4fc;
  font-style: italic;
}

.exportAction {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: #1f2937;
  border-radius: 0.25rem;
}

.exportButton {
  padding: 0.375rem 0.75rem;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.exportButton:hover:not(:disabled) {
  background: #4338ca;
}

.exportButton:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.5);
}

.exportButtonDisabled {
  background: #374151;
  color: #6b7280;
  cursor: not-allowed;
}

.exportDisabledText {
  font-size: 0.6875rem;
  color: #9ca3af;
  font-style: italic;
}

.exportNotice {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(16, 185, 129, 0.08);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #10b981;
}

.notice {
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.08);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #fbbf24;
}
</style>
