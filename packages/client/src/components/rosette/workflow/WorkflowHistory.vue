<template>
  <div v-if="history.length" class="wf-history">
    <div class="wf-history-title">History ({{ history.length }})</div>
    <div
      v-for="(evt, idx) in displayedHistory"
      :key="idx"
      class="wf-event"
    >
      <span class="wf-event-action">{{ evt.action }}</span>
      <span class="wf-event-transition">
        {{ evt.from_state }} → {{ evt.to_state }}
      </span>
      <span v-if="evt.note" class="wf-event-note">{{ evt.note }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface WorkflowEvent {
  action: string
  from_state: string
  to_state: string
  note?: string | null
}

const props = defineProps<{
  history: WorkflowEvent[]
  maxItems?: number
}>()

const displayedHistory = computed(() => {
  const max = props.maxItems ?? 5
  return props.history.slice().reverse().slice(0, max)
})
</script>

<style scoped>
.wf-history {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.wf-history-title {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.7;
  margin-bottom: 6px;
}

.wf-event {
  font-size: 11px;
  padding: 4px 0;
  display: flex;
  gap: 8px;
  align-items: center;
}

.wf-event-action {
  font-weight: 600;
}

.wf-event-transition {
  opacity: 0.7;
}

.wf-event-note {
  font-style: italic;
  opacity: 0.6;
}
</style>
