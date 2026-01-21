<template>
  <section class="diff-viewer">
    <header class="diff-header">
      <div>
        <h3>Diff Summary</h3>
        <p class="hint">
          Baseline: {{ diff?.baseline_name || '—' }}
        </p>
      </div>
      <button
        class="ghost"
        :disabled="!canExport || exporting"
        @click="exportOverlay"
      >
        {{ exporting ? 'Exporting…' : 'Export JSON Overlay' }}
      </button>
    </header>

    <div
      v-if="diff"
      class="summary-grid"
    >
      <div class="summary-card">
        <span class="label">Baseline Segments</span>
        <strong>{{ diff.summary.segments_baseline }}</strong>
      </div>
      <div class="summary-card">
        <span class="label">Current Segments</span>
        <strong>{{ diff.summary.segments_current }}</strong>
      </div>
      <div class="summary-card">
        <span class="label">Added</span>
        <strong class="added">+{{ diff.summary.added }}</strong>
      </div>
      <div class="summary-card">
        <span class="label">Removed</span>
        <strong class="removed">-{{ diff.summary.removed }}</strong>
      </div>
      <div class="summary-card">
        <span class="label">Matches</span>
        <strong>{{ diff.summary.unchanged }}</strong>
      </div>
      <div class="summary-card">
        <span class="label">Overlap</span>
        <strong>{{ (diff.summary.overlap_ratio * 100).toFixed(1) }}%</strong>
      </div>
    </div>

    <div
      v-if="diff && diff.segments.length"
      class="segment-table"
    >
      <header class="segment-header">
        <span>Status</span>
        <span>Type</span>
        <span>Length</span>
        <span>Path Index</span>
      </header>
      <div
        v-for="segment in diff.segments"
        :key="segment.id"
        class="segment-row"
      >
        <span :class="segment.status">{{ segment.status }}</span>
        <span>{{ segment.type }}</span>
        <span>{{ segment.length.toFixed(2) }} mm</span>
        <span>#{{ segment.path_index }}</span>
      </div>
    </div>

    <p
      v-else
      class="hint"
    >
      Select a baseline to see the detailed diff.
    </p>
  </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { CanonicalGeometry } from '@/utils/geometry'

interface DiffSummary {
  segments_baseline: number
  segments_current: number
  added: number
  removed: number
  unchanged: number
  overlap_ratio: number
}

interface DiffSegment {
  id: string
  type: string
  status: 'added' | 'removed' | 'match'
  length: number
  path_index: number
}

interface DiffResult {
  baseline_id: string
  baseline_name: string
  summary: DiffSummary
  segments: DiffSegment[]
}

const props = defineProps<{
  diff: DiffResult | null
  currentGeometry: CanonicalGeometry | null
}>()

const exporting = ref(false)
const API_EXPORT = '/api/compare/lab/export'

const canExport = computed(() => Boolean(props.diff && props.currentGeometry))

async function exportOverlay(): Promise<void> {
  if (!props.diff || !props.currentGeometry) {
    return
  }
  exporting.value = true
  try {
    const res = await fetch(API_EXPORT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        baseline_id: props.diff.baseline_id,
        current_geometry: props.currentGeometry,
        format: 'json',
      }),
    })
    if (!res.ok) {
      throw new Error('Export failed')
    }
    const payload = await res.json()
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${props.diff.baseline_name || 'baseline'}-diff.json`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Export overlay error', error)
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.diff-viewer {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-left: 1px solid #252525;
  padding-left: 1rem;
}

.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
}

.summary-card {
  background: #111;
  border: 1px solid #2a2a2a;
  padding: 0.75rem;
  border-radius: 8px;
}

.summary-card .label {
  display: block;
  font-size: 0.8rem;
  color: #8a8a8a;
}

.summary-card strong {
  font-size: 1.2rem;
}

.summary-card .added {
  color: #22c55e;
}

.summary-card .removed {
  color: #ef4444;
}

.segment-table {
  border: 1px solid #333;
  border-radius: 8px;
  overflow: hidden;
}

.segment-header,
.segment-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 0.35rem 0.5rem;
}

.segment-header {
  background: #111;
  font-size: 0.85rem;
  color: #aaa;
}

.segment-row:nth-child(even) {
  background: #171717;
}

.segment-row span {
  font-size: 0.85rem;
}

.segment-row span.added {
  color: #22c55e;
}

.segment-row span.removed {
  color: #ef4444;
}

.segment-row span.match {
  color: #9ca3af;
}

.ghost {
  background: transparent;
  border: 1px solid #444;
  color: #ddd;
  padding: 0.35rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
}

.ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hint {
  color: #9ca3af;
  margin: 0;
}
</style>
