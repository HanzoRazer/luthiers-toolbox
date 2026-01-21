<template>
  <div class="live-monitor">
    <div class="monitor-header">
      <h2>🔴 Real-time Monitoring</h2>
      <div class="connection-status">
        <span
          v-if="isConnected"
          class="status-badge connected"
        >● Connected</span>
        <span
          v-else
          class="status-badge disconnected"
        >○ Disconnected</span>
        <span
          v-if="reconnectAttempts > 0"
          class="reconnect-info"
        >
          (Retry {{ reconnectAttempts }}/5)
        </span>
      </div>
      <div class="controls">
        <button
          class="btn-primary"
          @click="toggleConnection"
        >
          {{ isConnected ? 'Disconnect' : 'Connect' }}
        </button>
        <button
          class="btn-secondary"
          @click="clearEvents"
        >
          Clear
        </button>
      </div>
    </div>

    <div class="filter-panel">
      <label>
        <input
          v-model="filters.job"
          type="checkbox"
          @change="updateFilters"
        >
        Jobs
      </label>
      <label>
        <input
          v-model="filters.pattern"
          type="checkbox"
          @change="updateFilters"
        >
        Patterns
      </label>
      <label>
        <input
          v-model="filters.material"
          type="checkbox"
          @change="updateFilters"
        >
        Materials
      </label>
      <label>
        <input
          v-model="filters.metrics"
          type="checkbox"
          @change="updateFilters"
        >
        Metrics
      </label>
    </div>

    <div
      ref="eventContainer"
      class="event-stream"
    >
      <div
        v-if="events.length === 0"
        class="no-events"
      >
        No events yet. Connect to start monitoring.
      </div>
      <div
        v-for="(event, index) in events"
        :key="index"
        class="event-item"
        :class="getEventClass(event.type)"
      >
        <div class="event-header">
          <span class="event-type">{{ event.type }}</span>
          <span class="event-time">{{ formatTime(event.timestamp) }}</span>
          <!-- N10.1: Drill-down button for job events -->
          <button 
            v-if="event.type.startsWith('job:') && event.data.job_id"
            class="drilldown-btn"
            title="View subjobs and CAM events"
            @click="openDrilldown(event.data.job_id)"
          >
            🔍 Drill-down
          </button>
        </div>
        
        <!-- MM-6: Fragility and Materials Display -->
        <div
          v-if="event.data.fragility_band || event.data.materials"
          class="event-metadata"
        >
          <span
            v-if="event.data.fragility_band" 
            class="fragility-badge"
            :class="fragilityBadgeClass(event.data.fragility_band)"
            :title="fragilityTitle(event.data.fragility_band, event.data.worst_fragility_score)"
          >
            {{ fragilityLabel(event.data.fragility_band) }}
            <span
              v-if="event.data.worst_fragility_score !== undefined"
              class="fragility-score"
            >
              {{ (event.data.worst_fragility_score * 100).toFixed(0) }}%
            </span>
          </span>
          <span
            v-if="event.data.materials && event.data.materials.length > 0"
            class="materials-list"
          >
            🪵 {{ event.data.materials.join(', ') }}
          </span>
          <span
            v-if="event.data.lane_hint"
            class="lane-hint"
          >
            Lane: {{ event.data.lane_hint }}
          </span>
        </div>
        
        <div class="event-data">
          <pre>{{ JSON.stringify(event.data, null, 2) }}</pre>
        </div>
      </div>
    </div>

    <div class="stats-footer">
      <span>Total Events: {{ events.length }}</span>
      <span>Jobs: {{ eventCounts.job }}</span>
      <span>Patterns: {{ eventCounts.pattern }}</span>
      <span>Materials: {{ eventCounts.material }}</span>
      <span>Metrics: {{ eventCounts.metrics }}</span>
    </div>

    <!-- N10.1: Drill-down drawer -->
    <LiveMonitorDrilldownDrawer
      :visible="showDrilldown"
      :drill="store.activeDrilldown"
      :loading="store.drilldownLoading"
      :error="store.drilldownError"
      @close="closeDrilldown"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'
import type { LiveMonitorEvent } from '@/models/live_monitor'
import { fragilityBadgeClass, fragilityLabel, fragilityTitle } from '@/models/live_monitor'
import { useLiveMonitorStore } from '@/stores/useLiveMonitorStore'
import LiveMonitorDrilldownDrawer from './LiveMonitorDrilldownDrawer.vue'

const { connect, disconnect, isConnected, subscribe, reconnectAttempts } = useWebSocket()
const store = useLiveMonitorStore()

const events = ref<LiveMonitorEvent[]>([])
const eventContainer = ref<HTMLElement | null>(null)
const showDrilldown = ref(false)
const filters = reactive({
  job: true,
  pattern: true,
  material: true,
  metrics: true
})

const eventCounts = reactive({
  job: 0,
  pattern: 0,
  material: 0,
  metrics: 0
})

let unsubscribe: (() => void) | null = null

const toggleConnection = async () => {
  if (isConnected.value) {
    disconnect()
    if (unsubscribe) {
      unsubscribe()
      unsubscribe = null
    }
  } else {
    await connect()
    updateFilters()
  }
}

const updateFilters = () => {
  if (!isConnected.value) return

  const activeFilters = Object.entries(filters)
    .filter(([_, enabled]) => enabled)
    .map(([name, _]) => name)

  if (activeFilters.length === 0) {
    activeFilters.push('all') // Subscribe to all if none selected
  }

  // Unsubscribe previous handler
  if (unsubscribe) {
    unsubscribe()
  }

  // Subscribe with new filters
  unsubscribe = subscribe(activeFilters, (event) => {
    events.value.push(event)

    // Update counts
    const [category] = event.type.split(':')
    if (category in eventCounts) {
      eventCounts[category as keyof typeof eventCounts]++
    }

    // Auto-scroll to bottom
    nextTick(() => {
      if (eventContainer.value) {
        eventContainer.value.scrollTop = eventContainer.value.scrollHeight
      }
    })
  })
}

const clearEvents = () => {
  events.value = []
  eventCounts.job = 0
  eventCounts.pattern = 0
  eventCounts.material = 0
  eventCounts.metrics = 0
}

const getEventClass = (type: string): string => {
  if (type.startsWith('job:')) return 'event-job'
  if (type.startsWith('pattern:')) return 'event-pattern'
  if (type.startsWith('material:')) return 'event-material'
  if (type.startsWith('metrics:')) return 'event-metrics'
  return 'event-default'
}

const formatTime = (timestamp: string): string => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

// N10.1: Drill-down functions
const openDrilldown = async (jobId: string) => {
  await store.loadDrilldown(jobId)
  showDrilldown.value = true
}

const closeDrilldown = () => {
  showDrilldown.value = false
  store.closeDrilldown()
}
</script>

<style scoped>
.live-monitor {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1rem;
  gap: 1rem;
}

.monitor-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.monitor-header h2 {
  margin: 0;
  flex: 1;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.status-badge.connected {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.disconnected {
  background: #fee2e2;
  color: #991b1b;
}

.reconnect-info {
  color: #6b7280;
  font-size: 0.75rem;
}

.controls {
  display: flex;
  gap: 0.5rem;
}

.btn-primary {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  color: #374151;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 600;
}

.btn-secondary:hover {
  background: #d1d5db;
}

.filter-panel {
  display: flex;
  gap: 1rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 0.375rem;
}

.filter-panel label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.event-stream {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  padding: 1rem;
  background: white;
}

.no-events {
  color: #9ca3af;
  text-align: center;
  padding: 3rem;
  font-style: italic;
}

.event-item {
  margin-bottom: 1rem;
  padding: 0.75rem;
  border-left: 4px solid #d1d5db;
  background: #f9fafb;
  border-radius: 0.25rem;
}

.event-item.event-job {
  border-left-color: #3b82f6;
}

.event-item.event-pattern {
  border-left-color: #8b5cf6;
}

.event-item.event-material {
  border-left-color: #f59e0b;
}

.event-item.event-metrics {
  border-left-color: #10b981;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.event-type {
  font-weight: 600;
  color: #374151;
}

.event-time {
  color: #6b7280;
  font-size: 0.875rem;
}

/* N10.1: Drill-down button */
.drilldown-btn {
  padding: 0.25rem 0.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.drilldown-btn:hover {
  background: #2563eb;
}

.event-data pre {
  margin: 0;
  font-size: 0.875rem;
  color: #1f2937;
  overflow-x: auto;
  max-width: 100%;
}

.stats-footer {
  display: flex;
  gap: 2rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.stats-footer span {
  font-weight: 600;
}

/* MM-6: Fragility Badge Styles */
.event-metadata {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.fragility-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.fragility-stable {
  background: #d1fae5;
  color: #065f46;
}

.fragility-medium {
  background: #fef3c7;
  color: #92400e;
}

.fragility-fragile {
  background: #fee2e2;
  color: #991b1b;
}

.fragility-unknown {
  background: #e5e7eb;
  color: #6b7280;
}

.fragility-score {
  font-weight: 900;
  margin-left: 0.125rem;
}

.materials-list {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: #f3f4f6;
  color: #374151;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.lane-hint {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}
</style>
