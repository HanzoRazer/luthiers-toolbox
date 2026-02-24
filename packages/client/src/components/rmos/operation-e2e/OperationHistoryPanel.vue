<script setup lang="ts">
/**
 * OperationHistoryPanel - Operation history list display
 * Extracted from RmosOperationE2EPanel.vue
 */
interface HistoryEntry {
  action: string
  runId: string
  status?: string
  timestamp: string
}

defineProps<{
  history: HistoryEntry[]
}>()

function statusClass(status: string): string {
  if (status === 'EXECUTED' || status === 'OK') return 'status-green'
  if (status === 'PLANNED') return 'status-blue'
  if (status === 'BLOCKED') return 'status-red'
  return 'status-yellow'
}
</script>

<template>
  <div class="card">
    <div class="title">
      History
    </div>
    <div class="history-list">
      <div
        v-for="(h, i) in history"
        :key="i"
        class="history-item"
      >
        <div class="history-header">
          <strong>{{ h.action }}</strong>
          <span class="timestamp">{{ h.timestamp }}</span>
        </div>
        <div class="history-meta">
          <code>{{ h.runId }}</code>
          <span
            v-if="h.status"
            class="badge"
            :class="statusClass(h.status)"
          >{{ h.status }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 1rem;
  margin-top: 1rem;
}

.title {
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 0.75rem;
  color: #333;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.history-item {
  padding: 0.5rem;
  background: white;
  border: 1px solid #eee;
  border-radius: 4px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.timestamp {
  font-size: 0.75rem;
  color: #888;
  font-family: monospace;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.history-meta code {
  font-size: 0.75rem;
  background: #f0f0f0;
  padding: 0.1rem 0.3rem;
  border-radius: 2px;
}

.badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-green {
  background: #d1fae5;
  color: #065f46;
}

.status-blue {
  background: #dbeafe;
  color: #1e40af;
}

.status-red {
  background: #fee2e2;
  color: #991b1b;
}

.status-yellow {
  background: #fef3c7;
  color: #92400e;
}
</style>
