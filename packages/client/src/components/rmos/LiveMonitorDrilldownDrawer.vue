<template>
  <div
    v-if="visible"
    class="drilldown-drawer"
  >
    <header class="drawer-header">
      <h3 class="drawer-title">
        Job Drill-Down – {{ drill?.job_id }}
      </h3>
      <button
        class="close-btn"
        aria-label="Close"
        @click="$emit('close')"
      >
        ✕
      </button>
    </header>

    <div
      v-if="loading"
      class="drawer-loading"
    >
      <div class="spinner" />
      Loading drill-down data...
    </div>
    
    <div
      v-if="error"
      class="drawer-error"
    >
      ⚠️ {{ error }}
    </div>

    <div
      v-if="drill && !loading"
      class="drawer-content"
    >
      <div
        v-for="(sj, idx) in drill.subjobs"
        :key="idx"
        class="subjob-card"
      >
        <div class="subjob-header">
          <div class="subjob-title">
            <span class="subjob-icon">{{ getSubjobIcon(sj.subjob_type) }}</span>
            <span class="subjob-type">{{ subjobLabel(sj.subjob_type) }}</span>
          </div>
          <div class="subjob-timeline">
            {{ formatTimestamp(sj.started_at) }} → {{ sj.ended_at ? formatTimestamp(sj.ended_at) : '—' }}
          </div>
        </div>

        <div
          v-if="sj.cam_events.length > 0"
          class="cam-events-table"
        >
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Feed</th>
                <th>RPM</th>
                <th>DOC</th>
                <th>State</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(e, eidx) in sj.cam_events"
                :key="eidx"
                :class="getRowClass(e.heuristic)"
              >
                <td>{{ formatTimestamp(e.timestamp) }}</td>
                <td>{{ e.feedrate.toFixed(0) }}</td>
                <td>{{ e.spindle_speed.toFixed(0) }}</td>
                <td>{{ e.doc.toFixed(2) }}</td>
                <td>
                  <span
                    class="feed-state-badge"
                    :class="feedStateClass(e.feed_state)"
                  >
                    {{ e.feed_state }}
                  </span>
                </td>
                <td>
                  <span
                    class="heuristic-badge"
                    :class="heuristicClass(e.heuristic)"
                  >
                    {{ e.heuristic }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div
          v-else
          class="no-events"
        >
          No CAM events recorded for this subjob.
        </div>
      </div>

      <div
        v-if="drill.subjobs.length === 0"
        class="no-subjobs"
      >
        No subjobs found for this job.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DrilldownResponse } from '@/models/live_monitor_drilldown'
import { 
  subjobLabel, 
  formatTimestamp, 
  feedStateClass, 
  heuristicClass,
  type SubjobType,
  type HeuristicLevel,
  type FeedState
} from '@/models/live_monitor_drilldown'

const props = defineProps<{
  visible: boolean
  drill: DrilldownResponse | null
  loading: boolean
  error: string | null
}>()

defineEmits<{
  close: []
}>()

function getSubjobIcon(type: SubjobType): string {
  const icons: Record<SubjobType, string> = {
    roughing: '⚡',
    profiling: '✂️',
    finishing: '✨',
    cleanup: '🧹',
    infeed: '➡️',
    outfeed: '⬅️'
  }
  return icons[type] || '📋'
}

function getRowClass(heuristic: HeuristicLevel): string {
  return `row-${heuristic}`
}
</script>

<style scoped>
.drilldown-drawer {
  position: fixed;
  right: 0;
  top: 0;
  height: 100%;
  width: 100%;
  max-width: 600px;
  background: white;
  border-left: 1px solid #e5e7eb;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.15);
  z-index: 40;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.drawer-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  transition: background 0.2s;
}

.close-btn:hover {
  background: #e5e7eb;
}

.drawer-loading,
.drawer-error {
  padding: 2rem;
  text-align: center;
  font-size: 0.875rem;
}

.drawer-loading {
  color: #6b7280;
}

.spinner {
  display: inline-block;
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.drawer-error {
  color: #dc2626;
}

.drawer-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.subjob-card {
  margin-bottom: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
  background: #f9fafb;
}

.subjob-header {
  padding: 0.75rem 1rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.subjob-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.subjob-icon {
  font-size: 1rem;
}

.subjob-timeline {
  font-size: 0.75rem;
  color: #6b7280;
}

.cam-events-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.75rem;
}

thead {
  background: #f3f4f6;
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: #4b5563;
  border-bottom: 1px solid #e5e7eb;
}

td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #f3f4f6;
}

tr:last-child td {
  border-bottom: none;
}

tr.row-danger {
  background: #fef2f2;
}

tr.row-warning {
  background: #fefce8;
}

.feed-state-badge,
.heuristic-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

/* Feed state colors */
.feed-stable {
  background: #d1fae5;
  color: #065f46;
}

.feed-increasing {
  background: #dbeafe;
  color: #1e40af;
}

.feed-decreasing {
  background: #e0e7ff;
  color: #4338ca;
}

.feed-danger-low,
.feed-danger-high {
  background: #fee2e2;
  color: #991b1b;
}

/* Heuristic colors */
.heuristic-info {
  background: #dbeafe;
  color: #1e40af;
}

.heuristic-warning {
  background: #fef3c7;
  color: #92400e;
}

.heuristic-danger {
  background: #fee2e2;
  color: #991b1b;
}

.no-events,
.no-subjobs {
  padding: 2rem;
  text-align: center;
  color: #9ca3af;
  font-size: 0.875rem;
  font-style: italic;
}
</style>
